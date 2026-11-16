"""Small, independently testable tools exposed to Voxa."""

from datetime import datetime


def format_local_time() -> str:
    """Format the current local date and time, including the timezone."""
    now = datetime.now().astimezone()
    return now.strftime("%A, %B %d, %Y at %I:%M %p %Z")
