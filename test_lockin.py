"""Tests for lock-in draft flow and updated block rule."""

import sys, os
sys.path.insert(0, '/sessions/sweet-quirky-lovelace/mnt/Silvies-Calendar-Lottery-and-Reservation-System')

import unittest
from datetime import date, datetime, timedelta


class TestConfig:
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SERVER_NAME = 'localhost'
    SECRET_KEY = 'test-secret-key'
    LOTTERY_START_MONTH = 4
    LOTTERY_START_DAY = 1
    LOTTERY_END_MONTH = 8
    LOTTERY_END_DAY = 7
    HUNTING_SEASON_MONTHS = [8, 9, 10, 11]
    MAX_RESERVATION_DAYS = 7
    PHASE1_PICK_DAYS = 5
    PHASE3_PICK_DAYS = 3
    MAIL_SUPPRESS_SEND = True
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'test@test.com'
    RESET_TOKEN_EXPIRY = 3600


def make_app():
    from app import create_app
    return create_app(config_class=TestConfig)


def setup_draft_season(db, season_class, member_class, draft_class, phase_class, phase_engine):
    """Helper: create a season in Phase 1 draft with 3 members opted in."""
    season = season_class(year=2026, phase=phase_class.PHASE1_DRAFT)
    db.session.add(season)

    members = []
    for i, (name, email) in enumerate([
        ('Alice', 'alice@test.com'),
        ('Bob', 'bob@test.com'),
        ('Carol', 'carol@test.com'),
    ]):
        m = member_class(name=name, email=email, role='regular')
        m.set_password('test')
        db.session.add(m)
        members.append(m)

    db.session.flush()

    for i, m in enumerate(members):
        entry = draft_class(season_id=season.id, member_id=m.id, position=i + 1)
        db.session.add(entry)

    db.session.commit()

    # Set deadline for first picker
    phase_engine._ensure_current_pick_has_deadline(season)

    return season, members


class TestBlockRuleAnyStartDay(unittest.TestCase):
    """Block rule: reservation can START any day within Fri-Thu block,
    but must END by the Thursday of that block."""

    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Season, Member, DraftOrder, PhaseState
        from app.phase_engine import PhaseEngine
        self.db = db
        self.PhaseState = PhaseState
        self.PhaseEngine = PhaseEngine

        self.season = Season(year=2026, phase=PhaseState.PHASE1_DRAFT)
        db.session.add(self.season)

        self.member = Member(name='Test', email='test@test.com', role='regular')
        self.member.set_password('test')
        db.session.add(self.member)
        db.session.flush()

        self.draft_entry = DraftOrder(
            season_id=self.season.id, member_id=self.member.id, position=1)
        db.session.add(self.draft_entry)
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_start_on_friday_end_thursday(self):
        """Classic full-week Fri-Thu block: allowed."""
        # April 3, 2026 is a Friday
        start = date(2026, 4, 3)
        end = date(2026, 4, 9)  # Thursday
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertTrue(valid, f"Should allow Fri-Thu block: {err}")

    def test_start_on_monday_end_thursday(self):
        """Start Monday, end Thursday of same block: allowed."""
        start = date(2026, 4, 6)  # Monday
        end = date(2026, 4, 9)    # Thursday
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertTrue(valid, f"Should allow Mon-Thu: {err}")

    def test_start_on_wednesday_end_thursday(self):
        """Start Wednesday, end Thursday: allowed."""
        start = date(2026, 4, 8)  # Wednesday
        end = date(2026, 4, 9)    # Thursday
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertTrue(valid, f"Should allow Wed-Thu: {err}")

    def test_single_day_tuesday(self):
        """Single day on a Tuesday: allowed."""
        start = date(2026, 4, 7)  # Tuesday
        end = date(2026, 4, 7)
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertTrue(valid, f"Should allow single-day Tue: {err}")

    def test_start_saturday_end_next_thursday(self):
        """Start Saturday, end next Thursday: allowed (same block)."""
        start = date(2026, 4, 4)  # Saturday
        end = date(2026, 4, 9)    # Thursday
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertTrue(valid, f"Should allow Sat-Thu: {err}")

    def test_cross_block_boundary_rejected(self):
        """Reservation crossing from one block into the next Thursday: rejected."""
        # Fri Apr 3 block ends Thu Apr 9
        start = date(2026, 4, 6)   # Monday
        end = date(2026, 4, 10)    # Friday (next block)
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertFalse(valid, "Should reject crossing block boundary")
        self.assertIn('Thursday', err)

    def test_start_friday_cross_into_next_week(self):
        """Fri start crossing into next block's dates: rejected."""
        start = date(2026, 4, 3)   # Friday
        end = date(2026, 4, 11)    # Saturday of next block
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertFalse(valid, "Should reject Fri crossing to next block")

    def test_block_rule_not_applied_in_phase3(self):
        """Phase 3 reverse draft: block rule applies."""
        self.season.phase = self.PhaseState.PHASE3_REVERSE
        self.draft_entry.phase3_picked = False
        self.db.session.commit()
        # Phase 3 does NOT have the block rule (only Phase 1 and 2)
        start = date(2026, 4, 6)  # Monday
        end = date(2026, 4, 12)   # Sunday (crosses block boundary)
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertTrue(valid, f"Phase 3 should not enforce block rule: {err}")

    def test_block_rule_not_applied_in_open_fcfs(self):
        """Open FCFS: no block rule."""
        self.season.phase = self.PhaseState.OPEN_FCFS
        self.db.session.commit()
        start = date(2026, 4, 6)
        end = date(2026, 4, 12)
        valid, err = self.PhaseEngine.validate_reservation(
            self.season, self.member, start, end)
        self.assertTrue(valid, f"Open FCFS should not enforce block rule: {err}")


