from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.core.security import get_calendar_url


class CalendarService:
    """Read-only Google Calendar integration through its private iCal feed."""

    allowed_hosts = {"calendar.google.com", "www.google.com"}

    def upcoming(self, days: int = 7) -> list[dict]:
        url = get_calendar_url()
        if not url:
            return []
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise ValueError("Calendar URL must be a Google Calendar HTTPS iCal address")
        request = Request(url, headers={"User-Agent": "SecondBrain/0.2"})
        with urlopen(request, timeout=8) as response:  # noqa: S310 - host is allow-listed above
            text = response.read(3_000_000).decode("utf-8", errors="replace")
        return self.parse(text, days)

    @classmethod
    def parse(cls, text: str, days: int = 7, now: datetime | None = None) -> list[dict]:
        # RFC 5545 lines may be folded with a leading space or tab.
        text = re.sub(r"\r?\n[ \t]", "", text)
        now = now or datetime.now().astimezone()
        end = now + timedelta(days=days)
        events: list[dict] = []
        for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", text, flags=re.S):
            values: dict[str, str] = {}
            for line in block.replace("\r", "").split("\n"):
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                values[key] = cls._unescape(value)
            start_key = next((key for key in values if key.startswith("DTSTART")), None)
            if not start_key:
                continue
            start, all_day = cls._parse_date(values[start_key], now.tzinfo)
            if start is None or start < now - timedelta(days=1) or start > end:
                continue
            events.append({
                "id": values.get("UID", f"{start.isoformat()}-{values.get('SUMMARY', '')}"),
                "title": values.get("SUMMARY", "Untitled event"),
                "start": start.isoformat(),
                "all_day": all_day,
                "location": values.get("LOCATION", ""),
                "description": values.get("DESCRIPTION", "")[:500],
            })
        return sorted(events, key=lambda item: item["start"])

    @staticmethod
    def _parse_date(value: str, local_tz) -> tuple[datetime | None, bool]:
        try:
            if len(value) == 8:
                parsed = datetime.combine(date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:] }"), datetime.min.time())
                return parsed.replace(tzinfo=local_tz), True
            if value.endswith("Z"):
                parsed = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
                return parsed.astimezone(local_tz), False
            parsed = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
            return parsed.replace(tzinfo=local_tz), False
        except (ValueError, TypeError):
            return None, False

    @staticmethod
    def _unescape(value: str) -> str:
        return value.replace("\\n", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")

