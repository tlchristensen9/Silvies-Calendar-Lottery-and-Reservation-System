"""Automated email notifications for phase transitions.

All functions check the 'emails_enabled' AppSetting before sending.
If emails are disabled (or the setting doesn't exist), they silently no-op.
"""

from flask import current_app
from flask_mail import Message
from app import db, mail
from app.models import AppSetting, Member, DraftOrder, MemberRole


def _emails_enabled():
    """Check whether the admin has enabled automated emails."""
    return AppSetting.get('emails_enabled', 'off') == 'on'


def _send(msg):
    """Send an email, logging failures without crashing the app."""
    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f'Failed to send email: {e}')


def _site_url():
    """Return the base URL for links in emails."""
    return current_app.config.get('SITE_URL', 'https://silviesclubreservations.pythonanywhere.com')


def notify_optin_open(season):
    """Email all active members: lottery opt-in is now open."""
    if not _emails_enabled():
        return
    members = Member.query.filter_by(is_active_member=True).filter(
        Member.role != MemberRole.LIFETIME
    ).all()
    url = f"{_site_url()}/calendar/"
    for member in members:
        if not member.email:
            continue
        msg = Message(
            subject=f'Silvies Club — {season.year} Lottery Opt-In Is Open',
            recipients=[member.email],
            body=(
                f"Hi {member.name},\n\n"
                f"The {season.year} lottery opt-in period is now open!\n\n"
                f"Log in to the reservation system to opt in to the lottery draw:\n"
                f"{url}\n\n"
                f"Once opt-in closes, the admin will run the draw and the draft "
                f"will begin.\n\n"
                f"— Silvies Club Reservations"
            )
        )
        _send(msg)


def notify_your_turn(draft_order, season, phase_num):
    """Email a member: it's your turn to pick.

    Args:
        draft_order: the DraftOrder entry for the member whose turn it is
        season: the active Season
        phase_num: 1 or 3 (which phase)
    """
    if not _emails_enabled():
        return
    member = draft_order.member
    if not member or not member.email:
        return
    if phase_num == 1:
        deadline = draft_order.phase1_pick_deadline
    else:
        deadline = draft_order.phase3_pick_deadline

    deadline_str = deadline.strftime('%b %d, %Y at %I:%M %p') if deadline else 'TBD'
    url = f"{_site_url()}/calendar/"

    msg = Message(
        subject=f'Silvies Club — It\'s Your Turn to Pick (Phase {phase_num})',
        recipients=[member.email],
        body=(
            f"Hi {member.name},\n\n"
            f"It's your turn to pick your dates in the {season.year} "
            f"Phase {phase_num} draft!\n\n"
            f"Your deadline to make your selection: {deadline_str}\n\n"
            f"Log in now to choose your dates and lock in your pick:\n"
            f"{url}\n\n"
            f"If you don't pick by the deadline, your turn will be "
            f"automatically skipped.\n\n"
            f"— Silvies Club Reservations"
        )
    )
    _send(msg)


def notify_phase2_open(season):
    """Email members who did NOT enter the draw: Phase 2 FCFS is open."""
    if not _emails_enabled():
        return
    # Find members who are NOT in the draft order for this season
    draft_member_ids = [
        d.member_id for d in
        DraftOrder.query.filter_by(season_id=season.id).all()
    ]
    members = Member.query.filter_by(is_active_member=True).filter(
        Member.id.notin_(draft_member_ids) if draft_member_ids else True,
        Member.role != MemberRole.LIFETIME
    ).all()
    url = f"{_site_url()}/calendar/"
    for member in members:
        if not member.email:
            continue
        msg = Message(
            subject=f'Silvies Club — {season.year} Calendar Open for Reservations',
            recipients=[member.email],
            body=(
                f"Hi {member.name},\n\n"
                f"The {season.year} calendar is now open for Phase 2 reservations "
                f"(first come, first served).\n\n"
                f"Since you did not enter the lottery, you can now reserve your "
                f"dates in the lottery period.\n\n"
                f"Log in to make your reservation:\n"
                f"{url}\n\n"
                f"— Silvies Club Reservations"
            )
        )
        _send(msg)
