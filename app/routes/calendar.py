"""Calendar routes: view calendar, make/cancel reservations."""

from datetime import date, datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for, current_app,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from app import db
from app.models import Season, Reservation, DraftOrder, PhaseState
from app.forms import ReservationForm
from app.phase_engine import PhaseEngine

calendar_bp = Blueprint('calendar', __name__)


@calendar_bp.route('/')
@login_required
def view():
    """Main calendar view showing the season's reservations."""
    season = PhaseEngine.get_active_season()

    if season:
        PhaseEngine.check_and_advance_deadlines(season)

    reservations = []
    can_reserve = False
    reserve_reason = ''
    draft_order = []

    is_my_turn = False
    upcoming_reservations = []
    if season:
        reservations = PhaseEngine.get_reserved_dates(season)
        upcoming_reservations = PhaseEngine.get_reserved_dates(season, exclude_past=True)
        can_reserve, reserve_reason = PhaseEngine.can_member_reserve(current_user, season)

        # Get draft order for display
        if season.phase in (PhaseState.PHASE1_DRAFT, PhaseState.PHASE3_REVERSE,
                            PhaseState.PHASE1_OPTIN):
            draft_order = (DraftOrder.query
                           .filter_by(season_id=season.id)
                           .order_by(DraftOrder.position)
                           .all())

        # Check if it's this member's turn (for cancel button visibility)
        current_pick = season.current_pick
        if (current_pick and current_pick.member_id == current_user.id
                and season.phase in (PhaseState.PHASE1_DRAFT, PhaseState.PHASE3_REVERSE)):
            is_my_turn = True

    calendar_config = PhaseEngine.get_calendar_config(season) if season else {}

    # Default start date: first day of lottery period for the active season
    lottery_start = None
    if season:
        lottery_start = date(
            season.year,
            current_app.config['LOTTERY_START_MONTH'],
            current_app.config['LOTTERY_START_DAY']
        ).isoformat()

    return render_template('calendar/view.html',
                           season=season,
                           reservations=reservations,
                           upcoming_reservations=upcoming_reservations,
                           can_reserve=can_reserve,
                           reserve_reason=reserve_reason,
                           draft_order=draft_order,
                           is_my_turn=is_my_turn,
                           calendar_config=calendar_config,
                           lottery_start=lottery_start)


@calendar_bp.route('/reserve', methods=['GET', 'POST'])
@login_required
def reserve():
    """Make a reservation."""
    season = PhaseEngine.get_active_season()
    if not season:
        flash('No active season.', 'warning')
        return redirect(url_for('calendar.view'))

    PhaseEngine.check_and_advance_deadlines(season)

    can_reserve, reason = PhaseEngine.can_member_reserve(current_user, season)
    if not can_reserve:
        flash(reason, 'warning')
        return redirect(url_for('calendar.view'))

    form = ReservationForm()

    if form.validate_on_submit():
        start = form.start_date.data
        end = form.end_date.data

        valid, error = PhaseEngine.validate_reservation(
            season, current_user, start, end)

        if not valid:
            flash(error, 'danger')
        else:
            reservation = PhaseEngine.make_reservation(
                season, current_user, start, end, notes=form.notes.data)
            # During draft phases, remind member to lock in (only for lottery dates)
            if reservation.phase_made in (PhaseState.PHASE1_DRAFT, PhaseState.PHASE3_REVERSE):
                flash(f'Reserved {start} to {end} ({reservation.num_days} day(s)). '
                      f'Go to your dashboard to lock in or change your pick.', 'info')
            else:
                flash(f'Reserved {start} to {end} - {reservation.num_days} day(s).', 'success')
            return redirect(url_for('main.dashboard'))

    # Pre-populate with query params from calendar click
    if request.args.get('start'):
        try:
            form.start_date.data = date.fromisoformat(request.args['start'])
        except ValueError:
            pass
    if request.args.get('end'):
        try:
            form.end_date.data = date.fromisoformat(request.args['end'])
        except ValueError:
            pass

    existing_reservations = PhaseEngine.get_reserved_dates(season) if season else []
    upcoming_reservations = PhaseEngine.get_reserved_dates(season, exclude_past=True) if season else []

    calendar_config = PhaseEngine.get_calendar_config(season) if season else {}

    # Default start date: first day of lottery period for the active season
    lottery_start = None
    if season:
        lottery_start = date(
            season.year,
            current_app.config['LOTTERY_START_MONTH'],
            current_app.config['LOTTERY_START_DAY']
        ).isoformat()

    return render_template('calendar/reserve.html',
                           form=form, season=season,
                           reservations=existing_reservations,
                           upcoming_reservations=upcoming_reservations,
                           calendar_config=calendar_config,
                           lottery_start=lottery_start)


