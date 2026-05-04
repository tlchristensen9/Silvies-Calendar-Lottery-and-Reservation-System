"""Admin (Spike) routes: member management, phase control, draft draw."""

from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort, current_app)
from flask_login import login_required, current_user
from app import db
from app.models import (Member, Season, DraftOrder, Reservation,
                        PhaseState, MemberRole, AppSetting)
from app.forms import MemberForm, SeasonForm
from app.phase_engine import PhaseEngine
from app.utils import get_now, get_today

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator: require admin (Spike) role."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/')
@admin_required
def dashboard():
    season = PhaseEngine.get_active_season()
    if season:
        PhaseEngine.check_and_advance_deadlines(season)

    members = Member.query.order_by(Member.name).all()
    seasons = Season.query.order_by(Season.year.desc()).all()

    draft_order = []
    opt_in_count = 0
    if season:
        draft_order = (DraftOrder.query
                       .filter_by(season_id=season.id)
                       .order_by(DraftOrder.position)
                       .all())
        opt_in_count = DraftOrder.query.filter_by(season_id=season.id).count()

    time_override_active = bool(AppSetting.get('time_override')) if current_app.config.get('DEBUG_TIME_TRAVEL') else False

    return render_template('admin/dashboard.html',
                           season=season, members=members, seasons=seasons,
                           draft_order=draft_order, opt_in_count=opt_in_count,
                           time_override_active=time_override_active,
                           app_time=get_now())


# --- Member Management ---

@admin_bp.route('/members')
@admin_required
def members():
    all_members = Member.query.order_by(Member.name).all()
    return render_template('admin/members.html', members=all_members)


@admin_bp.route('/members/add', methods=['GET', 'POST'])
@admin_required
def add_member():
    form = MemberForm()
    if form.validate_on_submit():
        if Member.query.filter_by(email=form.email.data.lower().strip()).first():
            flash('A member with that email already exists.', 'danger')
        else:
            member = Member(
                name=form.name.data.strip(),
                email=form.email.data.lower().strip(),
                phone=form.phone.data.strip() if form.phone.data else None,
                role=form.role.data
            )
            member.set_password(form.password.data or 'changeme')
            db.session.add(member)
            db.session.commit()
            flash(f'Member {member.name} added.', 'success')
            return redirect(url_for('admin.members'))

    return render_template('admin/member_form.html', form=form, editing=False)


@admin_bp.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)
    form = MemberForm(obj=member)

    if form.validate_on_submit():
        existing = Member.query.filter(
            Member.email == form.email.data.lower().strip(),
            Member.id != member.id).first()
        if existing:
            flash('Another member with that email already exists.', 'danger')
        else:
            member.name = form.name.data.strip()
            member.email = form.email.data.lower().strip()
            member.phone = form.phone.data.strip() if form.phone.data else None
            member.role = form.role.data
            if form.password.data:
                member.set_password(form.password.data)
            db.session.commit()
            flash(f'Member {member.name} updated.', 'success')
            return redirect(url_for('admin.members'))

    return render_template('admin/member_form.html', form=form, editing=True, member=member)


@admin_bp.route('/members/<int:member_id>/reset-password', methods=['POST'])
@admin_required
def reset_member_password(member_id):
    member = Member.query.get_or_404(member_id)
    member.set_password('changeme')
    db.session.commit()
    flash(f'Password for {member.name} reset to "changeme".', 'info')
    return redirect(url_for('admin.members'))


@admin_bp.route('/members/<int:member_id>/delete', methods=['POST'])
@admin_required
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    if member.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.members'))
    name = member.name
    # Cancel any active reservations
    Reservation.query.filter_by(member_id=member.id).delete()
    DraftOrder.query.filter_by(member_id=member.id).delete()
    db.session.delete(member)
    db.session.commit()
    flash(f'Member {name} has been deleted.', 'info')
    return redirect(url_for('admin.members'))


# --- Season Management ---

@admin_bp.route('/season/create', methods=['GET', 'POST'])
@admin_required
def create_season():
    form = SeasonForm()
    if form.validate_on_submit():
        if Season.query.filter_by(year=form.year.data).first():
            flash(f'Season {form.year.data} already exists.', 'danger')
        else:
            season = Season(
                year=form.year.data,
                phase1_optin_start=form.phase1_optin_start.data,
                phase1_draft_date=form.phase1_draft_date.data,
                phase2_start=form.phase2_start.data,
                phase3_start=form.phase3_start.data,
            )
            db.session.add(season)
            db.session.commit()
            flash(f'Season {season.year} created.', 'success')
            return redirect(url_for('admin.dashboard'))

    return render_template('admin/season_form.html', form=form)


