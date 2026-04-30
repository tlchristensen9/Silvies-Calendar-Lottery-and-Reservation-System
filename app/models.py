"""Database models for Silvies Club Calendar Reservation System."""

from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


class MemberRole:
    REGULAR = 'regular'
    LIFETIME = 'lifetime'
    ADMIN = 'admin'


class PhaseState:
    SETUP = 'setup'
    PHASE1_OPTIN = 'phase1_optin'
    PHASE1_DRAFT = 'phase1_draft'
    PHASE2_FCFS = 'phase2_fcfs'
    PHASE3_REVERSE = 'phase3_reverse'
    OPEN_FCFS = 'open_fcfs'
    CLOSED = 'closed'


class Member(UserMixin, db.Model):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=MemberRole.REGULAR)
    is_active_member = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reservations = db.relationship('Reservation', backref='member', lazy='dynamic')
    draft_entries = db.relationship('DraftOrder', backref='member', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == MemberRole.ADMIN

    @property
    def is_lifetime(self):
        return self.role == MemberRole.LIFETIME

    @property
    def can_enter_draft(self):
        return self.role in (MemberRole.REGULAR, MemberRole.ADMIN)

    def __repr__(self):
        return f'<Member {self.name}>'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Member, int(user_id))


class Season(db.Model):
    __tablename__ = 'seasons'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False)
    phase = db.Column(db.String(30), nullable=False, default=PhaseState.SETUP)
    phase1_optin_start = db.Column(db.Date, nullable=True)
    phase1_draft_date = db.Column(db.Date, nullable=True)
    phase2_start = db.Column(db.Date, nullable=True)
    phase3_start = db.Column(db.Date, nullable=True)
    open_fcfs_start = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    draft_orders = db.relationship('DraftOrder', backref='season', lazy='dynamic', cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', backref='season', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def is_active(self):
        return self.phase not in (PhaseState.SETUP, PhaseState.CLOSED)

    @property
    def current_pick(self):
        if self.phase == PhaseState.PHASE1_DRAFT:
            return (DraftOrder.query
                    .filter_by(season_id=self.id, phase1_picked=False)
                    .filter(DraftOrder.position > 0)
                    .order_by(DraftOrder.position.asc())
                    .first())
        elif self.phase == PhaseState.PHASE3_REVERSE:
            return (DraftOrder.query
                    .filter_by(season_id=self.id, phase3_picked=False)
                    .filter(DraftOrder.position > 0)
                    .order_by(DraftOrder.position.desc())
                    .first())
        return None

    @property
    def season_start(self):
        """First day of the full calendar year."""
        return date(self.year, 1, 1)

    @property
    def season_end(self):
        """Last day of the full calendar year."""
        return date(self.year, 12, 31)

    @property
    def lottery_start(self):
        """First day of lottery-controlled months (May 1)."""
        return date(self.year, 5, 1)

    @property
    def lottery_end(self):
        """Last day of lottery-controlled months (June 30)."""
        return date(self.year, 6, 30)

    def __repr__(self):
        return f'<Season {self.year} [{self.phase}]>'


class DraftOrder(db.Model):
    __tablename__ = 'draft_orders'
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    phase1_picked = db.Column(db.Boolean, default=False)
    phase1_pick_deadline = db.Column(db.DateTime, nullable=True)
    phase3_picked = db.Column(db.Boolean, default=False)
    phase3_pick_deadline = db.Column(db.DateTime, nullable=True)
    opted_in_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('season_id', 'member_id', name='uq_draft_season_member'),
    )

    def __repr__(self):
        return f'<DraftOrder Season={self.season_id} #{self.position} Member={self.member_id}>'


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey('seasons.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    phase_made = db.Column(db.String(30), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    is_cancelled = db.Column(db.Boolean, default=False)

    @property
    def num_days(self):
        return (self.end_date - self.start_date).days + 1

    @property
    def is_active(self):
        return not self.is_cancelled

    def overlaps_with(self, start, end):
        if self.is_cancelled:
            return False
        return self.start_date <= end and self.end_date >= start

    def __repr__(self):
        return f'<Reservation {self.start_date} to {self.end_date} by Member {self.member_id}>'
