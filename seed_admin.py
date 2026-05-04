"""Seed the database with an admin (Spike) account."""

from app import create_app, db
from app.models import Member, MemberRole

app = create_app()

with app.app_context():
    db.create_all()

    existing = Member.query.filter_by(email='tlchristensen9@gmail.com').first()
    if existing:
        print(f'Admin already exists: {existing.name} ({existing.email})')
    else:
        admin = Member(
            name='Thomas Christensen',
            email='tlchristensen9@gmail.com',
            role=MemberRole.ADMIN
        )
        admin.set_password('changeme')
        db.session.add(admin)
        db.session.commit()
        print(f'Admin created: {admin.name} ({admin.email})')
        print('Default password: changeme  (change it after first login)')