@calendar_bp.route('/lock-in', methods=['POST'])
@login_required
def lock_in():
    """Lock in the current picker's draft reservation and advance the draft."""
    season = PhaseEngine.get_active_season()
    if not season:
        flash('No active season.', 'warning')
        return redirect(url_for('calendar.view'))

    success, message = PhaseEngine.lock_in_pick(season, current_user)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'warning')
    return redirect(url_for('main.dashboard'))


@calendar_bp.route('/cancel/<int:reservation_id>', methods=['POST'])
@login_required
def cancel(reservation_id):
    """Cancel a reservation. Members can always cancel their own."""
    reservation = Reservation.query.get_or_404(reservation_id)

    # Only the owner or admin can cancel
    if reservation.member_id != current_user.id and not current_user.is_admin:
        flash('You can only cancel your own reservations.', 'danger')
        return redirect(url_for('calendar.view'))

    season = PhaseEngine.get_active_season()
    was_phase2 = reservation.phase_made == PhaseState.PHASE2_FCFS

    PhaseEngine.cancel_reservation(reservation)

    # Phase-aware feedback
    if was_phase2 and season and season.phase == PhaseState.PHASE2_FCFS:
        flash('Reservation cancelled. You may pick new dates while Phase 2 is still open.', 'info')
    else:
        flash('Reservation cancelled.', 'info')

    return redirect(url_for('main.dashboard'))


@calendar_bp.route('/api/reservations')
@login_required
def api_reservations():
    """JSON endpoint for calendar JavaScript to fetch reservations."""
    season = PhaseEngine.get_active_season()
    if not season:
        return jsonify([])

    return jsonify(PhaseEngine.get_reserved_dates(season))


@calendar_bp.route('/opt-in', methods=['POST'])
@login_required
def opt_in():
    """Member opts in to the Phase 1 draw."""
    season = PhaseEngine.get_active_season()
    if not season or season.phase != PhaseState.PHASE1_OPTIN:
        flash('Opt-in is not currently open.', 'warning')
        return redirect(url_for('main.dashboard'))

    if not current_user.can_enter_draft:
        flash('Your account is not eligible for the draw.', 'info')
        return redirect(url_for('main.dashboard'))

    existing = DraftOrder.query.filter_by(
        season_id=season.id, member_id=current_user.id).first()
    if existing:
        flash('You are already opted in.', 'info')
    else:
        # Temp position - reassigned when the draw runs
        max_pos = (db.session.query(db.func.max(DraftOrder.position))
                   .filter_by(season_id=season.id).scalar() or 0)
        entry = DraftOrder(season_id=season.id, member_id=current_user.id,
                           position=max_pos + 1)
        db.session.add(entry)
        db.session.commit()
        flash('You have opted in for the draw!', 'success')

    return redirect(url_for('main.dashboard'))


@calendar_bp.route('/api/available-dates')
@login_required
def api_available_dates():
    """JSON endpoint returning date availability for the season calendar."""
    season = PhaseEngine.get_active_season()
    if not season:
        return jsonify({'season_start': None, 'season_end': None,
                        'reserved_dates': [], 'calendar_config': {}})

    reservations = Reservation.query.filter_by(
        season_id=season.id, is_cancelled=False).all()

    # Build set of reserved dates
    reserved = set()
    for r in reservations:
        d = r.start_date
        while d <= r.end_date:
            reserved.add(d.isoformat())
            d += timedelta(days=1)

    return jsonify({
        'season_start': season.season_start.isoformat(),
        'season_end': season.season_end.isoformat(),
        'reserved_dates': sorted(reserved),
        'calendar_config': PhaseEngine.get_calendar_config(season),
        'phase': season.phase,
    })
