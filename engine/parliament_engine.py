import random
from .game_state import clamp, add_news


def calculate_bill_vote(state, bill):
    coalition = state["parliament"]["coalition"]
    parties = state["parties"]
    n = state["national"]

    coalition_base = sum(parties[p]["seats"] for p in coalition if p in parties)

    coalition_support_rate = _get_coalition_support_rate(state, bill)
    yes_from_coalition = int(coalition_base * coalition_support_rate)

    yes_from_opposition = 0
    for party_id, party in parties.items():
        if party_id in coalition:
            continue
        opp_support = bill.get("opposition_support", {}).get(party_id, 10) / 100
        opp_support *= _modifier_from_ideology(party, bill)
        yes_from_opposition += int(party["seats"] * opp_support)

    total_yes = yes_from_coalition + yes_from_opposition
    total_no = 240 - total_yes

    noise = random.randint(-6, 6)
    total_yes = max(0, min(240, total_yes + noise))
    total_no = 240 - total_yes

    passed = total_yes >= state["parliament"]["majority"]

    return {
        "yes": total_yes,
        "no": total_no,
        "passed": passed,
        "majority_needed": state["parliament"]["majority"]
    }


def _get_coalition_support_rate(state, bill):
    coalition = state["parliament"]["coalition"]
    parties = state["parties"]
    n = state["national"]

    total_coalition_seats = sum(parties[p]["seats"] for p in coalition if p in parties)
    weighted_support = 0

    for party_id in coalition:
        if party_id not in parties:
            continue
        party = parties[party_id]
        party_seats = party["seats"]
        base_support = bill.get("coalition_support", {}).get(party_id, 70) / 100

        loyalty = party.get("coalition_loyalty", 65) / 100
        tension = party.get("faction_tension", 40) / 100

        stability_mod = (n["government_stability"] - 50) / 200

        party_support = base_support * loyalty * (1 - tension * 0.3) + stability_mod
        party_support = max(0.1, min(1.0, party_support))

        weight = party_seats / total_coalition_seats
        weighted_support += party_support * weight

    return weighted_support


def _modifier_from_ideology(party, bill):
    bill_type = bill.get("type", "")
    ideology = party.get("ideology", {})

    if bill_type == "anti_corruption":
        base = ideology.get("democratic_authoritarian", 0)
        return max(0.1, 1.0 - base * 0.5)
    if bill_type == "social_policy":
        base = ideology.get("economic_left_right", 0)
        return max(0.1, 1.0 - base * 0.4)
    if bill_type == "environmental":
        base = ideology.get("green_industrial", 0)
        return max(0.1, 1.0 - base * 0.5)
    return 1.0


def propose_bill(state, bill):
    cost = bill.get("political_capital_cost", 8)
    if state["national"]["political_capital"] < cost:
        return False, "Insufficient political capital."

    if state["parliament"]["votes_this_turn"] >= 1:
        return False, "Already voted on a bill this turn."

    state["national"]["political_capital"] -= cost
    state["parliament"]["active_bill"] = bill
    state["parliament"]["votes_this_turn"] = 1

    result = calculate_bill_vote(state, bill)

    if result["passed"]:
        _pass_bill(state, bill, result)
        return True, result
    else:
        _fail_bill(state, bill, result)
        return False, result


def _pass_bill(state, bill, result):
    from .game_state import apply_national_effects, apply_voter_effects, apply_region_effects

    state["parliament"]["passed_laws"].append({
        "id": bill["id"],
        "title": bill["title"],
        "turn_passed": state["turn"],
        "vote": result,
        "implementing": True,
        "turns_remaining": bill.get("implementation_turns", 3)
    })

    budget_cost = bill.get("budget_cost", 0)
    state["national"]["budget_deficit"] = round(state["national"]["budget_deficit"] + budget_cost, 2)

    state["implementing_laws"].append({
        "bill_id": bill["id"],
        "bill": bill,
        "turns_remaining": bill.get("implementation_turns", 3),
        "turn_passed": state["turn"]
    })

    news_text = bill.get("news_pass", f"Parliament passes: {bill['title']}. Vote: {result['yes']}-{result['no']}.")
    add_news(state, "⚖️", news_text, "political")

    state["history"]["laws_passed"].append({
        "turn": state["turn"],
        "bill_id": bill["id"],
        "title": bill["title"],
        "vote": result
    })

    state["national"]["democratic_quality"] = int(clamp(state["national"]["democratic_quality"] + 1))


def _fail_bill(state, bill, result):
    state["parliament"]["failed_bills"].append({
        "id": bill["id"],
        "title": bill["title"],
        "turn_failed": state["turn"],
        "vote": result
    })

    news_text = bill.get("news_fail", f"Bill failed: {bill['title']}. Vote: {result['yes']}-{result['no']}.")
    add_news(state, "❌", news_text, "political")

    state["national"]["government_stability"] = int(clamp(state["national"]["government_stability"] - 5))
    state["national"]["public_trust"] = int(clamp(state["national"]["public_trust"] - 3))


def process_implementing_laws(state):
    completed = []
    remaining = []

    for impl in state.get("implementing_laws", []):
        impl["turns_remaining"] -= 1
        if impl["turns_remaining"] <= 0:
            _apply_law_full_effects(state, impl["bill"])
            completed.append(impl["bill_id"])
        else:
            remaining.append(impl)

    state["implementing_laws"] = remaining

    for bill_id in completed:
        for law in state["parliament"]["passed_laws"]:
            if law["id"] == bill_id:
                law["implementing"] = False
        if random.random() < 0.3:
            pass


def _apply_law_full_effects(state, bill):
    from .game_state import (apply_national_effects, apply_voter_effects,
                              apply_region_effects)
    effects = bill.get("effects_on_pass", {})

    if "national" in effects:
        apply_national_effects(state, effects["national"])

    if "voter_effects" in effects:
        apply_voter_effects(state, effects["voter_effects"])

    if "regions" in effects:
        apply_region_effects(state, effects["regions"])

    if "coalition_effects" in effects:
        from .game_state import apply_coalition_effects
        apply_coalition_effects(state, effects["coalition_effects"])

    add_news(state, "✅", f"Law fully implemented: {bill['title']}. Effects now visible.", "political")


def reset_votes_for_turn(state):
    state["parliament"]["votes_this_turn"] = 0
    state["parliament"]["active_bill"] = None
