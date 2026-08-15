#!/usr/bin/env python3
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "schedule.json"
OUTPUTS = [ROOT / "calendar.ics", ROOT / "public" / "calendar.ics"]
ALLOWED_TYPES = {"DT", "K", "TR", "TS", "LL", "GEL", "DTN"}

def ics_escape(value: str) -> str:
    return (value.replace("\\", "\\\\").replace(";", "\\;")
                 .replace(",", "\\,").replace("\n", "\\n"))

def event_times(shift):
    start = datetime.strptime(f"{shift['date']} {shift['start']}", "%Y-%m-%d %H:%M")
    end = datetime.strptime(f"{shift['date']} {shift['end']}", "%Y-%m-%d %H:%M")
    if end <= start:
        end += timedelta(days=1)
    return start, end

def stable_uid(shift, location):
    raw = "|".join([shift["type"], shift["date"], shift["start"], shift["end"], location, shift.get("description", "")])
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{digest}@my-work-calendar"

def build_calendar(data):
    calendar = data["calendar"]
    location = calendar["location"]
    tzid = calendar.get("timezone", "Europe/Moscow")
    normalized, seen = [], set()
    for shift in data.get("shifts", []):
        if shift["type"] not in ALLOWED_TYPES:
            raise ValueError(f"Unknown shift type: {shift['type']}")
        start, end = event_times(shift)
        key = (shift["type"], start, end, location, shift.get("description", ""))
        if key in seen:
            continue
        seen.add(key)
        normalized.append((shift, start, end))
    normalized.sort(key=lambda item: item[1])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Dmitry Work Calendar//RU",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH", f"X-WR-CALNAME:{ics_escape(calendar['name'])}",
        f"X-WR-TIMEZONE:{ics_escape(tzid)}"
    ]
    for shift, start, end in normalized:
        lines += [
            "BEGIN:VEVENT", f"UID:{stable_uid(shift, location)}", f"DTSTAMP:{stamp}",
            f"DTSTART;TZID={tzid}:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID={tzid}:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{ics_escape(shift['type'])}", f"LOCATION:{ics_escape(location)}"
        ]
        if shift.get("description"):
            lines.append(f"DESCRIPTION:{ics_escape(shift['description'])}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

def main():
    data = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    ics = build_calendar(data)
    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(ics, encoding="utf-8")
    print(f"Generated {len(data.get('shifts', []))} schedule entries.")

if __name__ == "__main__":
    main()
