import random
from .game_state import clamp, add_news, apply_national_effects
from .mp_generator import lobby_mp, lobby_party, update_mp_vote_intention


LOBBY_ACTIONS = {
    "meet_mp": {
        "name": "Meet Individual MP",
        "icon": "🤝",
        "ap_cost": 1,
        "pc_cost": 1,
        "description": "One-on-one meeting with a specific MP. Strongly improves their support.",
        "requires_target": "mp"
    },
    "lobby_party": {
        "name": "Negotiate with Party",
        "icon": "🗳️",
        "ap_cost": 2,
        "pc_cost": 4,
        "description": "Sit-down with party leadership. Boost loyalty across all their MPs.",
        "requires_target": "party"
    },
    "press_conference": {
        "name": "Hold Press Conference",
        "icon": "🎤",
        "ap_cost": 1,
        "pc_cost": 2,
        "description": "Public address. Modest trust boost. Affects undecided voters and MPs.",
        "requires_target": None,
        "national_effect": {"public_trust": 3}
    },
    "national_address": {
        "name": "National TV Address",
        "icon": "📺",
        "ap_cost": 3,
        "pc_cost": 8,
        "description": "Address the nation. Big trust boost when timed well.",
        "requires_target": None,
        "national_effect": {"public_trust": 8, "government_stability": 4}
    },
    "lobby_committee": {
        "name": "Lobby Committee",
        "icon": "🏛️",
        "ap_cost": 2,
        "pc_cost": 3,
        "description": "Push committee members on a specific bill. Speeds up positive intentions.",
        "requires_target": "bill"
    },
    "media_offensive": {
        "name": "Media Offensive on Bill",
        "icon": "📢",
        "ap_cost": 2,
        "pc_cost": 5,
        "description": "Launch coordinated media push for a bill. Shifts public opinion and undecided MPs.",
        "requires_target": "bill"
    },
    "horse_trading": {
        "name": "Horse Trading",
        "icon": "🐴",
        "ap_cost": 2,
        "pc_cost": 6,
        "description": "Offer favors to opposition MPs to flip their vote on a bill.",
        "requires_target": "bill"
    },
    "anti_corruption_pledge": {
        "name": "Anti-Corruption Pledge",
        "icon": "🔍",
        "ap_cost": 1,
        "pc_cost": 3,
        "description": "Public commitment to fight corruption. Trust + EU relations boost.",
        "requires_target": None,
        "national_effect": {"corruption": -2, "public_trust": 3, "eu_relations": 2}
    },
    "rally_supporters": {
        "name": "Rally Party Supporters",
        "icon": "🚩",
        "ap_cost": 2,
        "pc_cost": 2,
        "description": "Energize the base. Boosts your own party's poll and loyalty.",
        "requires_target": None
    },
    "diplomatic_call": {
        "name": "EU Diplomatic Call",
        "icon": "🇪🇺",
        "ap_cost": 1,
        "pc_cost": 2,
        "description": "Call EU partners. Reinforces relations.",
        "requires_target": None,
        "national_effect": {"eu_relations": 3, "foreign_investment": 1}
    },
}


