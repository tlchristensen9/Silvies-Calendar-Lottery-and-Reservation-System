# Silvies Club Calendar Lottery & Reservation System — Technical Briefing

**Last updated:** May 5, 2026
**Status:** Feature-complete through TODOv2. Ready for deployment testing.

---

## What This Is

A Flask web app for a 30-member hunting/fishing club (Silvies Valley Ranch) to manage shared cabin reservations through a multi-phase lottery draft system. The "Spike" (club admin) runs the annual process; members log in to opt into the draft, pick dates during their turn, and manage their reservations.

## Tech Stack

Flask 3.1, Flask-SQLAlchemy (SQLite), Flask-Login, Flask-WTF, Flask-Mail, Flask-Migrate. Vanilla JS calendar UI. Deployed on PythonAnywhere. No background workers — deadline checks run on page load.

## The Calendar Year

The year is divided into three booking zones:

- **Open booking** (Jan 1 – Mar 31, and Dec): Any active member can reserve anytime. No lottery rules apply.
- **Lottery period** (Apr 1 – Aug 7): Reservations are controlled by the multi-phase draft system described below.
- **Hunting season** (Aug 8 – Nov 30): Cabin is open for hunting; no reservations needed or allowed.

These boundaries are configurable in `config.py` via `LOTTERY_START_MONTH/DAY`, `LOTTERY_END_MONTH/DAY`, and `HUNTING_SEASON_MONTHS`.

## The Draft System — Phase Flow

Phases advance manually by the admin (Spike), with one exception: draft phases auto-advance when all members have picked.

```
SETUP → PHASE1_OPTIN → PHASE1_DRAFT → PHASE2_FCFS → PHASE3_REVERSE → OPEN_FCFS → CLOSED
```

**SETUP:** Admin creates the season. No member actions.

**PHASE1_OPTIN:** Members opt in for the lottery draw. Lifetime members are excluded from the draw (they get priority outside the system). Admin can also opt members in manually.

**PHASE1_DRAFT:** Admin runs the draw, which randomizes opted-in members into a numbered order. Members pick one at a time, in order. Each member gets a configurable deadline (default 5 days) to select dates in the lottery period. Reservations are *tentative* until the member clicks "Lock In" on their dashboard. If they don't pick by the deadline, they're auto-skipped (or auto-locked if they have a tentative reservation). The Friday-Thursday block rule applies: reservations can start on any day but must end by the Thursday of the Fri-Thu block the start date falls in. Max 7 days per reservation.

**PHASE2_FCFS:** First come, first served for members who did NOT enter the draw. They get one reservation in the lottery period. If they cancel, they can rebook while Phase 2 is still open. The Fri-Thu block rule also applies here. Draw members cannot reserve lottery dates during this phase.

**PHASE3_REVERSE:** Same draw members pick again, in reverse order (last picker goes first). Same deadline and lock-in mechanics as Phase 1.

**OPEN_FCFS:** All remaining lottery dates open to everyone, no restrictions beyond overlap checking.

**CLOSED:** Season is archived.

## Key Business Rules

