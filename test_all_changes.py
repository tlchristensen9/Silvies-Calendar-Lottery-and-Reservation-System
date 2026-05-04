"""Comprehensive tests for all TODO items."""

import sys, os
sys.path.insert(0, '/sessions/sweet-quirky-lovelace/mnt/Silvies-Calendar-Lottery-and-Reservation-System')

import unittest
from datetime import date, timedelta


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


class TestLotteryPeriodExpansion(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Season
        self.db = db
        self.season = Season(year=2026)
        db.session.add(self.season)
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_lottery_start_date(self):
        self.assertEqual(self.season.lottery_start, date(2026, 4, 1))

    def test_lottery_end_date(self):
        self.assertEqual(self.season.lottery_end, date(2026, 8, 7))

    def test_april_is_lottery(self):
        from app.phase_engine import PhaseEngine
        self.assertTrue(PhaseEngine._is_lottery_date(date(2026, 4, 15), self.season))

    def test_july_is_lottery(self):
        from app.phase_engine import PhaseEngine
        self.assertTrue(PhaseEngine._is_lottery_date(date(2026, 7, 15), self.season))

    def test_aug7_is_lottery(self):
        from app.phase_engine import PhaseEngine
        self.assertTrue(PhaseEngine._is_lottery_date(date(2026, 8, 7), self.season))

    def test_aug8_is_not_lottery(self):
        from app.phase_engine import PhaseEngine
        self.assertFalse(PhaseEngine._is_lottery_date(date(2026, 8, 8), self.season))

    def test_march_is_not_lottery(self):
        from app.phase_engine import PhaseEngine
        self.assertFalse(PhaseEngine._is_lottery_date(date(2026, 3, 31), self.season))

    def test_aug8_is_hunting(self):
        from app.phase_engine import PhaseEngine
        self.assertTrue(PhaseEngine._is_hunting_date(date(2026, 8, 8), self.season))

    def test_aug7_is_not_hunting(self):
        from app.phase_engine import PhaseEngine
        self.assertFalse(PhaseEngine._is_hunting_date(date(2026, 8, 7), self.season))

    def test_november_is_hunting(self):
        from app.phase_engine import PhaseEngine
        self.assertTrue(PhaseEngine._is_hunting_date(date(2026, 11, 15), self.season))

    def test_december_is_not_hunting(self):
        from app.phase_engine import PhaseEngine
        self.assertFalse(PhaseEngine._is_hunting_date(date(2026, 12, 1), self.season))


class TestFridayThursdayBlockRule(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Season, Member, MemberRole, PhaseState
        self.db = db
        # Use Phase 2 - member must NOT be in the draft to reserve in Phase 2
        self.season = Season(year=2026, phase=PhaseState.PHASE2_FCFS)
        db.session.add(self.season)
        self.member = Member(name='Test User', email='test@example.com', role=MemberRole.REGULAR)
        self.member.set_password('password123')
        db.session.add(self.member)
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_block_start_from_friday(self):
        from app.phase_engine import PhaseEngine
        fri = date(2026, 4, 3)
        self.assertEqual(fri.weekday(), 4)
        self.assertEqual(PhaseEngine._get_fri_thu_block_start(fri), fri)

    def test_block_start_from_wednesday(self):
        from app.phase_engine import PhaseEngine
        wed = date(2026, 4, 8)
        self.assertEqual(wed.weekday(), 2)
        # Should go back to Friday April 3
        self.assertEqual(PhaseEngine._get_fri_thu_block_start(wed), date(2026, 4, 3))

    def test_block_end_from_friday(self):
        from app.phase_engine import PhaseEngine
        fri = date(2026, 4, 3)
        block_end = PhaseEngine._get_fri_thu_block_end(fri)
        self.assertEqual(block_end, date(2026, 4, 9))
        self.assertEqual(block_end.weekday(), 3)

    def test_block_end_from_thursday(self):
        from app.phase_engine import PhaseEngine
        thu = date(2026, 4, 9)
        block_end = PhaseEngine._get_fri_thu_block_end(thu)
        self.assertEqual(block_end, thu)

    def test_valid_fri_to_thu_reservation(self):
        from app.phase_engine import PhaseEngine
        # Friday May 1 to Thursday May 7, 2026
        fri = date(2026, 5, 1)
        thu = date(2026, 5, 7)
        self.assertEqual(fri.weekday(), 4)
        self.assertEqual(thu.weekday(), 3)
        ok, msg = PhaseEngine.validate_reservation(self.season, self.member, fri, thu)
        self.assertTrue(ok, f"Expected valid but got: {msg}")

    def test_non_friday_start_allowed_phase2(self):
        from app.phase_engine import PhaseEngine
        # Wednesday April 15 to Thursday April 16 — within same Fri-Thu block, should be allowed
        wed = date(2026, 4, 15)
        thu = date(2026, 4, 16)
        self.assertEqual(wed.weekday(), 2)
        ok, msg = PhaseEngine.validate_reservation(self.season, self.member, wed, thu)
        self.assertTrue(ok, f"Non-Friday start should be allowed within block: {msg}")

    def test_invalid_non_thursday_end_phase2(self):
        from app.phase_engine import PhaseEngine
        # Friday April 3 to Wednesday April 8 — valid start, but ends before Thursday still OK
        # Actually the rule is: reservation must be contained in Fri-Thu block
        # Fri Apr 3 to Wed Apr 8 is within the block (Fri Apr 3 - Thu Apr 9), so it SHOULD pass
        # The rule says must be CONTAINED in block, not that it must span full block
        fri = date(2026, 4, 3)
        wed = date(2026, 4, 8)
        self.assertEqual(fri.weekday(), 4)
        ok, msg = PhaseEngine.validate_reservation(self.season, self.member, fri, wed)
        # This should PASS because it's contained within the Fri-Thu block
        self.assertTrue(ok, f"Fri-to-Wed within block should be valid, got: {msg}")

    def test_reservation_spanning_two_blocks_rejected(self):
        from app.phase_engine import PhaseEngine
        # Friday April 3 to Friday April 10 — spans two blocks
        fri1 = date(2026, 4, 3)
        fri2 = date(2026, 4, 10)
        ok, msg = PhaseEngine.validate_reservation(self.season, self.member, fri1, fri2)
        self.assertFalse(ok, f"Cross-block reservation should be rejected")

    def test_phase3_no_block_rule(self):
        """Phase 3 should NOT enforce Friday-Thursday blocks."""
        from app.phase_engine import PhaseEngine
        from app.models import PhaseState, DraftOrder
        self.season.phase = PhaseState.PHASE3_REVERSE
        # Need a DraftOrder for this member so they can pick in Phase 3
        draft = DraftOrder(season_id=self.season.id, member_id=self.member.id,
                          position=1, phase3_picked=False)
        self.db.session.add(draft)
        self.db.session.commit()
        # Wednesday to Saturday in lottery period — no block rule in Phase 3
        wed = date(2026, 4, 15)
        sat = date(2026, 4, 18)
        ok, msg = PhaseEngine.validate_reservation(self.season, self.member, wed, sat)
        self.assertTrue(ok, f"Phase 3 should allow non-block reservations, got: {msg}")

    def test_open_phase_no_block_rule(self):
        """OPEN_FCFS should NOT enforce Friday-Thursday blocks."""
        from app.phase_engine import PhaseEngine
        from app.models import PhaseState
        self.season.phase = PhaseState.OPEN_FCFS
        self.db.session.commit()
        wed = date(2026, 4, 15)
        sat = date(2026, 4, 18)
        ok, msg = PhaseEngine.validate_reservation(self.season, self.member, wed, sat)
        self.assertTrue(ok, f"Open phase should allow non-block reservations, got: {msg}")


class TestPasswordRecovery(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        self.db = db

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_generate_and_verify_token(self):
        from app.routes.auth import _generate_reset_token, _verify_reset_token
        token = _generate_reset_token('test@example.com')
        self.assertIsNotNone(token)
        verified = _verify_reset_token(token, max_age=3600)
        self.assertEqual(verified, 'test@example.com')

    def test_invalid_token_returns_none(self):
        from app.routes.auth import _verify_reset_token
        self.assertIsNone(_verify_reset_token('invalid-token-xyz', max_age=3600))

    def test_forgot_password_route_exists(self):
        client = self.app.test_client()
        resp = client.get('/forgot-password')
        self.assertEqual(resp.status_code, 200)

    def test_forgot_password_post(self):
        from app.models import Member, MemberRole
        m = Member(name='Test', email='test@example.com', role=MemberRole.REGULAR)
        m.set_password('pass123')
        self.db.session.add(m)
        self.db.session.commit()
        client = self.app.test_client()
        resp = client.post('/forgot-password', data={'email': 'test@example.com'}, follow_redirects=False)
        self.assertIn(resp.status_code, [302, 200])


class TestSettingsPage(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Member, MemberRole
        self.db = db
        self.member = Member(name='Test User', email='test@example.com', phone='555-1234', role=MemberRole.REGULAR)
        self.member.set_password('oldpass123')
        db.session.add(self.member)
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def _login(self, client):
        client.post('/login', data={'email': 'test@example.com', 'password': 'oldpass123'})

    def test_settings_requires_login(self):
        client = self.app.test_client()
        resp = client.get('/settings', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

    def test_settings_page_loads(self):
        client = self.app.test_client()
        self._login(client)
        resp = client.get('/settings')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Account Settings', resp.data)

    def test_update_email(self):
        from app.models import Member
        client = self.app.test_client()
        self._login(client)
        client.post('/settings', data={
            'email': 'newemail@example.com', 'phone': '555-1234',
            'current_password': 'oldpass123', 'new_password': '', 'confirm_password': ''
        }, follow_redirects=True)
        member = Member.query.get(self.member.id)
        self.assertEqual(member.email, 'newemail@example.com')

    def test_update_phone(self):
        from app.models import Member
        client = self.app.test_client()
        self._login(client)
        client.post('/settings', data={
            'email': 'test@example.com', 'phone': '555-9999',
            'current_password': 'oldpass123', 'new_password': '', 'confirm_password': ''
        }, follow_redirects=True)
        member = Member.query.get(self.member.id)
        self.assertEqual(member.phone, '555-9999')

    def test_wrong_password_rejected(self):
        from app.models import Member
        client = self.app.test_client()
        self._login(client)
        client.post('/settings', data={
            'email': 'hack@example.com', 'phone': '',
            'current_password': 'wrongpassword', 'new_password': '', 'confirm_password': ''
        }, follow_redirects=True)
        member = Member.query.get(self.member.id)
        self.assertEqual(member.email, 'test@example.com')

    def test_change_password(self):
        from app.models import Member
        client = self.app.test_client()
        self._login(client)
        client.post('/settings', data={
            'email': 'test@example.com', 'phone': '555-1234',
            'current_password': 'oldpass123', 'new_password': 'newpass456', 'confirm_password': 'newpass456'
        }, follow_redirects=True)
        member = Member.query.get(self.member.id)
        self.assertTrue(member.check_password('newpass456'))


class TestAdminDeleteMember(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Member, MemberRole
        self.db = db
        self.admin = Member(name='Admin Spike', email='admin@example.com', role=MemberRole.ADMIN)
        self.admin.set_password('adminpass')
        self.target = Member(name='Delete Me', email='delete@example.com', role=MemberRole.REGULAR)
        self.target.set_password('pass123')
        db.session.add_all([self.admin, self.target])
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def _login_admin(self, client):
        client.post('/login', data={'email': 'admin@example.com', 'password': 'adminpass'})

    def test_delete_member(self):
        from app.models import Member
        client = self.app.test_client()
        self._login_admin(client)
        target_id = self.target.id
        client.post(f'/admin/members/{target_id}/delete', follow_redirects=True)
        self.assertIsNone(Member.query.get(target_id))

    def test_cannot_delete_self(self):
        from app.models import Member
        client = self.app.test_client()
        self._login_admin(client)
        admin_id = self.admin.id
        client.post(f'/admin/members/{admin_id}/delete', follow_redirects=True)
        self.assertIsNotNone(Member.query.get(admin_id))


class TestCalendarConfig(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Season
        self.db = db
        self.season = Season(year=2026)
        db.session.add(self.season)
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_calendar_config_dates(self):
        from app.phase_engine import PhaseEngine
        config = PhaseEngine.get_calendar_config(self.season)
        self.assertEqual(config['lottery_start'], '2026-04-01')
        self.assertEqual(config['lottery_end'], '2026-08-07')
        self.assertEqual(config['hunting_start'], '2026-08-08')
        self.assertEqual(config['hunting_end'], '2026-11-30')


class TestOpenBooking(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Season, Member, MemberRole, PhaseState
        self.db = db
        self.season = Season(year=2026, phase=PhaseState.OPEN_FCFS)
        db.session.add(self.season)
        self.member = Member(name='Test', email='test@example.com', role=MemberRole.REGULAR)
        self.member.set_password('pass123')
        db.session.add(self.member)
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_february_booking(self):
        from app.phase_engine import PhaseEngine
        ok, msg = PhaseEngine.validate_reservation(self.season, self.member, date(2026, 2, 10), date(2026, 2, 14))
        self.assertTrue(ok, f"Feb booking should work, got: {msg}")

    def test_december_booking(self):
        from app.phase_engine import PhaseEngine
        ok, msg = PhaseEngine.validate_reservation(self.season, self.member, date(2026, 12, 1), date(2026, 12, 5))
        self.assertTrue(ok, f"Dec booking should work, got: {msg}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
