import json
import copy
import random
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load(filename):
    with open(os.path.join(DATA_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


def initialize_game(scenario="fragmented_republic", difficulty="normal"):
    parties_data = _load("parties.json")
    regions_data = _load("regions.json")
    voter_groups = _load("voter_groups.json")
    ministers_data = _load("ministers.json")

    diff_mod = {"easy": 0.7, "normal": 1.0, "hard": 1.4, "nightmare": 1.8}.get(difficulty, 1.0)

    state = {
        "meta": {
            "scenario": scenario,
            "difficulty": difficulty,
            "diff_mod": diff_mod,
            "game_version": "2.0"
        },

        "calendar": {
            "date": {"year": 2024, "month": 3, "day": 4},
            "action_points": 4,
            "max_action_points": 4,
            "scheduled_actions": [],
            "weekly_action_history": []
        },
        "turn": 1,

        "phase": "governance",
        "election_due": {"year": 2028, "month": 3, "day": 1},
        "election_triggered": False,
        "campaign_active": False,
        "player_party": "democratic_alliance",
        "player_role": "prime_minister",

        "national": {
            "government_stability": 62,
            "public_trust": 44,
            "democratic_quality": 65,
            "corruption": 58,
            "rule_of_law": 52,
            "media_freedom": 60,
            "civil_rights": 63,
            "inflation": 7.8,
            "unemployment": 13.2,
            "gdp_growth": 1.8,
            "public_debt": 68.0,
            "budget_deficit": 4.2,
            "social_tension": 58,
            "elite_conflict": 42,
            "security_risk": 32,
            "military_readiness": 45,
            "energy_security": 52,
            "eu_relations": 65,
            "foreign_investment": 42,
            "political_capital": 55,
            "coalition_stability": 62,
            "party_unity": 60,
            "faction_tension": 38,
            "ethnic_tension": 48,
            "business_confidence": 48
        },

        "parties": copy.deepcopy(parties_data),
        "regions": copy.deepcopy(regions_data),

        "parliament": {
            "total_seats": 240,
            "majority": 121,
            "coalition": ["democratic_alliance", "social_democrats", "green_future", "liberal_democrats"],
            "coalition_seats": 125,
            "speaker": "Georgi Petrov (Independent)",
            "confidence": 62,
            "passed_laws": [],
            "failed_bills": [],
        },

        "cabinet": copy.deepcopy(ministers_data),
        "active_events": [],
        "events_seen": [],
        "news": [],

        "active_bills": [],
        "implementing_laws": [],

        "election_campaign": None,

        "history": {
            "events": [],
            "decisions": [],
            "laws_passed": [],
            "election_results": [],
            "approval_history": [],
            "economic_history": [],
            "lobbying_log": []
        },

        "voter_groups": copy.deepcopy(voter_groups),

        "game_over": False,
        "game_over_reason": None,
        "victory": False,
        "final_scores": None
    }

    _set_initial_party_seats(state)

    from .mp_generator import generate_mps
    state["mps"] = generate_mps(state["parties"], state["regions"], 240)

    _generate_opening_news(state)
    return state


def _set_initial_party_seats(state):
    seats = {
        "democratic_alliance": 90,
        "citizens_union": 68,
        "national_front": 47,
        "social_democrats": 20,
        "green_future": 10,
        "liberal_democrats": 5
    }
    for pid, s in seats.items():
        if pid in state["parties"]:
            state["parties"][pid]["seats"] = s
    state["parliament"]["coalition_seats"] = sum(
        seats[p] for p in state["parliament"]["coalition"]
    )


def _generate_opening_news(state):
    opening_news = [
        ("🏛️", "DA-led coalition sworn in. Markova becomes Prime Minister. 125-seat working majority.", "political"),
        ("💰", "Finance Ministry: budget deficit at 4.2% GDP, above EU targets. Tough months ahead.", "economic"),
        ("📊", "Latest poll: DA 34%, CU 30%, NF rising to 22%. Three coalition partners trail thresholds.", "political"),
        ("🌍", "EU Commissioner urges new government to accelerate judicial reform. 'Clock is ticking.'", "foreign"),
        ("⚡", "Energy prices 40% above last year. Households struggle. Opposition demands action.", "economic"),
    ]
    for icon, text, ntype in opening_news:
        state["news"].append({
            "turn": 0,
            "month": "March 2024",
            "day_str": "Mon 4 Mar 2024",
            "icon": icon,
            "text": text,
            "type": ntype
        })


def get_date_string(state, full=False):
    months = ["", "January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    d = state["calendar"]["date"]
    if full:
        from .calendar_engine import format_date
        return format_date(d, full=True)
    return f"{d['day']} {months[d['month']]} {d['year']}"


def get_days_to_election(state):
    from .calendar_engine import days_between
    return days_between(state["calendar"]["date"], state["election_due"])


def get_coalition_seat_total(state):
    return sum(
        state["parties"][p]["seats"]
        for p in state["parliament"]["coalition"]
        if p in state["parties"]
    )


def clamp(value, lo=0, hi=100):
    return max(lo, min(hi, value))


def apply_national_effects(state, effects_dict):
    if not effects_dict:
        return
    n = state["national"]
    for key, delta in effects_dict.items():
        if key in n:
            if key in ("inflation", "gdp_growth", "unemployment", "public_debt", "budget_deficit"):
                n[key] = round(n[key] + delta, 2)
            else:
                n[key] = int(clamp(n[key] + delta))


def apply_voter_effects(state, voter_effects):
    if not voter_effects:
        return
    party_affinity_changes = {}
    for group_id, delta in voter_effects.items():
        if group_id not in state["voter_groups"]:
            continue
        group = state["voter_groups"][group_id]
        size_weight = group["size"] / 100.0
        for party_id, affinity in group.get("party_affinity", {}).items():
            party_affinity_changes[party_id] = party_affinity_changes.get(party_id, 0) + delta * affinity * size_weight * 0.15

    for party_id, change in party_affinity_changes.items():
        if party_id in state["parties"]:
            current = state["parties"][party_id]["poll"]
            state["parties"][party_id]["poll"] = round(clamp(current + change, 1, 60), 1)
    _normalize_polls(state)


def _normalize_polls(state):
    total = sum(p["poll"] for p in state["parties"].values())
    if total <= 0:
        return
    for party in state["parties"].values():
        party["poll"] = round((party["poll"] / total) * 100, 1)


def apply_coalition_effects(state, coalition_effects):
    if not coalition_effects:
        return
    for party_id, effects in coalition_effects.items():
        if party_id in state["parties"]:
            p = state["parties"][party_id]
            if "loyalty" in effects:
                current = p.get("coalition_loyalty", 65)
                p["coalition_loyalty"] = int(clamp(current + effects["loyalty"]))
            if "tension" in effects:
                current = p.get("faction_tension", 40)
                p["faction_tension"] = int(clamp(current + effects["tension"]))


def apply_region_effects(state, region_effects):
    if not region_effects:
        return
    for region_id, effects in region_effects.items():
        if region_id not in state["regions"]:
            continue
        region = state["regions"][region_id]
        for key, val in effects.items():
            if key.startswith("party_support_"):
                party_short = key.replace("party_support_", "")
                party_map = {"da": "democratic_alliance", "cu": "citizens_union",
                             "nf": "national_front", "sd": "social_democrats",
                             "gf": "green_future", "ld": "liberal_democrats"}
                party_id = party_map.get(party_short)
                if party_id and "party_support" in region["politics"]:
                    current = region["politics"]["party_support"].get(party_id, 0)
                    region["politics"]["party_support"][party_id] = int(clamp(current + val))
            elif key in region.get("economy", {}):
                region["economy"][key] = round(region["economy"][key] + val, 1)
            elif key in region.get("politics", {}):
                current = region["politics"][key]
                region["politics"][key] = int(clamp(current + val))


def add_news(state, icon, text, ntype="general"):
    d = state["calendar"]["date"]
    months = ["", "January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    state["news"].insert(0, {
        "turn": state["turn"],
        "day_str": f"{d['day']} {months[d['month']][:3]} {d['year']}",
        "icon": icon,
        "text": text,
        "type": ntype
    })
    if len(state["news"]) > 80:
        state["news"] = state["news"][:80]


def check_game_over(state):
    n = state["national"]

    if n["government_stability"] <= 5:
        state["game_over"] = True
        state["game_over_reason"] = "coalition_collapse"
        return True
    if n["public_trust"] <= 5:
        state["game_over"] = True
        state["game_over_reason"] = "total_loss_of_trust"
        return True
    if n["public_debt"] >= 130:
        state["game_over"] = True
        state["game_over_reason"] = "debt_crisis"
        return True
    if n["social_tension"] >= 95:
        state["game_over"] = True
        state["game_over_reason"] = "revolution"
        return True

    coalition_seats = get_coalition_seat_total(state)
    if coalition_seats < state["parliament"]["majority"]:
        state["national"]["government_stability"] = max(
            0, state["national"]["government_stability"] - 5
        )

    return False
