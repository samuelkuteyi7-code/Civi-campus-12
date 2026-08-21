"""
Daily check-in streak - Section 15 Game Layer.

Pure logic kept separate from the endpoint so it's independently
testable: given the last check-in date and today's date, compute the
new streak count. No database access in this module.

Rules:
  - Same day as last check-in -> streak unchanged (already counted today)
  - Exactly one day after last check-in -> streak increments
  - Any bigger gap (or no previous check-in) -> streak resets to 1

Dates are plain date objects - callers decide the timezone (this app
uses UTC calendar days, see GameProfile.last_checkin_date).
"""

from datetime import date, timedelta


def next_streak(last_checkin: date | None, today: date, current_streak: int) -> int:
    if last_checkin is None:
        return 1
    if last_checkin == today:
        return current_streak
    if last_checkin == today - timedelta(days=1):
        return current_streak + 1
    return 1
