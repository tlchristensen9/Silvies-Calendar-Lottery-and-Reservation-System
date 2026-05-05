Project Context: Silvies Club Lottery \& Reservation System

1. Project Overview
A Flask-based web application for managing annual cabin reservations for the Silvies Club. The system utilizes a multi-phase lottery to manage high-demand "Lottery Dates" (April 1 – August 7) and transitions to open booking for the remainder of the year.
2. Core Logic: The Phase Engine
The PhaseEngine (app/phase\_engine.py) governs the application lifecycle:

SETUP: Configuration of the upcoming season.

PHASE1\_OPTIN: Members register interest in the lottery.

PHASE1\_DRAFT: Randomized draft where each member has a 5-day deadline to pick.

PHASE2\_FCFS: First-come, first-served for members who skipped the draft.

PHASE3\_REVERSE: Second draft in reverse order of Phase 1 with a 3-day deadline.

OPEN\_FCFS: General availability for all dates.

CLOSED: End of season.

3. Technical Architecture \& Constraints
Environment: PythonAnywhere (Free tier).

Backend: Flask, SQLAlchemy, Python.

4. Business Rules for Reservations
The Friday-Thursday Rule: During lottery phases, reservations are restricted to "blocks." A stay can start any day within a Friday-Thursday block, but must end by the following Thursday to ensure the cabin is clear for the next weekend's arrival.

Max Stay: 7 days.

Blackout Dates: August 8 through November is reserved for hunting season and is not managed via this reservation system.

Always available dates: the months of December-March are always available to reserve for any member.

5. Developer \& Operational Notes
Database Models: Member (Roles: Regular, Lifetime, Admin), Season, DraftOrder (tracks lottery deadlines), and Reservation.

6\. Making changes: Always use bash cat or sed to edit files instead of the internal File Edit tool. This avoids mount caching and truncation issues in this environment.

7\. Testing changes: Only run the specific test related to the changes made in a given prompt response, not an entire test suite for every change. When there is low risk of code change interdependencies make multiple changes and then perform a single test.

8\. PythonAnywhere Limitations: The system avoids complex background tasks; logic typically triggers on-demand when a user visits the dashboard or an admin interacts with the PhaseEngine.

9\. Formatting: Maintain a clean, functional code style. When adding features, prioritize centralizing logic in utils.py or phase\_engine.py rather than duplicating it in routes.

