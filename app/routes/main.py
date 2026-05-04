"""Main routes: dashboard, member profile."""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Season, Reservation, DraftOrder, PhaseState
from app.phase_engine import PhaseEngine

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    season = PhaseEngine.get_active_season()

    # Check deadlines on every page load (replaces background worker)
    if season:
        PhaseEngine.check_and_advance_deadlines(season)

    # Get member's reservations
    my_reservations = []
    draft_position = None
    can_reserve = False
    reserve_reason = ''
    current_pick = None
    draft_reservation = None
    is_my_turn = False

    if season:
        my_reservations = (Reservation.query
                           .filter_by(season_id=season.id, member_id=current_user.id,
                                      is_cancelled=False)
                           .order_by(Reservation.start_date)
                           .all())

        draft_entry = DraftOrder.query.filter_by(
            season_id=season.id, member_id=current_user.id).first()
        if draft_entry:
            draft_position = draft_entry.position

        can_reserve, reserve_reason = PhaseEngine.can_member_reserve(current_user, season)
        current_pick = season.current_pick

        # Check if it's this member's turn and they have a tentative draft reservation
        if (current_pick and current_pick.member_id == current_user.id
                and season.phase in (PhaseState.PHASE1_DRAFT, PhaseState.PHASE3_REVERSE)):
            is_my_turn = True
            draft_reservation = PhaseEngine.get_current_draft_reservation(season, current_user)

    return render_template('dashboard.html',
                           season=season,
                           my_reservations=my_reservations,
                           draft_position=draft_position,
                           can_reserve=can_reserve,
                           reserve_reason=reserve_reason,
                           current_pick=current_pick,
                           draft_reservation=draft_reservation,
                           is_my_turn=is_my_turn)