def execute_action(state, action_id, target=None, target_id=None):
    action = LOBBY_ACTIONS.get(action_id)
    if not action:
        return False, "Unknown action."

    cal = state["calendar"]
    if cal["action_points"] < action["ap_cost"]:
        return False, f"Not enough action points (need {action['ap_cost']})."

    n = state["national"]
    if n["political_capital"] < action["pc_cost"]:
        return False, f"Not enough political capital (need {action['pc_cost']})."

    cal["action_points"] -= action["ap_cost"]
    n["political_capital"] -= action["pc_cost"]

    log_msg = ""

    if "national_effect" in action:
        apply_national_effects(state, action["national_effect"])

    if action_id == "meet_mp" and target_id:
        ok = lobby_mp(state, target_id, intensity=2)
        mp = next((m for m in state["mps"] if m["id"] == target_id), None)
        if ok and mp:
            log_msg = f"Met with {mp['name']} ({mp['party']}). Relationship strengthened."
        else:
            log_msg = "Meeting completed."

    elif action_id == "lobby_party" and target_id:
        affected = lobby_party(state, target_id, intensity=3)
        party = state["parties"].get(target_id, {})
        log_msg = f"Negotiated with {party.get('name','party')}. {affected} MPs influenced."

    elif action_id == "lobby_committee" and target_id:
        bill = next((b for b in state.get("active_bills", []) if b["id"] == target_id), None)
        if bill:
            _lobby_committee(state, bill)
            log_msg = f"Lobbied committee on '{bill['title']}'. Some MPs shifted toward yes."

    elif action_id == "media_offensive" and target_id:
        bill = next((b for b in state.get("active_bills", []) if b["id"] == target_id), None)
        if bill:
            _media_offensive(state, bill)
            log_msg = f"Media offensive launched for '{bill['title']}'. Public opinion shifted."

    elif action_id == "horse_trading" and target_id:
        bill = next((b for b in state.get("active_bills", []) if b["id"] == target_id), None)
        if bill:
            flipped = _horse_trade(state, bill)
            log_msg = f"Horse trading on '{bill['title']}'. {flipped} opposition MPs swayed."

    elif action_id == "rally_supporters":
        player_id = state["player_party"]
        state["parties"][player_id]["poll"] = min(60, state["parties"][player_id]["poll"] + 0.4)
        for mp in state["mps"]:
            if mp["party"] == player_id:
                mp["loyalty"] = min(100, mp["loyalty"] + 3)
        log_msg = "Rally energized DA base. Party loyalty up."

    elif action_id == "press_conference":
        log_msg = "Press conference held. Trust nudged upward."

    elif action_id == "national_address":
        log_msg = "Major TV address delivered. Significant trust boost."

    elif action_id == "anti_corruption_pledge":
        log_msg = "Anti-corruption pledge announced."

    elif action_id == "diplomatic_call":
        log_msg = "Diplomatic call completed. EU relations improved."

    state.setdefault("history", {}).setdefault("lobbying_log", []).append({
        "turn": state["turn"],
        "date": state["calendar"]["date"],
        "action": action_id,
        "target_id": target_id,
        "log": log_msg
    })

    add_news(state, action.get("icon", "📋"), log_msg, "political")
    state["_toast_msg"] = f"{action.get('icon','✓')} {log_msg}"
    return True, log_msg


def _lobby_committee(state, bill):
    coalition = state["parliament"]["coalition"]
    candidates = [m for m in state["mps"]
                   if m["party"] in coalition and
                   m["vote_intentions"].get(bill["id"]) in ("undecided", "abstain")]
    candidates.sort(key=lambda m: -m["persuadability"])
    influenced = candidates[:8]
    for mp in influenced:
        mp["loyalty"] = min(100, mp["loyalty"] + 3)
        mp["lobbying_received"] = mp.get("lobbying_received", 0) + 1
        mp["vote_intentions"][bill["id"]] = update_mp_vote_intention(mp, bill, state)


def _media_offensive(state, bill):
    state["national"]["public_trust"] = min(100, state["national"]["public_trust"] + 2)
    swayable = [m for m in state["mps"]
                 if m["vote_intentions"].get(bill["id"]) in ("undecided", "abstain")]
    swayable.sort(key=lambda m: -m["media_profile"])
    for mp in swayable[:12]:
        mp["lobbying_received"] = mp.get("lobbying_received", 0) + 0.7
        mp["vote_intentions"][bill["id"]] = update_mp_vote_intention(mp, bill, state)


def _horse_trade(state, bill):
    coalition = state["parliament"]["coalition"]
    opposition_mps = [m for m in state["mps"]
                       if m["party"] not in coalition and
                       m["vote_intentions"].get(bill["id"]) in ("undecided", "no", "abstain")]
    flippable = [m for m in opposition_mps if m["persuadability"] > 50 and m["corruption_risk"] > 40]
    flippable.sort(key=lambda m: -(m["persuadability"] + m["corruption_risk"]))
    flipped = 0
    for mp in flippable[:5]:
        mp["personal_relationship"] = min(100, mp["personal_relationship"] + 12)
        mp["lobbying_received"] = mp.get("lobbying_received", 0) + 2
        new_intention = update_mp_vote_intention(mp, bill, state)
        if new_intention == "yes":
            flipped += 1
        mp["vote_intentions"][bill["id"]] = new_intention

    state["national"]["corruption"] = min(100, state["national"]["corruption"] + 1)
    return flipped
