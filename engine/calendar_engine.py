from datetime import date, timedelta
import random


DAYS_PER_MONTH = {
    1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
    7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
}

MONTHS = ["", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def to_date_obj(d):
    return date(d["year"], d["month"], d["day"])


def from_date_obj(d):
    return {"year": d.year, "month": d.month, "day": d.day}


def advance_day(date_dict, days=1):
    d = to_date_obj(date_dict)
    d += timedelta(days=days)
    return from_date_obj(d)


def get_weekday(date_dict):
    d = to_date_obj(date_dict)
    return WEEKDAYS[d.weekday()]


def is_parliament_day(date_dict):
    return get_weekday(date_dict) in ("Tue", "Wed", "Thu")


def is_weekend(date_dict):
    return get_weekday(date_dict) in ("Sat", "Sun")


def format_date(date_dict, full=True):
    if full:
        return f"{get_weekday(date_dict)} {date_dict['day']} {MONTHS[date_dict['month']]} {date_dict['year']}"
    return f"{date_dict['day']} {MONTHS[date_dict['month']][:3]}"


def days_between(d1, d2):
    return (to_date_obj(d2) - to_date_obj(d1)).days


def get_upcoming_calendar(state, days=14):
    current = state["calendar"]["date"]
    items = []

    for i in range(days):
        d = advance_day(current, i)
        weekday = get_weekday(d)
        is_pd = is_parliament_day(d)
        is_we = is_weekend(d)

        day_items = []

        for bill in state.get("active_bills", []):
            for stage_event in bill.get("scheduled_events", []):
                if (stage_event["date"]["year"] == d["year"] and
                    stage_event["date"]["month"] == d["month"] and
                    stage_event["date"]["day"] == d["day"]):
                    day_items.append({
                        "type": stage_event["type"],
                        "label": stage_event["label"],
                        "bill_id": bill["id"],
                        "bill_title": bill["title"],
                        "icon": stage_event.get("icon", "📌")
                    })

        for sched in state["calendar"].get("scheduled_actions", []):
            if (sched["date"]["year"] == d["year"] and
                sched["date"]["month"] == d["month"] and
                sched["date"]["day"] == d["day"]):
                day_items.append({
                    "type": "scheduled_action",
                    "label": sched["action"],
                    "icon": "📅"
                })

        items.append({
            "date": d,
            "weekday": weekday,
            "is_parliament_day": is_pd,
            "is_weekend": is_we,
            "events": day_items,
            "is_today": (i == 0)
        })

    return items


def schedule_action(state, days_ahead, action_label):
    target_date = advance_day(state["calendar"]["date"], days_ahead)
    state["calendar"].setdefault("scheduled_actions", []).append({
        "date": target_date,
        "action": action_label
    })
