import json
import random
import os
from .game_state import clamp, add_news

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load_events():
    with open(os.path.join(DATA_DIR, "events.json"), encoding="utf-8") as f:
        return json.load(f)


def check_and_fire_events(state):
    if len(state["active_events"]) >= 2:
        return

    events = _load_events()
    seen = set(state["events_seen"])
    n = state["national"]
    diff = state["meta"]["diff_mod"]

    eligible = []
    for ev in events:
        if ev["id"] in seen and not ev.get("repeatable", False):
            continue

        if not _check_conditions(ev.get("trigger_conditions", {}), n):
            continue

        base_prob = ev.get("probability", 0.05) * diff
        turn = state.get("turn", 1)
        if turn < 3 and ev.get("severity", 1) >= 4:
            base_prob *= 0.3

        eligible.append((ev, base_prob))

    random.shuffle(eligible)
    slots = 2 - len(state["active_events"])
    for ev, prob in eligible[:10]:
        if slots <= 0:
            break
        if random.random() < prob:
            state["active_events"].append(_prepare_event(ev))
            if not ev.get("repeatable", False):
                state["events_seen"].append(ev["id"])
            slots -= 1


def _check_conditions(conditions, national):
    for key, (op, threshold) in conditions.items():
        if key not in national:
            continue
        val = national[key]
        if op == ">" and not (val > threshold):
            return False
        if op == "<" and not (val < threshold):
            return False
        if op == ">=" and not (val >= threshold):
            return False
        if op == "<=" and not (val <= threshold):
            return False
    return True


def _prepare_event(ev):
    return {
        "id": ev["id"],
        "title": ev["title"],
        "description": ev["description"],
        "type": ev["type"],
        "severity": ev.get("severity", 2),
        "choices": ev["choices"],
        "resolved": False,
        "chosen": None
    }


def resolve_event(state, event_id, choice_id):
    event = next((e for e in state["active_events"] if e["id"] == event_id), None)
    if not event:
        return

    choice = next((c for c in event["choices"] if c["id"] == choice_id), None)
    if not choice:
        return

    effects = choice.get("effects", {})

    from .game_state import (apply_national_effects, apply_voter_effects,
                              apply_coalition_effects, apply_region_effects,
                              apply_national_effects)

    if "national" in effects:
        apply_national_effects(state, effects["national"])

    if "voter_effects" in effects:
        apply_voter_effects(state, effects["voter_effects"])

    if "coalition_effects" in effects:
        apply_coalition_effects(state, effects["coalition_effects"])

    if "regions" in effects:
        apply_region_effects(state, effects["regions"])

    if "parties" in effects:
        for party_id, peffects in effects["parties"].items():
            if party_id in state["parties"]:
                p = state["parties"][party_id]
                for k, v in peffects.items():
                    if k == "seats":
                        p["seats"] = max(0, p["seats"] + v)
                    elif k == "poll":
                        p["poll"] = round(clamp(p["poll"] + v, 1, 60), 1)

    if effects.get("national", {}).get("election_early"):
        state["election_triggered"] = True
        months_to_election = (state["election_due"]["year"] - state["date"]["year"]) * 12 + \
                              (state["election_due"]["month"] - state["date"]["month"])
        if months_to_election > 3:
            state["election_due"] = {
                "year": state["date"]["year"],
                "month": min(12, state["date"]["month"] + 2)
            }

    news_text = effects.get("news", f"Event resolved: {event['title']}")
    icons = {"economic": "💰", "political": "🏛️", "corruption": "🔍",
             "social": "🗣️", "security": "🚔", "environmental": "🌿",
             "foreign_policy": "🌍", "media": "📺"}
    icon = icons.get(event["type"], "📰")
    add_news(state, icon, news_text, event["type"])

    state["history"]["decisions"].append({
        "turn": state["turn"],
        "event_id": event_id,
        "event_title": event["title"],
        "choice_id": choice_id,
        "choice_text": choice["text"]
    })

    state["active_events"] = [e for e in state["active_events"] if e["id"] != event_id]


def generate_ai_headlines(state):
    n = state["national"]
    t = state["turn"]

    possible_headlines = []

    if n["social_tension"] > 65:
        possible_headlines.append(
            ("🗣️", "Opposition leader demands PM resign over 'leadership failure'", "political")
        )
    if n["corruption"] > 70:
        possible_headlines.append(
            ("🔍", "NGO releases corruption risk ranking — Pustinyakovo scores poorly", "corruption")
        )
    if n["eu_relations"] < 55:
        possible_headlines.append(
            ("🌍", "EU Parliament passes resolution criticizing Pustinyakovo democratic backsliding", "foreign")
        )
    if n["eu_relations"] > 75:
        possible_headlines.append(
            ("🌍", "EU praises Pustinyakovo reform progress. New funding tranche approved.", "foreign")
        )
    if state["parties"]["national_front"]["poll"] > 25:
        possible_headlines.append(
            ("🔴", "National Front poll surge alarms coalition. Dokov: 'We will win the next election.'", "political")
        )
    if n["public_trust"] < 35:
        possible_headlines.append(
            ("📊", "Public trust in government reaches new low, poll shows. Coalition scrambles.", "political")
        )
    if n["inflation"] > 9:
        possible_headlines.append(
            ("💰", "Union leaders hold emergency meeting over inflation crisis. Strike warned.", "economic")
        )

    generic_headlines = [
        ("🏛️", "Parliament sits in heated session. MPs argue over budget priorities.", "political"),
        ("📺", "State broadcaster accused of government bias by press freedom group.", "media"),
        ("🗳️", "New poll: undecided voters key bloc ahead of next election.", "political"),
        ("🌍", "Foreign ambassadors meet PM for routine coordination session.", "foreign"),
        ("💰", "Chamber of Commerce warns of challenging business conditions.", "economic"),
        ("🔍", "Anti-corruption watchdog releases annual report with mixed findings.", "corruption"),
    ]

    if possible_headlines and random.random() < 0.6:
        return random.choice(possible_headlines)
    if random.random() < 0.4:
        return random.choice(generic_headlines)
    return None
