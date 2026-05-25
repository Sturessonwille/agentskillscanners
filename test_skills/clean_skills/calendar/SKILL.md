---
name: calendar
description: "Calendar and scheduling management. Use this skill when the user needs to create, view, update, or manage calendar events, appointments, meetings, or schedule-related tasks."
---

# Calendar Management Skill

You are a calendar and scheduling assistant. Help users create, view, modify, and manage calendar events efficiently.

## When to Use This Skill

- Create, update, or delete calendar events
- Check availability or schedule conflicts
- Export or import calendar data (ICS/iCal)
- Handle recurring event patterns
- Deal with timezones in scheduling

## ICS File Format Basics

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Your Organization//Your App//EN
BEGIN:VEVENT
UID:unique-id@yourdomain.com
DTSTAMP:20250120T120000Z
DTSTART:20250125T140000Z
DTEND:20250125T150000Z
SUMMARY:Team Meeting
DESCRIPTION:Weekly team sync
LOCATION:Conference Room A
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR
```

## Recurrence Rules (RRULE)

```
RRULE:FREQ=DAILY;COUNT=10
RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR
RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE
RRULE:FREQ=MONTHLY;BYMONTHDAY=1,15
RRULE:FREQ=MONTHLY;BYDAY=1MO
```

## Working with Python

```python
from icalendar import Calendar, Event
from datetime import datetime
import pytz

cal = Calendar()
cal.add('prodid', '-//My Organization//My App//EN')
cal.add('version', '2.0')

event = Event()
event.add('summary', 'Team Meeting')
event.add('dtstart', datetime(2025, 1, 25, 14, 0, 0, tzinfo=pytz.UTC))
event.add('dtend', datetime(2025, 1, 25, 15, 0, 0, tzinfo=pytz.UTC))
event.add('uid', f'{datetime.now().timestamp()}@example.com')

cal.add_component(event)

with open('meeting.ics', 'wb') as f:
    f.write(cal.to_ical())
```

## Operational Guidelines

1. Always include timezone information for events with specific times
2. Generate unique UIDs for each event to prevent conflicts
3. Set DTSTAMP to the current timestamp when creating events
4. Use DTEND or DURATION but not both for event duration
5. Validate ICS files before distribution or import
6. Handle recurring events with proper RRULE syntax
7. Set appropriate reminder triggers based on event importance
8. Use SEQUENCE for updates (increment on each modification)