class TestLockInFlow(unittest.TestCase):
    """Test the lock-in reservation flow during draft phases."""

    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Season, Member, DraftOrder, Reservation, PhaseState
        from app.phase_engine import PhaseEngine
        self.db = db
        self.PhaseState = PhaseState
        self.PhaseEngine = PhaseEngine
        self.Reservation = Reservation
        self.DraftOrder = DraftOrder

        self.season, self.members = setup_draft_season(
            db, Season, Member, DraftOrder, PhaseState, PhaseEngine)
        self.alice, self.bob, self.carol = self.members

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_reservation_does_not_auto_advance(self):
        """Making a reservation during draft does NOT advance to next picker."""
        # Alice is position 1, should be current pick
        current = self.season.current_pick
        self.assertEqual(current.member_id, self.alice.id)

        # Alice makes a reservation
        res = self.PhaseEngine.make_reservation(
            self.season, self.alice, date(2026, 4, 3), date(2026, 4, 9))
        self.assertIsNotNone(res)

        # Still Alice's turn — draft should NOT have advanced
        current_after = self.season.current_pick
        self.assertEqual(current_after.member_id, self.alice.id,
                         "Draft should NOT auto-advance after reservation")

    def test_lock_in_advances_draft(self):
        """Locking in should mark as picked and advance to next person."""
        # Alice makes reservation then locks in
        self.PhaseEngine.make_reservation(
            self.season, self.alice, date(2026, 4, 3), date(2026, 4, 9))

        success, msg = self.PhaseEngine.lock_in_pick(self.season, self.alice)
        self.assertTrue(success, f"Lock-in should succeed: {msg}")

        # Now it should be Bob's turn
        current = self.season.current_pick
        self.assertEqual(current.member_id, self.bob.id,
                         "After lock-in, draft should advance to Bob")

    def test_lock_in_without_reservation_fails(self):
        """Can't lock in if no reservation made."""
        success, msg = self.PhaseEngine.lock_in_pick(self.season, self.alice)
        self.assertFalse(success, "Lock-in should fail without a reservation")
        self.assertIn('make a reservation', msg.lower())

    def test_lock_in_wrong_member_fails(self):
        """Can't lock in if it's not your turn."""
        success, msg = self.PhaseEngine.lock_in_pick(self.season, self.bob)
        self.assertFalse(success, "Lock-in should fail for wrong member")
        self.assertIn('not your turn', msg.lower())

    def test_lock_in_not_draft_phase_fails(self):
        """Lock-in only works during draft phases."""
        self.season.phase = self.PhaseState.PHASE2_FCFS
        self.db.session.commit()
        success, msg = self.PhaseEngine.lock_in_pick(self.season, self.alice)
        self.assertFalse(success, "Lock-in should fail outside draft phase")

    def test_cancel_and_repick(self):
        """Member can cancel their draft reservation and make a new one."""
        # Alice makes a reservation
        res = self.PhaseEngine.make_reservation(
            self.season, self.alice, date(2026, 4, 3), date(2026, 4, 9))

        # Alice cancels it
        self.PhaseEngine.cancel_reservation(res)
        self.assertTrue(res.is_cancelled)

        # Still Alice's turn
        current = self.season.current_pick
        self.assertEqual(current.member_id, self.alice.id)

        # Alice makes a different reservation
        res2 = self.PhaseEngine.make_reservation(
            self.season, self.alice, date(2026, 4, 10), date(2026, 4, 16))
        self.assertIsNotNone(res2)

        # Lock in the new one
        success, msg = self.PhaseEngine.lock_in_pick(self.season, self.alice)
        self.assertTrue(success)

        # Bob's turn now
        current = self.season.current_pick
        self.assertEqual(current.member_id, self.bob.id)

    def test_get_current_draft_reservation(self):
        """get_current_draft_reservation returns the active draft res."""
        # No reservation yet
        res = self.PhaseEngine.get_current_draft_reservation(self.season, self.alice)
        self.assertIsNone(res)

        # Make one
        made = self.PhaseEngine.make_reservation(
            self.season, self.alice, date(2026, 4, 3), date(2026, 4, 9))

        res = self.PhaseEngine.get_current_draft_reservation(self.season, self.alice)
        self.assertIsNotNone(res)
        self.assertEqual(res.id, made.id)

        # Cancel it
        self.PhaseEngine.cancel_reservation(made)
        res = self.PhaseEngine.get_current_draft_reservation(self.season, self.alice)
        self.assertIsNone(res, "Cancelled reservation should not be returned")

    def test_full_draft_advances_to_phase2(self):
        """When all members lock in, phase should advance to Phase 2."""
        # Each member picks and locks in
        dates = [
            (date(2026, 4, 3), date(2026, 4, 9)),
            (date(2026, 4, 10), date(2026, 4, 16)),
            (date(2026, 4, 17), date(2026, 4, 23)),
        ]
        for member, (start, end) in zip(self.members, dates):
            self.PhaseEngine.make_reservation(self.season, member, start, end)
            self.PhaseEngine.lock_in_pick(self.season, member)

        self.assertEqual(self.season.phase, self.PhaseState.PHASE2_FCFS,
                         "Phase should advance to Phase 2 after all picks locked in")


