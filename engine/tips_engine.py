"""Contextual tips system. Shows helpful hints based on the current game state.
Tips are triggered by conditions (low trust, bill stuck, coalition wavering, etc.)
and rate-limited so the same advice doesn't appear too often.
"""
import random


TIPS = [
    {
        "id": "trust_critical",
        "icon": "🚨",
        "title": "Public trust collapsing",
        "text": "Trust below 30%. Try a 📺 National TV Address for a big boost, pass a popular law (pensions or healthcare), or hold a 🎤 Press Conference.",
        "priority": 10,
        "trigger": lambda s: s["national"]["public_trust"] < 30,
    },
    {
        "id": "trust_low",
        "icon": "💡",
        "title": "Trust is slipping",
        "text": "Public trust is low. Anti-corruption pledges and EU diplomatic calls help slowly. Avoid austerity bills for now.",
        "priority": 6,
        "trigger": lambda s: 30 <= s["national"]["public_trust"] < 42,
    },
    {
        "id": "coalition_wavering",
        "icon": "⚠️",
        "title": "Coalition partner wavering",
        "text": "A coalition party has loyalty below 50%. Use 🗳️ Negotiate with Party (Calendar tab) to boost loyalty across all their MPs.",
        "priority": 9,
        "trigger": lambda s: any(
            s["parties"][pid].get("coalition_loyalty", 65) < 50
            for pid in s["parliament"]["coalition"]
            if pid != s["player_party"] and pid in s["parties"]
        ),
    },
    {
        "id": "bill_committee_stage",
        "icon": "🏛️",
        "title": "Bill in committee — lobby now!",
        "text": "Committee stage is the BEST time to lobby. Use 🏛️ Lobby Committee or meet individual MPs to flip undecided votes before First Reading.",
        "priority": 8,
        "trigger": lambda s: any(b.get("stage") == "committee" for b in s.get("active_bills", [])),
    },
    {
        "id": "bill_failing",
        "icon": "🔴",
        "title": "Bill is failing — act now",
        "text": "An active bill is below majority threshold. Try 🐴 Horse Trading (flip opposition MPs), 📢 Media Offensive, or 🤝 Meet Individual MPs.",
        "priority": 9,
        "trigger": lambda s: any(
            (sum(1 for mp in s.get("mps", [])
                  if mp.get("vote_intentions", {}).get(b["id"]) == "yes") < s["parliament"]["majority"] - 10)
            for b in s.get("active_bills", [])
        ),
    },
    {
        "id": "inflation_high",
        "icon": "🔥",
        "title": "Inflation is dangerous",
        "text": "Inflation above 9%. Try anti-inflation legislation, or hit 🏦 Anti-Inflation in Economy → Actions. Watch for unrest.",
        "priority": 8,
        "trigger": lambda s: s["national"]["inflation"] > 9,
    },
    {
        "id": "corruption_high",
        "icon": "🔍",
        "title": "Corruption is hurting you",
        "text": "Corruption above 65 erodes trust and EU funding. Pass Anti-Corruption Agency or Anti-Oligarch laws — both massively boost your reputation.",
        "priority": 7,
        "trigger": lambda s: s["national"]["corruption"] > 65,
    },
    {
        "id": "tension_high",
        "icon": "🗣️",
        "title": "Streets are restless",
        "text": "Social tension above 70. Avoid austerity. Consider populist concessions: pension increase, minimum wage, or healthcare reform.",
        "priority": 7,
        "trigger": lambda s: s["national"]["social_tension"] > 70,
    },
    {
        "id": "election_imminent",
        "icon": "🗳️",
        "title": "Election in less than 90 days",
        "text": "Stop introducing risky bills now — focus on 🚩 Rallies, 📺 TV Addresses, and 🎤 Press Conferences to boost your poll number.",
        "priority": 9,
        "trigger": lambda s: 0 < _days_to_election(s) < 90,
    },
    {
        "id": "election_very_close",
        "icon": "⏰",
        "title": "Election in 30 days!",
        "text": "Last sprint. Spend Political Capital on big media events. Pass nothing controversial. Watch your polls.",
        "priority": 10,
        "trigger": lambda s: 0 < _days_to_election(s) < 30,
    },
    {
        "id": "pc_low",
        "icon": "💼",
        "title": "Political capital running low",
        "text": "PC below 15. Don't propose bills — they cost 8-15 PC and may fail. PC refills monthly. Wait, then strike when you have 30+.",
        "priority": 6,
        "trigger": lambda s: s["national"]["political_capital"] < 15,
    },
    {
        "id": "no_active_bills",
        "icon": "📜",
        "title": "No bills in progress",
        "text": "Parliament is idle. Go to Parliament → Propose Bill to introduce legislation. Bills take 14 days, so start early in your term.",
        "priority": 4,
        "trigger": lambda s: not s.get("active_bills") and s.get("turn", 0) > 14,
    },
    {
        "id": "nf_surging",
        "icon": "🔴",
        "title": "National Front is surging",
        "text": "NF poll above 25%. They feed on chaos. Stabilize the economy, fight corruption visibly, and pass EU-friendly bills to slow their rise.",
        "priority": 8,
        "trigger": lambda s: s["parties"].get("national_front", {}).get("poll", 0) > 25,
    },
    {
        "id": "eu_relations_low",
        "icon": "🇪🇺",
        "title": "EU relations are slipping",
        "text": "EU below 60. Use 🇪🇺 EU Diplomatic Call (cheap), pass Judicial Reform or Anti-Corruption laws, or accept their criticisms publicly.",
        "priority": 6,
        "trigger": lambda s: s["national"]["eu_relations"] < 60,
    },
    {
        "id": "energy_low",
        "icon": "⚡",
        "title": "Energy security is fragile",
        "text": "Below 50. Pass Emergency Energy Security or Renewable Transition. Energy crises are some of the worst events you can face.",
        "priority": 6,
        "trigger": lambda s: s["national"]["energy_security"] < 50,
    },
    {
        "id": "good_economy_use_it",
        "icon": "📈",
        "title": "Strong economy — capitalize!",
        "text": "GDP growing, inflation low. This is when to push controversial reforms (judicial, anti-oligarch). Trust is forgiving when wallets are full.",
        "priority": 5,
        "trigger": lambda s: s["national"]["gdp_growth"] > 3 and s["national"]["inflation"] < 5,
    },
    {
        "id": "ap_unspent",
        "icon": "⚡",
        "title": "Action Points unused",
        "text": "You have 4/4 AP and didn't use any. AP doesn't carry over — spend them on lobbying, press, or meetings each day before advancing.",
        "priority": 3,
        "trigger": lambda s: s["calendar"]["action_points"] >= s["calendar"]["max_action_points"] and s.get("turn", 1) > 5,
    },
    {
        "id": "tutorial_first_bill",
        "icon": "📖",
        "title": "Tip: Introduce your first bill",
        "text": "You're 7 days in. Try Parliament → Propose Bill. Anti-Corruption Agency is a great first choice — broad coalition support and big trust boost.",
        "priority": 4,
        "trigger": lambda s: s.get("turn", 0) > 7 and not s.get("active_bills") and not s["parliament"]["passed_laws"],
    },
    {
        "id": "tutorial_save",
        "icon": "💾",
        "title": "Tip: Save your game",
        "text": "Don't forget to save! Use 💾 Save in the sidebar. If signed in, it also goes to the cloud.",
        "priority": 2,
        "trigger": lambda s: s.get("turn", 0) > 14 and s.get("turn", 0) % 30 == 0,
    },
    {
        "id": "stable_keep_going",
        "icon": "✅",
        "title": "Doing well — keep momentum",
        "text": "Trust above 55, stability above 65. You're winning. Now is the time to push your most ambitious reform.",
        "priority": 4,
        "trigger": lambda s: s["national"]["public_trust"] > 55 and s["national"]["government_stability"] > 65,
    },
]