# --- Phase Transitions ---

@admin_bp.route('/season/<int:season_id>/start-optin', methods=['POST'])
@admin_required
def start_optin(season_id):
    season = Season.query.get_or_404(season_id)
    try:
        PhaseEngine.start_optin(season)
        flash('Phase 1 opt-in period started!', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/season/<int:season_id>/run-draw', methods=['POST'])
@admin_required
def run_draw(season_id):
    season = Season.query.get_or_404(season_id)
    try:
        PhaseEngine.run_draft_draw(season)
        flash('Draft draw complete! Members can now start picking.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/season/<int:season_id>/advance-phase2', methods=['POST'])
@admin_required
def advance_phase2(season_id):
    season = Season.query.get_or_404(season_id)
    try:
        PhaseEngine.advance_to_phase2(season)
        flash('Advanced to Phase 2 — non-draw members can now reserve.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/season/<int:season_id>/advance-phase3', methods=['POST'])
@admin_required
def advance_phase3(season_id):
    season = Season.query.get_or_404(season_id)
    try:
        PhaseEngine.advance_to_phase3(season)
        flash('Advanced to Phase 3 — reverse draft picks begin.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/season/<int:season_id>/advance-open', methods=['POST'])
@admin_required
def advance_open(season_id):
    season = Season.query.get_or_404(season_id)
    try:
        PhaseEngine.advance_to_open(season)
        flash('All remaining dates are now open FCFS.', 'success')
    except ValueError as e:
        flash(str(e), 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/season/<int:season_id>/close', methods=['POST'])
@admin_required
def close_season(season_id):
    season = Season.query.get_or_404(season_id)
    PhaseEngine.close_season(season)
    flash(f'Season {season.year} closed.', 'info')
    return redirect(url_for('admin.dashboard'))


# --- Opt-in Management ---

@admin_bp.route('/season/<int:season_id>/optin/<int:member_id>', methods=['POST'])
@admin_required
def admin_optin_member(season_id, member_id):
    """Spike can opt a member into the draw."""
    season = Season.query.get_or_404(season_id)
    member = Member.query.get_or_404(member_id)

    if season.phase != PhaseState.PHASE1_OPTIN:
        flash('Opt-in is not currently open.', 'warning')
        return redirect(url_for('admin.dashboard'))

    existing = DraftOrder.query.filter_by(
        season_id=season.id, member_id=member.id).first()
    if existing:
        flash(f'{member.name} is already opted in.', 'info')
    else:
        max_pos = db.session.query(db.func.max(DraftOrder.position)).filter_by(season_id=season.id).scalar() or 0
        entry = DraftOrder(season_id=season.id, member_id=member.id, position=max_pos + 1)
        db.session.add(entry)
        db.session.commit()
        flash(f'{member.name} opted into the draw.', 'success')

    return redirect(url_for('admin.dashboard'))


# --- Trade / Cancel ---

@admin_bp.route('/reservation/<int:res_id>/trade', methods=['POST'])
@admin_required
def trade_reservation(res_id):
    """Trade a reservation to another member."""
    reservation = Reservation.query.get_or_404(res_id)
    new_member_id = request.form.get('new_member_id', type=int)
    if not new_member_id:
        flash('Select a member to trade to.', 'danger')
        return redirect(url_for('admin.dashboard'))

    new_member = Member.query.get_or_404(new_member_id)
    PhaseEngine.trade_reservation(reservation, new_member)
    flash(f'Reservation traded to {new_member.name}.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reservation/<int:res_id>/cancel', methods=['POST'])
@admin_required
def admin_cancel_reservation(res_id):
    """Admin cancel any reservation."""
    reservation = Reservation.query.get_or_404(res_id)
    PhaseEngine.cancel_reservation(reservation)
    flash('Reservation cancelled.', 'info')
    return redirect(url_for('admin.dashboard'))


# --- Admin Tools: Time Travel, Deadlines, Reset ---

@admin_bp.route('/tools')
@admin_required
def admin_tools():
    """Admin tools page: time travel, deadline config, season reset."""
    season = PhaseEngine.get_active_season()
    time_travel_enabled = current_app.config.get('DEBUG_TIME_TRAVEL', False)
    current_override = None
    if time_travel_enabled:
        current_override = AppSetting.get('time_override')
    return render_template('admin/tools.html',
                           season=season,
                           time_travel_enabled=time_travel_enabled,
                           current_override=current_override,
                           now=get_now(),
                           today=get_today())


@admin_bp.route('/tools/time-set', methods=['POST'])
@admin_required
def time_set():
    """Set a fake date/time override."""
    if not current_app.config.get('DEBUG_TIME_TRAVEL', False):
        flash('Time travel is disabled.', 'danger')
        return redirect(url_for('admin.admin_tools'))

    date_str = request.form.get('override_date', '')
    time_str = request.form.get('override_time', '12:00')
    if not date_str:
        flash('Please enter a date.', 'danger')
        return redirect(url_for('admin.admin_tools'))

    try:
        dt = datetime.fromisoformat(f'{date_str}T{time_str}:00')
        AppSetting.set('time_override', dt.isoformat())
        flash(f'Time override set to {dt.strftime("%b %d, %Y at %I:%M %p")}.', 'success')
    except ValueError:
        flash('Invalid date/time format.', 'danger')

    return redirect(url_for('admin.admin_tools'))


@admin_bp.route('/tools/time-jump', methods=['POST'])
@admin_required
def time_jump():
    """Jump the fake clock forward by a number of hours."""
    if not current_app.config.get('DEBUG_TIME_TRAVEL', False):
        flash('Time travel is disabled.', 'danger')
        return redirect(url_for('admin.admin_tools'))

    hours = request.form.get('jump_hours', 0, type=int)
    if hours <= 0:
        flash('Enter a positive number of hours.', 'danger')
        return redirect(url_for('admin.admin_tools'))

    current = get_now()
    new_time = current + timedelta(hours=hours)
    AppSetting.set('time_override', new_time.isoformat())
    flash(f'Jumped {hours} hours forward to {new_time.strftime("%b %d, %Y at %I:%M %p")}.', 'success')

    # After jumping, check for expired deadlines
    season = PhaseEngine.get_active_season()
    if season:
        skipped = PhaseEngine.check_and_advance_deadlines(season)
        if skipped:
            flash(f'{skipped} pick deadline(s) expired and were auto-skipped.', 'info')

    return redirect(url_for('admin.admin_tools'))


@admin_bp.route('/tools/time-clear', methods=['POST'])
@admin_required
def time_clear():
    """Clear the time override, return to real time."""
    AppSetting.delete('time_override')
    flash('Time override cleared. Using real system time.', 'info')
    return redirect(url_for('admin.admin_tools'))


@admin_bp.route('/tools/deadlines', methods=['POST'])
@admin_required
def update_deadlines():
    """Update pick deadline durations for the active season."""
    season = PhaseEngine.get_active_season()
    if not season:
        flash('No active season.', 'danger')
        return redirect(url_for('admin.admin_tools'))

    p1_hours = request.form.get('phase1_pick_hours', '', type=str).strip()
    p3_hours = request.form.get('phase3_pick_hours', '', type=str).strip()

    season.phase1_pick_hours = int(p1_hours) if p1_hours else None
    season.phase3_pick_hours = int(p3_hours) if p3_hours else None
    db.session.commit()

    if season.phase1_pick_hours or season.phase3_pick_hours:
        msg = 'Pick deadlines updated: '
        parts = []
        if season.phase1_pick_hours:
            parts.append(f'Phase 1 = {season.phase1_pick_hours}h')
        if season.phase3_pick_hours:
            parts.append(f'Phase 3 = {season.phase3_pick_hours}h')
        flash(msg + ', '.join(parts) + '.', 'success')
    else:
        flash('Pick deadlines reset to config defaults.', 'info')

    return redirect(url_for('admin.admin_tools'))


@admin_bp.route('/season/<int:season_id>/reset', methods=['POST'])
@admin_required
def reset_season(season_id):
    """Reset a season: wipe reservations, draft orders, reset to SETUP.
    Requires typing the 4-digit year as confirmation."""
    season = Season.query.get_or_404(season_id)
    confirm_year = request.form.get('confirm_year', '').strip()

    if confirm_year != str(season.year):
        flash(f'Reset cancelled — you must type "{season.year}" to confirm.', 'danger')
        return redirect(url_for('admin.admin_tools'))

    # Wipe all reservations for this season
    Reservation.query.filter_by(season_id=season.id).delete()
    # Wipe all draft orders for this season
    DraftOrder.query.filter_by(season_id=season.id).delete()
    # Reset phase and all phase dates
    season.phase = PhaseState.SETUP
    season.phase1_optin_start = None
    season.phase1_draft_date = None
    season.phase2_start = None
    season.phase3_start = None
    season.open_fcfs_start = None
    db.session.commit()

    flash(f'Season {season.year} has been fully reset to Setup phase.', 'success')
    return redirect(url_for('admin.admin_tools'))
