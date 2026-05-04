"""Seed the database with all club members from the Silvies Club roster."""

from app import create_app, db
from app.models import Member, MemberRole

app = create_app()

# Member roster: (name, email, phone, role)
MEMBERS = [
    ('Andrew Burton', 'coastrange541@gmail.com', '541-602-7234', MemberRole.REGULAR),
    ('Tom Christensen', 'tlchristensen9@gmail.com', '541-207-8752', MemberRole.ADMIN),
    ('Tim Jensen', 'tim.jensen@oregonstate.edu', '419-531-6226', MemberRole.REGULAR),
    ('Nate Koenigsknecht', 'nkoenigsknecht@gmail.com', '541-602-2927', MemberRole.REGULAR),
    ('Jason Koertge', 'jason@meatisgoodforyou.com', '503-869-8899', MemberRole.REGULAR),
    ('John Larison', 'john.larison@gmail.com', '541-829-1488', MemberRole.REGULAR),
    ('Ted Larison', 'larison77@gmail.com', '512-567-2806', MemberRole.REGULAR),
]

with app.app_context():
    db.create_all()

    added = 0
    skipped = 0
    for name, email, phone, role in MEMBERS:
        existing = Member.query.filter_by(email=email.lower()).first()
        if existing:
            print(f'  SKIP  {name} ({email}) — already exists')
            skipped += 1
        else:
            member = Member(
                name=name,
                email=email.lower(),
                phone=phone,
                role=role
            )
            member.set_password('changeme')
            db.session.add(member)
            added += 1
            print(f'  ADD   {name} ({email}) [{role}]')

    db.session.commit()
    print(f'\nDone: {added} added, {skipped} skipped.')
    if added:
        print('Default password for all new members: changeme')
