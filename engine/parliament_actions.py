"""Parliamentary procedural actions — special moves outside normal bill flow.
Things like filibusters, no-confidence motions, inquiries, coalition retreats.
"""
import random
from .game_state import clamp, add_news, apply_national_effects


PROCEDURAL_ACTIONS = {
    "coalition_retreat": {
        "id": "coalition_retreat",
        "name": "Coalition Retreat",
        "icon": "🏞️",
        "ap_cost": 3,
        "pc_cost": 6,
        "description": "Two-day retreat with all coalition leaders. Major loyalty + stability boost.",
        "category": "coalition",
        "effects": {
            "national": {"government_stability": 8, "coalition_stability": 12},
            "coalition_loyalty_all": 12,
            "news": "Coalition leaders retreat to Boyana for two days of unity talks. Public sees a coordinated team."
        }
    },
    "speaker_meeting": {
        "id": "speaker_meeting",
        "name": "Meet the Speaker",
        "icon": "👨‍⚖️",
        "ap_cost": 1,
        "pc_cost": 3,
        "description": "Negotiate parliament's agenda with the Speaker. Speeds up your active bills.",
        "category": "agenda",
        "effects": {
            "national": {"government_stability": 3},
            "speed_up_bills": True,
            "news": "PM meets with Speaker Petrov to set parliamentary priorities. Active bills accelerated."
        }
    },
    "filibuster": {
        "id": "filibuster",
        "name": "Filibuster Opposition",
        "icon": "🛑",
        "ap_cost": 2,
        "pc_cost": 4,
        "description": "Use procedural delays to stall opposition motions. Damages opposition party polls.",
        "category": "obstruction",
        "effects": {
            "opposition_poll_drop": 1.0,
            "national": {"democratic_quality": -2, "government_stability": -2},
            "news": "Coalition MPs deploy procedural filibuster, delaying opposition agenda. Opposition cries foul."
        }
    },
    "parliamentary_inquiry": {
        "id": "parliamentary_inquiry",
        "name": "Parliamentary Inquiry",
        "icon": "🔍",
        "ap_cost": 2,
        "pc_cost": 5,
        "description": "Open a parliamentary investigation into opposition wrongdoing. Slow but damaging.",
        "category": "obstruction",
        "effects": {
            "opposition_poll_drop": 1.5,
            "national": {"corruption": -2, "democratic_quality": -3, "rule_of_law": -1},
            "news": "Parliamentary inquiry opened into opposition party finances. Months of bad headlines ahead for them."
        }
    },
    "no_confidence_minister": {
        "id": "no_confidence_minister",
        "name": "Replace a Minister",
        "icon": "🪑",
        "ap_cost": 2,
        "pc_cost": 8,
        "description": "Force out a controversial minister. Boosts trust if a scandal-prone one is replaced.",
        "category": "cabinet",
        "effects": {
            "national": {"public_trust": 5, "corruption": -4, "government_stability": -3},
            "news": "PM dismisses a controversial minister. Public sees decisive leadership; cabinet morale shaken."
        }
    },
    "cabinet_reshuffle": {
        "id": "cabinet_reshuffle",
        "name": "Cabinet Reshuffle",
        "icon": "🔄",
        "ap_cost": 3,
        "pc_cost": 12,
        "description": "Major cabinet shake-up. Big stability + loyalty boost, but messy in the press.",
        "category": "cabinet",
        "effects": {
            "national": {"government_stability": 10, "public_trust": 4, "coalition_stability": 8},
            "coalition_loyalty_all": 6,
            "news": "Sweeping cabinet reshuffle announced. New faces in Finance, Interior, Health. Coalition partners rewarded with new ministries."
        }
    },
    "emergency_session": {
        "id": "emergency_session",
        "name": "Emergency Session",
        "icon": "🚨",
        "ap_cost": 2,
        "pc_cost": 4,
        "description": "Call emergency parliamentary session to address current crises. Boosts your authority.",
        "category": "agenda",
        "effects": {
            "national": {"government_stability": 6, "public_trust": 3, "social_tension": -5},
            "news": "PM calls emergency session of parliament. Government projects calm authority during crisis."
        }
    },
    "appeal_to_president": {
        "id": "appeal_to_president",
        "name": "Appeal to President",
        "icon": "🏛️",
        "ap_cost": 1,
        "pc_cost": 3,
        "description": "Request presidential intervention on a contested issue. Modest authority boost.",
        "category": "agenda",
        "effects": {
            "national": {"government_stability": 4, "rule_of_law": 2},
            "news": "PM meets with President to request mediation on parliamentary disputes."
        }
    },
    "address_to_nation": {
        "id": "address_to_nation",
        "name": "Address to the Nation",
        "icon": "📜",
        "ap_cost": 3,
        "pc_cost": 7,
        "description": "Major prepared address from the parliamentary chamber. Trust + stability surge.",
        "category": "media",
        "effects": {
            "national": {"public_trust": 9, "government_stability": 5, "social_tension": -6},
            "news": "PM Markova addresses joint session of parliament. Powerful speech praised across most outlets."
        }
    },
    "anti_corruption_blitz": {
        "id": "anti_corruption_blitz",
        "name": "Anti-Corruption Blitz",
        "icon": "🚔",
        "ap_cost": 3,
        "pc_cost": 9,
        "description": "Surprise raids and arrests. Big drop in corruption + trust boost, but elite blowback.",
        "category": "reform",
        "effects": {
            "national": {"corruption": -10, "public_trust": 8, "rule_of_law": 5, "elite_conflict": 12, "foreign_investment": -3},
            "news": "Coordinated anti-corruption raids hit business and political elites. Markets jittery, public ecstatic."
        }
    },
}


def execute_procedural(state, action_id):
    action = PROCEDURAL_ACTIONS.get(action_id)
    if not action:
        return False, "Unknown action."

    cal = state["calendar"]
    if cal["action_points"] < action["ap_cost"]:
        return False, f"Need {action['ap_cost']} AP."
    if state["national"]["political_capital"] < action["pc_cost"]:
        return False, f"Need {action['pc_cost']} PC."

    cal["action_points"] -= action["ap_cost"]
    state["national"]["political_capital"] -= action["pc_cost"]

    effects = action["effects"]
    if "national" in effects:
        apply_national_effects(state, effects["national"])

    if effects.get("coalition_loyalty_all"):
        boost = effects["coalition_loyalty_all"]
        for pid in state["parliament"]["coalition"]:
            if pid != state["player_party"] and pid in state["parties"]:
                p = state["parties"][pid]
                p["coalition_loyalty"] = int(clamp(p.get("coalition_loyalty", 65) + boost))

    if effects.get("opposition_poll_drop"):
        drop = effects["opposition_poll_drop"]
        opposition = [pid for pid in state["parties"]
                       if pid not in state["parliament"]["coalition"]]
        if opposition:
            target = random.choice(opposition)
            tp = state["parties"][target]
            tp["poll"] = round(max(2.0, tp["poll"] - drop), 1)

    if effects.get("speed_up_bills"):
        for bill in state.get("active_bills", []):
            bill["stage_day"] = bill.get("stage_day", 0) + 1

    add_news(state, action["icon"], effects.get("news", action["name"]), "political")
    state["_toast_msg"] = f"{action['icon']} {action['name']} executed"
    return True, action["name"]
