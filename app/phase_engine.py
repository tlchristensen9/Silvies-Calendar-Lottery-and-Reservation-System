import random
from datetime import datetime, date, timedelta
from flask import current_app
from app import db
from app.models import (Season, DraftOrder, Reservation, Member, PhaseState, MemberRole)
from app.utils import get_now, get_today


class PhaseEngine:

    @staticmethod
    def get_active_season():
        return Season.query.filter(Season.phase != PhaseState.CLOSED).first()

    @staticmethod
    def check_and_advance_deadlines(season):
        if season.phase not in (PhaseState.PHASE1_DRAFT, PhaseState.PHASE3_REVERSE):
            return 0
        skipped = 0
        now = get_now()
        if season.phase == PhaseState.PHASE1_DRAFT:
            overdue = (DraftOrder.query
                       .filter_by(season_id=season.id, phase1_picked=False)
                       .filter(DraftOrder.phase1_pick_deadline.isnot(None))
                       .filter(DraftOrder.phase1_pick_deadline < now)
                       .all())
            for entry in overdue:
                entry.phase1_picked = True
                skipped += 1
        elif season.phase == PhaseState.PHASE3_REVERSE:
            overdue = (DraftOrder.query
                       .filter_by(season_id=season.id, phase3_picked=False)
                       .filter(DraftOrder.phase3_pick_deadline.isnot(None))
                       .filter(DraftOrder.phase3_pick_deadline < now)
                       .all())
            for entry in overdue:
                entry.phase3_picked = True
                skipped += 1
        if skipped:
            db.session.commit()
            PhaseEngine._maybe_advance_draft_phase(season)
        PhaseEngine._ensure_current_pick_has_deadline(season)
        return skipped

    @staticmethod
    def _maybe_advance_draft_phase(season):
        if season.phase == PhaseState.PHASE1_DRAFT:
            remaining = DraftOrder.query.filter_by(season_id=season.id, phase1_picked=False).count()
            if remaining == 0:
                season.phase = PhaseState.PHASE2_FCFS
                season.phase2_start = get_today()
                db.session.commit()
        elif season.phase == PhaseState.PHASE3_REVERSE:
            remaining = DraftOrder.query.filter_by(season_id=season.id, phase3_picked=False).count()
            if remaining == 0:
                season.phase = PhaseState.OPEN_FCFS
                season.open_fcfs_start = get_today()
                db.session.commit()

    @staticmethod
    def _ensure_current_pick_has_deadline(season):
        current = season.current_pick
        if not current:
            return
        if season.phase == PhaseState.PHASE1_DRAFT and not current.phase1_pick_deadline:
            # Season-level override (hours) takes priority, else config default (days)
            if season.phase1_pick_hours:
                current.phase1_pick_deadline = get_now() + timedelta(hours=season.phase1_pick_hours)
            else:
                days = current_app.config.get('PHASE1_PICK_DAYS', 5)
                current.phase1_pick_deadline = get_now() + timedelta(days=days)
            db.session.commit()
        elif season.phase == PhaseState.PHASE3_REVERSE and not current.phase3_pick_deadline:
            if season.phase3_pick_hours:
                current.phase3_pick_deadline = get_now() + timedelta(hours=season.phase3_pick_hours)
            else:
                days = current_app.config.get('PHASE3_PICK_DAYS', 3)
                current.phase3_pick_deadline = get_now() + timedelta(days=days)
            db.session.commit()

    @staticmethod
    def start_optin(season):
        if season.phase != PhaseState.SETUP:
            raise ValueError(f'Cannot start opt-in from phase: {season.phase}')
        season.phase = PhaseState.PHASE1_OPTIN
        season.phase1_optin_start = get_today()
        db.session.commit()

    @staticmethod
    def run_draft_draw(season):
        if season.phase != PhaseState.PHASE1_OPTIN:
            raise ValueError(f'Cannot run draw from phase: {season.phase}')
        entries = DraftOrder.query.filter_by(season_id=season.id).all()
        if not entries:
            raise ValueError('No members have opted in to the draw.')
        random.shuffle(entries)
        for i, entry in enumerate(entries, start=1):
            db.session.execute(
                db.text('UPDATE draft_orders SET position = :pos WHERE id = :eid'),
                {'pos': i, 'eid': entry.id}
            )
        season.phase = PhaseState.PHASE1_DRAFT
        season.phase1_draft_date = get_today()
        db.session.commit()
        for entry in entries:
            db.session.refresh(entry)
        PhaseEngine._ensure_current_pick_has_deadline(season)

    @staticmethod
    def advance_to_phase2(season):
        if season.phase != PhaseState.PHASE1_DRAFT:
            raise ValueError(f'Cannot advance to Phase 2 from: {season.phase}')
        season.phase = PhaseState.PHASE2_FCFS
        season.phase2_start = get_today()
        db.session.commit()

    @staticmethod
    def advance_to_phase3(season):
        if season.phase != PhaseState.PHASE2_FCFS:
            raise ValueError(f'Cannot advance to Phase 3 from: {season.phase}')
        entries = DraftOrder.query.filter_by(season_id=season.id).all()
        for entry in entries:
            entry.phase3_picked = False
            entry.phase3_pick_deadline = None
        season.phase = PhaseState.PHASE3_REVERSE
        season.phase3_start = get_today()
        db.session.commit()
        PhaseEngine._ensure_current_pick_has_deadline(season)

    @staticmethod
    def advance_to_open(season):
        if season.phase not in (PhaseState.PHASE3_REVERSE, PhaseState.PHASE2_FCFS):
            raise ValueError(f'Cannot advance to open FCFS from: {season.phase}')
        season.phase = PhaseState.OPEN_FCFS
        season.open_fcfs_start = get_today()
        db.session.commit()

    @staticmethod
    def close_season(season):
        season.phase = PhaseState.CLOSED
        db.session.commit()

    @staticmethod
    def _is_lottery_date(d, season):
        """Check if a single date falls within the lottery period."""
        return season.lottery_start <= d <= season.lottery_end

    @staticmethod
    def _is_hunting_date(d, season):
        """Check if a date falls in hunting season (after lottery end through Nov)."""
        hunting_months = current_app.config.get('HUNTING_SEASON_MONTHS', [8, 9, 10, 11])
        return d.month in hunting_months and d > season.lottery_end

    @staticmethod
    def _dates_overlap_lottery(start_date, end_date, season):
        """Check if any date in range falls within the lottery period."""
        return start_date <= season.lottery_end and end_date >= season.lottery_start

    @staticmethod
    def _dates_overlap_hunting(start_date, end_date, season):
        """Check if any date in range falls in hunting season."""
        d = start_date
        while d <= end_date:
            if PhaseEngine._is_hunting_date(d, season):
                return True, d
            d += timedelta(days=1)
        return False, None

    @staticmethod
    def get_date_type(d, season):
        """Return 'lottery', 'open', or 'hunting' for a given date."""
        if PhaseEngine._is_lottery_date(d, season):
            return 'lottery'
        if PhaseEngine._is_hunting_date(d, season):
            return 'hunting'
        return 'open'

    @staticmethod
    def can_member_reserve_open(member, season):
        """Check if a member can book in open dates (always yes for any member)."""
        if not season:
            return False, 'No active season.'
        return True, 'Open booking - reserve anytime.'

    @staticmethod
    def can_member_reserve_lottery(member, season):
        """Check if a member can reserve in lottery dates, phase-dependent."""
        if not season:
            return False, 'No active season.'
        if season.phase == PhaseState.SETUP:
            return False, 'Season has not started yet.'
        if season.phase == PhaseState.PHASE1_OPTIN:
            return False, 'Opt-in period - reservations begin after the draw.'
        if season.phase == PhaseState.PHASE1_DRAFT:
            current = season.current_pick
            if not current or current.member_id != member.id:
                return False, 'It is not your turn to pick.'
            return True, 'Your turn to pick!'
        if season.phase == PhaseState.PHASE2_FCFS:
            in_draw = DraftOrder.query.filter_by(season_id=season.id, member_id=member.id).first()
            if in_draw:
                return False, 'Phase 2 is for members who did not enter the draw.'
            existing = Reservation.query.filter_by(
                season_id=season.id, member_id=member.id,
                phase_made=PhaseState.PHASE2_FCFS, is_cancelled=False).first()
            if existing:
                return False, 'You already reserved in Phase 2.'
            return True, 'First come, first served!'
        if season.phase == PhaseState.PHASE3_REVERSE:
            current = season.current_pick
            if not current or current.member_id != member.id:
                return False, 'It is not your turn to pick.'
            return True, 'Your turn for a second pick!'
        if season.phase == PhaseState.OPEN_FCFS:
            return True, 'Open dates available.'
        return False, 'Lottery dates are not yet available.'

    @staticmethod
    def can_member_reserve(member, season):
        """Combined check - open booking is always allowed, lottery depends on phase."""
        if not season:
            return False, 'No active season.'
        return True, 'You can book open dates anytime. Lottery dates depend on current phase.'

    @staticmethod
    def get_reserved_dates(season):
        reservations = Reservation.query.filter_by(season_id=season.id, is_cancelled=False).all()
        return [{'id': r.id, 'member_id': r.member_id, 'member_name': r.member.name,
                 'start_date': r.start_date.isoformat(), 'end_date': r.end_date.isoformat(),
                 'notes': r.notes, 'phase': r.phase_made} for r in reservations]

    @staticmethod
    def get_calendar_config(season):
        """Return date-based config for the calendar UI."""
        return {
            'lottery_start': season.lottery_start.isoformat(),
            'lottery_end': season.lottery_end.isoformat(),
            'hunting_start': (season.lottery_end + timedelta(days=1)).isoformat(),
            'hunting_end': date(season.year, 11, 30).isoformat(),
            'season_start': season.season_start.isoformat(),
            'season_end': season.season_end.isoformat(),
        }

    @staticmethod
    def _get_fri_thu_block_start(d):
        """Given a date, return the Friday that starts its Fri-Thu block."""
        day_of_week = d.weekday()  # 0=Mon..6=Sun
        if day_of_week == 4:  # Friday
            return d
        elif day_of_week < 4:  # Mon-Thu: go back to previous Friday
            return d - timedelta(days=(day_of_week + 3))
        else:  # Sat-Sun: go back to previous Friday
            return d - timedelta(days=(day_of_week - 4))

    @staticmethod
    def _get_fri_thu_block_end(d):
        """Given a date, return the Thursday that ends its Fri-Thu block."""
        day_of_week = d.weekday()
        if day_of_week == 3:  # Thursday
            return d
        elif day_of_week < 3:  # Mon-Wed
            return d + timedelta(days=(3 - day_of_week))
        else:  # Fri-Sun
            return d + timedelta(days=((3 - day_of_week) % 7))

    @staticmethod
    def validate_reservation(season, member, start_date, end_date):
        if start_date > end_date:
            return False, 'Start date must be before end date.'
        num_days = (end_date - start_date).days + 1
        max_days = current_app.config.get('MAX_RESERVATION_DAYS', 7)
        if num_days > max_days:
            return False, f'Reservation cannot exceed {max_days} days.'
        if start_date < season.season_start or end_date > season.season_end:
            return False, 'Dates must be within the season.'
        # Check that dates don't fall in hunting season
        hunting_hit, hunting_date = PhaseEngine._dates_overlap_hunting(start_date, end_date, season)
        if hunting_hit:
            return False, f'{hunting_date.strftime("%B %d")} is hunting season - no reservations needed.'
        # Check for lottery dates: enforce phase rules
        has_lottery_dates = PhaseEngine._dates_overlap_lottery(start_date, end_date, season)
        if has_lottery_dates:
            can, reason = PhaseEngine.can_member_reserve_lottery(member, season)
            if not can:
                return False, reason
            # Friday-Thursday block rule: Phase 1 and Phase 2 only
            if season.phase in (PhaseState.PHASE1_DRAFT, PhaseState.PHASE2_FCFS):
                block_start = PhaseEngine._get_fri_thu_block_start(start_date)
                if start_date != block_start:
                    return False, (f'Reservation must start on Friday '
                                   f'({block_start.strftime("%B %d")}).')
                block_end = PhaseEngine._get_fri_thu_block_end(start_date)
                if end_date > block_end:
                    return False, (f'Reservation must end by {block_end.strftime("%A, %B %d")} '
                                   f'(the Thursday of this Fri-Thu block).')
        existing = Reservation.query.filter_by(season_id=season.id, is_cancelled=False).all()
        for r in existing:
            if r.start_date <= end_date and r.end_date >= start_date:
                return False, f'Dates overlap with {r.member.name}.'
        return True, None

    @staticmethod
    def make_reservation(season, member, start_date, end_date, notes=None):
        has_lottery_dates = PhaseEngine._dates_overlap_lottery(start_date, end_date, season)
        if has_lottery_dates:
            phase_made = season.phase
        else:
            phase_made = 'open_booking'

        reservation = Reservation(season_id=season.id, member_id=member.id,
                                  start_date=start_date, end_date=end_date,
                                  phase_made=phase_made, notes=notes)
        db.session.add(reservation)
        if has_lottery_dates:
            if season.phase == PhaseState.PHASE1_DRAFT:
                draft_entry = DraftOrder.query.filter_by(season_id=season.id, member_id=member.id).first()
                if draft_entry:
                    draft_entry.phase1_picked = True
            elif season.phase == PhaseState.PHASE3_REVERSE:
                draft_entry = DraftOrder.query.filter_by(season_id=season.id, member_id=member.id).first()
                if draft_entry:
                    draft_entry.phase3_picked = True
        db.session.commit()
        if has_lottery_dates:
            PhaseEngine._maybe_advance_draft_phase(season)
            PhaseEngine._ensure_current_pick_has_deadline(season)
        return reservation

    @staticmethod
    def cancel_reservation(reservation):
        reservation.is_cancelled = True
        reservation.cancelled_at = get_now()
        db.session.commit()

    @staticmethod
    def trade_reservation(reservation, new_member):
        reservation.member_id = new_member.id
        db.session.commit()