- **Max 7 days per reservation** (configurable via `MAX_RESERVATION_DAYS`).
- **Friday-Thursday block rule** (Phase 1 & 2 only): Reservation can start any day, but must end by Thursday of that week's Fri-Thu block.
- **No double-booking:** Overlap checking applies universally. Admin overrides also check for overlap (admin cannot double-book either, only create reservations that don't conflict).
- **Blocked dates:** Admin can block date ranges (e.g., Annual Meeting). These show in red/coral on the calendar and prevent anyone from booking those dates. Stored as `Reservation` records with `is_blocked=True` and a `block_label`.
- **Open booking dates** (outside lottery period) are always available to any member regardless of phase.
- **Lock-in flow:** During draft phases, reservations are tentative. Member must explicitly "Lock In" from their dashboard, which finalizes the pick and advances the draft to the next person.
- **Cancel anytime:** Members can cancel their own reservations at any time, from both the dashboard and calendar view.

## Database Models (app/models.py)

**Member:** id, name, email, phone, password_hash, role (regular/lifetime/admin), is_active_member. UserMixin for Flask-Login.

**Season:** id, year (unique), phase (string matching PhaseState constants), optional date fields for phase scheduling, phase1_pick_hours/phase3_pick_hours for deadline overrides. Has relationships to DraftOrder and Reservation.

**DraftOrder:** Links a member to a season with a position number. Tracks phase1_picked/phase3_picked booleans and pick deadlines. Unique constraint on (season_id, member_id).

**Reservation:** season_id, member_id, start_date, end_date, phase_made (which phase created it — or 'open_booking' or 'admin_override'), notes, is_cancelled, cancelled_at, is_blocked, block_label.

**AppSetting:** Simple key-value store for global settings.

## Core Engine (app/phase_engine.py — 396 lines)

The `PhaseEngine` class is the central business logic layer. Key methods:

- `get_active_season()` — Returns the non-closed season.
- `can_member_reserve(member, season)` — Combined check; open booking always allowed, lottery dates phase-dependent.
- `can_member_reserve_lottery(member, season)` — Phase-specific rules (is it your turn? are you in the draw? etc.).
- `validate_reservation(season, member, start, end)` — Enforces max days, season bounds, hunting season exclusion, block rule, blocked date checking, and overlap detection.
- `make_reservation(...)` — Creates reservation, sets `phase_made` based on whether dates are in lottery period.
- `lock_in_pick(season, member)` — Marks current picker as done, advances draft, sets next picker's deadline.
- `check_and_advance_deadlines(season)` — Called on every page load; auto-locks or skips overdue pickers.
- `get_reserved_dates(season)` — Returns reservation list with blocked info for calendar JS.
- `_get_fri_thu_block_end(date)` — Calculates the Thursday boundary for the block rule.

## Routes

**Auth** (`/login`, `/logout`, `/forgot-password`, `/reset-password/<token>`, `/settings`, `/change-password`): Standard Flask-Login auth with email-based password reset via Gmail SMTP.

**Main** (`/`, `/dashboard`): Dashboard shows season status, draft position, lock-in controls (when it's your turn), and reservation list with cancel buttons.

**Calendar** (`/calendar/`, `/calendar/reserve`, `/calendar/lock-in`, `/calendar/cancel/<id>`, `/calendar/opt-in`, plus two API endpoints for JSON data): Calendar view, reservation form with sticky date selector, lock-in route, cancel route (redirects to dashboard with phase-aware messaging).

**Admin** (`/admin/` + 20 sub-routes): Season management (create, advance phases, run draw, close, reset), member management (CRUD, password reset), reservation management (cancel, trade), admin reserve/block dates, and tools (deadline override, season reset with year-confirmation safeguard).

## Frontend

Single `calendar.js` (189 lines) renders a 12-month mini calendar. Color-coded by zone: lottery dates in amber, hunting in gray, open in default. Blocked dates render in red with the block label. Clicking an available date pre-fills the reservation form.

CSS is in `style.css` with CSS custom properties for theming. Responsive grid layout.

## Admin Tools

- **Pick Deadline Duration:** Override how many hours each member gets to pick (instead of the default days from config). Per-season setting stored on the Season model.
- **Season Reset:** Deletes all reservations and draft orders for a season, resets to SETUP. Requires typing the year number to confirm.
- **Admin Reserve / Block:** Create a reservation for any member bypassing phase rules, or block dates entirely.

## Configuration (config.py)

Key settings: `LOTTERY_START_MONTH/DAY` (Apr 1), `LOTTERY_END_MONTH/DAY` (Aug 7), `HUNTING_SEASON_MONTHS` ([8,9,10,11]), `MAX_RESERVATION_DAYS` (7), `PHASE1_PICK_DAYS` (5), `PHASE3_PICK_DAYS` (3), `PHASE2_DURATION_DAYS` (31), `MAX_MEMBERS` (30). Email via Gmail SMTP for password recovery.

## Deployment Notes

- Target: PythonAnywhere (WSGI via `wsgi.py`)
- Database: SQLite at `instance/silvies.db`
- `seed_admin.py` creates the initial admin account
- `seed_members.py` populates test members
- No migrations directory exists yet — use `flask db init` + `flask db migrate` when deploying updates to a production database that already has data
- **Important:** The `is_blocked` and `block_label` columns on the Reservation table were added after initial deployment. An `ALTER TABLE` or migration is needed for existing databases.

## Test Files

- `test_admin_tools.py` — Deadline overrides, season reset, tools page (8 tests)
- `test_lockin.py` — Lock-in flow, block rule, deadline auto-lock (19 tests)
- `test_all_changes.py` — Broader integration tests

## Development Notes

- **No background workers.** Deadline expiration is checked on every dashboard/calendar page load via `PhaseEngine.check_and_advance_deadlines()`.
- **Time travel feature was removed.** `app/utils.py` now contains simple `get_now()` and `get_today()` wrappers around `datetime.utcnow()`. These exist as a single point of control if a time abstraction is ever needed again.
- **`phase_made` field** on Reservation distinguishes how a reservation was created: the phase constant string (e.g., `'phase1_draft'`), `'open_booking'`, or `'admin_override'`. This drives flash message logic and phase permission checks.
- **AppSetting.get()** uses `query.filter_by().first()` instead of `db.session.get()` to avoid SQLAlchemy identity map caching issues after deletions.

## Completed Work Log

1. Project scaffold, models, auth, phase engine, calendar UI, admin dashboard, seed data
2. Year-round calendar (12 months, open booking outside lottery period)
3. Admin member management (add, edit, delete, password reset)
4. Calendar UX (end date auto-jump, reservation notes display)
5. Friday-Thursday block rule (Phase 1 & 2)
6. Lottery period expansion (Apr 1 – Aug 7)
7. Password recovery via email (Gmail SMTP)
8. Member settings page (email, phone, password)
9. Admin tools: time travel (later removed), pick deadline override, season reset
10. Lock-in flow for draft picks (tentative → lock in → advance)
11. Flash message fix (lock-in reminder only during draft phases for lottery dates)
12. Admin calendar override and date blocking
13. Member cancel/reschedule (cancel anytime, Phase 2 rebooking)
14. Time travel removal (kept deadline + reset tools)
15. Sticky reservation form while scrolling mini calendar
