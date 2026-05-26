"""Seed the database with all club members from the Silvies Club 2026 roster.

Spike/Admin account uses silviesclub1946@gmail.com and is created first.
All active and lifetime members are created separately as non-admin accounts.
Default password for all accounts: changeme
"""

from app import create_app, db
from app.models import Member, MemberRole

app = create_app()

# ------------------------------------------------------------------
# Spike / Admin account (separate from member accounts)
# ------------------------------------------------------------------
ADMIN = {
    'name': 'Spike',
    'email': 'silviesclub1946@gmail.com',
    'phone': None,
    'role': MemberRole.ADMIN,
}

# ------------------------------------------------------------------
# Active Members (20)
# ------------------------------------------------------------------
MEMBERS = [
    ('Andrew Burton',           'coastrange541@gmail.com',           '541-602-7234',  MemberRole.REGULAR),
    ('Don Brown',               'doncapitol11@gmail.com',            '503-930-6022',  MemberRole.REGULAR),
    ('Tom Christensen',         'tlchristensen9@gmail.com',          '541-207-8752',  MemberRole.REGULAR),
    ('Dan Croft',               'dan.merideth@gmail.com',            '503-330-5504',  MemberRole.REGULAR),
    ('Bob Culp',                'culpba@yahoo.com',                  '503-580-9669',  MemberRole.REGULAR),
    ('Bruce Devlin',            'bhdevlin@icloud.com',               '971-832-0663',  MemberRole.REGULAR),
    ('Daniel Hitchcock',        'danjenh@yahoo.com',                 '971-570-7039',  MemberRole.REGULAR),
    ('Tim Jensen',              'tim.jensen@oregonstate.edu',        '419-531-6226',  MemberRole.REGULAR),
    ('Nate Koenigsknecht',      'nkoenigsknecht@gmail.com',          '541-602-2927',  MemberRole.REGULAR),
    ('Jason Koertge',           'jason@meatisgoodforyou.com',        '503-869-8899',  MemberRole.REGULAR),
    ('John Larison',            'john.larison@gmail.com',            '541-829-1488',  MemberRole.REGULAR),
    ('Ted Larison',             'larison77@gmail.com',               '512-567-2806',  MemberRole.REGULAR),
    ('Cam Little',              'cam.liza.little@comcast.net',       '541-760-0578',  MemberRole.REGULAR),
    ('Rex Newell',              'newell5626@msn.com',                '503-559-0291',  MemberRole.REGULAR),
    ('Jay Prall',               'kilo17@comcast.net',                '503-932-7836',  MemberRole.REGULAR),
    ('Tyler Prall',             'tjprall@comcast.net',               '971-600-6555',  MemberRole.REGULAR),
    ('Tim Tubb',                'timt@johnlscott.com',               '971-506-8822',  MemberRole.REGULAR),
    ('Garrett Wampler',         'garrett.wampler1@gmail.com',        '503-569-0770',  MemberRole.REGULAR),
    ('Tyler Wampler',           'k14tyler@comcast.net',              '503-932-7725',  MemberRole.REGULAR),
    ('Trevor Williamson',       'trevorwilliamson92@gmail.com',      '503-990-3110',  MemberRole.REGULAR),
]

# ------------------------------------------------------------------
# Lifetime Honorary Members (2)
# ------------------------------------------------------------------
LIFETIME_MEMBERS = [
    ('Jim Larison',             'jim.elaine.larison@gmail.com',      '541-231-6816',  MemberRole.LIFETIME),
    ('Les Williamson',          'les.williamson46@gmail.com',        '503-932-3633',  MemberRole.LIFETIME),
]


def seed_account(name, email, phone, role):
    """Create a single member account if it doesn't already exist."""
    existing = Member.query.filter_by(email=email.lower()).first()
    if existing:
        print(f'  SKIP  {name} ({email}) -- already exists')
        return False
    member = Member(
        name=name,
        email=email.lower(),
        phone=phone,
        role=role,
    )
    member.set_password('changeme')
    db.session.add(member)
    print(f'  ADD   {name} ({email}) [{role}]')
    return True


with app.app_context():
    db.create_all()

    added = 0
    skipped = 0

    # --- Admin / Spike account ---
    print('=== Spike / Admin Account ===')
    if seed_account(ADMIN['name'], ADMIN['email'], ADMIN['phone'], ADMIN['role']):
        added += 1
    else:
        skipped += 1

    # --- Active members ---
    print('\n=== Active Members ===')
    for name, email, phone, role in MEMBERS:
        if seed_account(name, email, phone, role):
            added += 1
        else:
            skipped += 1

    # --- Lifetime members ---
    print('\n=== Lifetime Honorary Members ===')
    for name, email, phone, role in LIFETIME_MEMBERS:
        if seed_account(name, email, phone, role):
            added += 1
        else:
            skipped += 1

    db.session.commit()
    print(f'\nDone: {added} added, {skipped} skipped (total roster: {added + skipped}).')
    if added:
        print('Default password for all new accounts: changeme')