def _days_to_election(state):
    from .calendar_engine import days_between
    return days_between(state["calendar"]["date"], state["election_due"])


def get_relevant_tip(state, recently_shown=None):
    """Returns the most relevant tip right now, or None.

    recently_shown: list of tip IDs shown recently (won't repeat).
    """
    recently_shown = set(recently_shown or [])
    candidates = []
    for tip in TIPS:
        if tip["id"] in recently_shown:
            continue
        try:
            if tip["trigger"](state):
                candidates.append(tip)
        except Exception:
            continue

    if not candidates:
        return None

    candidates.sort(key=lambda t: -t["priority"])
    top_priority = candidates[0]["priority"]
    top_tier = [t for t in candidates if t["priority"] >= top_priority - 1]
    return random.choice(top_tier)


def maybe_show_tip(state):
    """Returns a tip dict if it's a good moment to show one, else None.
    Limits to ~1 tip per 3-5 days, never the same tip twice in a row.
    """
    history = state.setdefault("_tips_shown", [])
    last_tip_turn = state.get("_last_tip_turn", 0)
    turn = state.get("turn", 1)

    if turn - last_tip_turn < 3 and turn != 1:
        return None

    tip = get_relevant_tip(state, recently_shown=history[-5:])
    if tip:
        state["_last_tip_turn"] = turn
        history.append(tip["id"])
        if len(history) > 30:
            state["_tips_shown"] = history[-30:]
        return tip
    return None
