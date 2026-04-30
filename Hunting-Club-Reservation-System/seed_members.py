"""Seed the database with the 21 current club members + admin (Spike) account.

Run once after creating the database:
    python seed_members.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Member, MemberRole

# Current club members — update names/emails/phones as needed
MEMBERS = [
    {"name": "John Smith", "email": "john.smith@email.com", "phone": "555-0101"},
    {"name": "Mike Johnson", "email": "mike.johnson@email.com", "phone": "555-0102"},
    {"name": "Robert Brown", "email": "robert.brown@email.com", "phone": "555-0103"},
    {"name": "William Davis", "email": "william.davis@email.com", "phone": "555-0104"},
    {"name": "James Miller", "email": "james.miller@email.com", "phone": "555-0105"},
    {"name": "David Wilson", "email": "david.wilson@email.com", "phone": "555-0106"},
    {"name": "Richard Moore", "email": "richard.moore@email.com", "phone": "555-0107"},
    {"name": "Joseph Taylor", "email": "joseph.taylor@email.com", "phone": "555-0108"},
    {"name": "Thomas Anderson", "email": "thomas.anderson@email.com", "phone": "555-0109"},
    {"name": "Charles Thomas", "email": "charles.thomas@email.com", "phone": "555-0110"},
    {"name": "Christopher Jackson", "email": "christopher.jackson@email.com", "phone": "555-0111"},
    {"name": "Daniel White", "email": "daniel.white@email.com", "phone": "555-0112"},
    {"name": "Matthew Harris", "email": "matthew.harris@email.com", "phone": "555-0113"},
    {"name": "Anthony Martin", "email": "anthony.martin@email.com", "phone": "555-0114"},
    {"name": "Mark Thompson", "email": "mark.thompson@email.com", "phone": "555-0115"},
    {"name": "Donald Garcia", "email": "donald.garcia@email.com", "phone": "555-0116"},
    {"name": "Steven Martinez", "email": "steven.martinez@email.com", "phone": "555-0117"},
    {"name": "Paul Rodriguez", "email": "paul.rodriguez@email.com", "phone": "555-0118"},
    {"name": "Andrew Lewis", "email": "andrew.lewis@email.com", "phone": "555-0119"},
    {"name": "Kenneth Walker", "email": "kenneth.walker@email.com", "phone": "555-0120"},
    {"name": "Joshua Hall", "email": "joshua.hall@email.com", "phone": "555-0121"},
]


def seed():
    app = create_app()

    with app.app_context():
        db.create_all()

        # Check if already seeded
        if Member.query.first():
            print("Database already has members. Skipping seed.")
            print(f"Total members: {Member.query.count()}")
            return

        # Create admin (Spike) account
        spike = Member(
            name="Spike Admin",
            email="spike@silviesclub.com",
            phone="555-0100",
            role=MemberRole.ADMIN
        )
        spike.set_password("silvies2027")
        db.session.add(spike)
        print("Created Spike admin account (spike@silviesclub.com / silvies2027)")

        # Create regular members
        for m in MEMBERS:
            member = Member(
                name=m["name"],
                email=m["email"],
                phone=m["phone"],
                role=MemberRole.REGULAR
            )
            member.set_password("changeme")
            db.session.add(member)

        db.session.commit()
        total = Member.query.count()
        print(f"Seeded {total} members (1 admin + {total - 1} regular).")
        print("Default member password: changeme")


if __name__ == "__main__":
    seed()
