"""Tests for admin tools: time travel, deadline overrides, season reset."""

import sys
sys.path.insert(0, '/sessions/sweet-quirky-lovelace/mnt/Silvies-Calendar-Lottery-and-Reservation-System')

import unittest
from datetime import datetime, date, timedelta


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
    DEBUG_TIME_TRAVEL = True
    PHASE1_PICK_DAYS = 5
    PHASE3_PICK_DAYS = 3


def make_app():
    from app import create_app
    return create_app(config_class=TestConfig)


class TestTimeTravel(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import AppSetting
        self.db = db

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def test_get_now_without_override(self):
        from app.utils import get_now
        now = get_now()
        real_now = datetime.utcnow()
        # Should be within 2 seconds of real time
        self.assertAlmostEqual(now.timestamp(), real_now.timestamp(), delta=2)

    def test_get_now_with_override(self):
        from app.utils import get_now
        from app.models import AppSetting
        fake_time = datetime(2026, 7, 15, 10, 30, 0)
        AppSetting.set('time_override', fake_time.isoformat())
        result = get_now()
        self.assertEqual(result, fake_time)

    def test_get_today_with_override(self):
        from app.utils import get_today
        from app.models import AppSetting
        fake_time = datetime(2026, 7, 15, 10, 30, 0)
        AppSetting.set('time_override', fake_time.isoformat())
        result = get_today()
        self.assertEqual(result, date(2026, 7, 15))

    def test_clear_override(self):
        from app.utils import get_now
        from app.models import AppSetting
        fake_time = datetime(2026, 7, 15, 10, 30, 0)
        AppSetting.set('time_override', fake_time.isoformat())
        self.assertEqual(get_now(), fake_time)
        AppSetting.delete('time_override')
        now = get_now()
        real_now = datetime.utcnow()
        self.assertAlmostEqual(now.timestamp(), real_now.timestamp(), delta=2)

    def test_time_travel_disabled(self):
        """When DEBUG_TIME_TRAVEL is False, override should be ignored."""
        from app.models import AppSetting
        AppSetting.set('time_override', datetime(2026, 7, 15, 10, 30, 0).isoformat())
        self.app.config['DEBUG_TIME_TRAVEL'] = False
        from app.utils import get_now
        now = get_now()
        real_now = datetime.utcnow()
        self.assertAlmostEqual(now.timestamp(), real_now.timestamp(), delta=2)
        self.app.config['DEBUG_TIME_TRAVEL'] = True  # restore


class TestAdminToolsRoutes(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Member, Season, MemberRole
        self.db = db
        self.admin = Member(name='Admin', email='admin@test.com', role=MemberRole.ADMIN)
        self.admin.set_password('adminpass')
        db.session.add(self.admin)
        self.season = Season(year=2026)
        db.session.add(self.season)
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def _login(self, client):
        client.post('/login', data={'email': 'admin@test.com', 'password': 'adminpass'})

    def test_tools_page_loads(self):
        client = self.app.test_client()
        self._login(client)
        resp = client.get('/admin/tools')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Time Travel', resp.data)

    def test_time_set(self):
        from app.models import AppSetting
        client = self.app.test_client()
        self._login(client)
        resp = client.post('/admin/tools/time-set', data={
            'override_date': '2026-07-15',
            'override_time': '10:30'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        override = AppSetting.get('time_override')
        self.assertIsNotNone(override)
        self.assertIn('2026-07-15', override)

    def test_time_jump(self):
        from app.models import AppSetting
        from app.utils import get_now
        client = self.app.test_client()
        self._login(client)
        # Set initial time
        client.post('/admin/tools/time-set', data={
            'override_date': '2026-07-15',
            'override_time': '10:00'
        })
        # Jump 6 hours
        client.post('/admin/tools/time-jump', data={'jump_hours': '6'})
        now = get_now()
        self.assertEqual(now.hour, 16)  # 10:00 + 6h = 16:00

    def test_time_clear(self):
        from app.models import AppSetting
        client = self.app.test_client()
        self._login(client)
        AppSetting.set('time_override', '2026-07-15T10:00:00')
        client.post('/admin/tools/time-clear')
        self.assertIsNone(AppSetting.get('time_override'))


class TestDeadlineOverride(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import Member, Season, DraftOrder, MemberRole, PhaseState
        self.db = db
        self.admin = Member(name='Admin', email='admin@test.com', role=MemberRole.ADMIN)
        self.admin.set_password('adminpass')
        self.member = Member(name='Test', email='test@test.com', role=MemberRole.REGULAR)
        self.member.set_password('testpass')
        self.season = Season(year=2026, phase=PhaseState.PHASE1_DRAFT)
        db.session.add_all([self.admin, self.member, self.season])
        db.session.commit()
        # Add draft order
        draft = DraftOrder(season_id=self.season.id, member_id=self.member.id,
                          position=1, phase1_picked=False)
        db.session.add(draft)
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def _login(self, client):
        client.post('/login', data={'email': 'admin@test.com', 'password': 'adminpass'})

    def test_set_deadline_override(self):
        from app.models import Season
        client = self.app.test_client()
        self._login(client)
        client.post('/admin/tools/deadlines', data={
            'phase1_pick_hours': '2',
            'phase3_pick_hours': '1'
        }, follow_redirects=True)
        season = Season.query.get(self.season.id)
        self.assertEqual(season.phase1_pick_hours, 2)
        self.assertEqual(season.phase3_pick_hours, 1)

    def test_deadline_override_affects_engine(self):
        from app.phase_engine import PhaseEngine
        from app.utils import get_now
        self.season.phase1_pick_hours = 2  # 2 hours instead of 5 days
        self.db.session.commit()
        PhaseEngine._ensure_current_pick_has_deadline(self.season)
        draft = self.season.current_pick
        self.assertIsNotNone(draft.phase1_pick_deadline)
        expected = get_now() + timedelta(hours=2)
        # Should be within 5 seconds
        self.assertAlmostEqual(
            draft.phase1_pick_deadline.timestamp(),
            expected.timestamp(),
            delta=5
        )


class TestResetSeason(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        from app import db
        from app.models import (Member, Season, DraftOrder, Reservation,
                                MemberRole, PhaseState)
        self.db = db
        self.admin = Member(name='Admin', email='admin@test.com', role=MemberRole.ADMIN)
        self.admin.set_password('adminpass')
        self.member = Member(name='Test', email='test@test.com', role=MemberRole.REGULAR)
        self.member.set_password('testpass')
        self.season = Season(year=2026, phase=PhaseState.PHASE2_FCFS)
        db.session.add_all([self.admin, self.member, self.season])
        db.session.commit()
        # Add some data to be wiped
        draft = DraftOrder(season_id=self.season.id, member_id=self.member.id, position=1)
        res = Reservation(season_id=self.season.id, member_id=self.member.id,
                         start_date=date(2026, 5, 1), end_date=date(2026, 5, 7),
                         phase_made='phase2_fcfs')
        db.session.add_all([draft, res])
        db.session.commit()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()
        self.ctx.pop()

    def _login(self, client):
        client.post('/login', data={'email': 'admin@test.com', 'password': 'adminpass'})

    def test_reset_with_correct_year(self):
        from app.models import Season, Reservation, DraftOrder, PhaseState
        client = self.app.test_client()
        self._login(client)
        client.post(f'/admin/season/{self.season.id}/reset', data={
            'confirm_year': '2026'
        }, follow_redirects=True)
        season = Season.query.get(self.season.id)
        self.assertEqual(season.phase, PhaseState.SETUP)
        self.assertEqual(Reservation.query.filter_by(season_id=season.id).count(), 0)
        self.assertEqual(DraftOrder.query.filter_by(season_id=season.id).count(), 0)

    def test_reset_with_wrong_year_rejected(self):
        from app.models import Season, Reservation, DraftOrder, PhaseState
        client = self.app.test_client()
        self._login(client)
        client.post(f'/admin/season/{self.season.id}/reset', data={
            'confirm_year': '9999'
        }, follow_redirects=True)
        season = Season.query.get(self.season.id)
        # Should NOT have been reset
        self.assertEqual(season.phase, PhaseState.PHASE2_FCFS)
        self.assertGreater(Reservation.query.filter_by(season_id=season.id).count(), 0)

    def test_reset_with_empty_year_rejected(self):
        from app.models import Season, PhaseState
        client = self.app.test_client()
        self._login(client)
        client.post(f'/admin/season/{self.season.id}/reset', data={
            'confirm_year': ''
        }, follow_redirects=True)
        season = Season.query.get(self.season.id)
        self.assertEqual(season.phase, PhaseState.PHASE2_FCFS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