class TestDeadlineAutoLock(unittest.TestCase):
    """Test that deadline expiry auto-locks if reservation exists, skips if not."""

    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Season, Member, DraftOrder, Reservation, PhaseState
        from app.phase_engine import PhaseEngine
        self.db = db
        self.PhaseState = PhaseState
        self.PhaseEngine = PhaseEngine
        self.DraftOrder = DraftOrder
        self.Reservation = Reservation

        self.season, self.members = setup_draft_season(
            db, Season, Member, DraftOrder, PhaseState, PhaseEngine)
        self.alice, self.bob, self.carol = self.members

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_deadline_expiry_with_reservation_auto_locks(self):
        """If deadline expires and member has a reservation, it gets auto-locked."""
        # Alice makes a reservation
        self.PhaseEngine.make_reservation(
            self.season, self.alice, date(2026, 4, 3), date(2026, 4, 9))

        # Expire Alice's deadline
        entry = self.DraftOrder.query.filter_by(
            season_id=self.season.id, member_id=self.alice.id).first()
        entry.phase1_pick_deadline = datetime(2020, 1, 1)  # In the past
        self.db.session.commit()

        # Check deadlines — should auto-lock Alice
        advanced = self.PhaseEngine.check_and_advance_deadlines(self.season)
        self.assertEqual(advanced, 1)

        # Alice's reservation should still be there (not cancelled)
        res = self.Reservation.query.filter_by(
            season_id=self.season.id, member_id=self.alice.id,
            is_cancelled=False).first()
        self.assertIsNotNone(res, "Reservation should be kept after auto-lock")

        # Bob should now be current pick
        current = self.season.current_pick
        self.assertEqual(current.member_id, self.bob.id)

    def test_deadline_expiry_without_reservation_skips(self):
        """If deadline expires and member has NO reservation, they get skipped."""
        # Don't make a reservation for Alice — just expire her deadline
        entry = self.DraftOrder.query.filter_by(
            season_id=self.season.id, member_id=self.alice.id).first()
        entry.phase1_pick_deadline = datetime(2020, 1, 1)
        self.db.session.commit()

        advanced = self.PhaseEngine.check_and_advance_deadlines(self.season)
        self.assertEqual(advanced, 1)

        # No reservation for Alice
        res = self.Reservation.query.filter_by(
            season_id=self.season.id, member_id=self.alice.id,
            is_cancelled=False).first()
        self.assertIsNone(res, "No reservation should exist after skip")

        # Bob should now be current pick
        current = self.season.current_pick
        self.assertEqual(current.member_id, self.bob.id)


if __name__ == '__main__':
    unittest.main()
