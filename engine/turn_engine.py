import random
from .game_state import (clamp, add_news, check_game_over, get_coalition_seat_total,
                          get_days_to_election, get_date_string)
from .economy_engine import update_economy
from .event_engine import check_and_fire_events, generate_ai_headlines
from .calendar_engine import advance_day, is_parliament_day, is_weekend, get_weekday
from .bill_engine import advance_bill_stages


def advance_day_turn(state):
    """Advance one day. Used for the lawgivers-style daily mode."""
    if state.get("game_over"):
        return state

    state["calendar"]["date"] = advance_day(state["calendar"]["date"], 1)
    state["turn"] += 1

    state["calendar"]["action_points"] = state["calendar"].get("max_action_points", 4)

    weekday = get_weekday(state["calendar"]["date"])

    advance_bill_stages(state)

    if state["turn"] % 7 == 0:
        _weekly_economy_update(state)
    if state["turn"] % 30 == 0:
        _monthly_indicators_update(state)

    _update_party_polls_daily(state)
    _update_coalition_health_daily(state)

    if is_parliament_day(state["calendar"]["date"]) and random.random() < 0.4:
        check_and_fire_events(state)
    elif random.random() < 0.18:
        check_and_fire_events(state)

    if random.random() < 0.25:
        headline = generate_ai_headlines(state)
        if headline:
            add_news(state, *headline)

    _record_history_daily(state)
    _check_election_trigger(state)
    check_game_over(state)

    return state


def _weekly_economy_update(state):
    update_economy(state)


def _monthly_indicators_update(state):
    n = state["national"]
    diff = state["meta"]["diff_mod"]

    trust_drift = _calculate_trust_drift(n, diff)
    n["public_trust"] = int(clamp(n["public_trust"] + trust_drift))

    stability_drift = _calculate_stability_drift(state)
    n["government_stability"] = int(clamp(n["government_stability"] + stability_drift))

    if n["corruption"] > 60:
        n["rule_of_law"] = int(clamp(n["rule_of_law"] - 0.1 * diff))
    if n["rule_of_law"] > 65:
        n["corruption"] = int(clamp(n["corruption"] - 0.1))

    social_drift = 0
    if n["inflation"] > 8:
        social_drift += 0.5 * diff
    if n["unemployment"] > 17:
        social_drift += 0.3 * diff
    if n["gdp_growth"] > 3:
        social_drift -= 0.3
    n["social_tension"] = int(clamp(n["social_tension"] + social_drift))

    n["political_capital"] = int(clamp(n["political_capital"] + 6))
    add_news(state, "💼", "Monthly political capital increase. Cabinet realigns priorities.", "political")


def _calculate_trust_drift(n, diff):
    drift = 0
    if n["gdp_growth"] > 3.5:
        drift += 0.4
    elif n["gdp_growth"] < 0:
        drift -= 0.4
    if n["inflation"] > 10:
        drift -= 0.5 * diff
    elif n["inflation"] > 7:
        drift -= 0.3 * diff
    elif n["inflation"] < 3:
        drift += 0.2
    if n["unemployment"] > 20:
        drift -= 0.4 * diff
    if n["corruption"] > 70:
        drift -= 0.3 * diff
    elif n["corruption"] < 40:
        drift += 0.15
    drift += random.gauss(0, 0.15)
    return drift


def _calculate_stability_drift(state):
    n = state["national"]
    coalition_seats = get_coalition_seat_total(state)
    majority = state["parliament"]["majority"]

    drift = 0
    seat_margin = coalition_seats - majority
    if seat_margin < 5:
        drift -= 0.5
    elif seat_margin > 20:
        drift += 0.1

    loyalties = []
    for pid in state["parliament"]["coalition"]:
        if pid in state["parties"] and pid != state["player_party"]:
            loyalties.append(state["parties"][pid].get("coalition_loyalty", 65))
    if loyalties:
        avg_loyalty = sum(loyalties) / len(loyalties)
        if avg_loyalty < 50:
            drift -= 0.5
        elif avg_loyalty > 75:
            drift += 0.1

    if n["public_trust"] < 35:
        drift -= 0.3
    if n["social_tension"] > 75:
        drift -= 0.3
    drift += random.gauss(0, 0.1)
    return drift


def _update_party_polls_daily(state):
    if state["turn"] % 3 != 0:
        return
    n = state["national"]
    parties = state["parties"]
    player_id = state["player_party"]

    player_poll_change = 0
    if n["gdp_growth"] > 2:
        player_poll_change += 0.04
    elif n["gdp_growth"] < 0:
        player_poll_change -= 0.06
    if n["inflation"] > 9:
        player_poll_change -= 0.10
    elif n["inflation"] < 4:
        player_poll_change += 0.05
    if n["public_trust"] > 55:
        player_poll_change += 0.06
    elif n["public_trust"] < 35:
        player_poll_change -= 0.09
    if n["corruption"] > 65:
        player_poll_change -= 0.07
    player_poll_change += random.gauss(0, 0.15)
    parties[player_id]["poll"] = round(clamp(parties[player_id]["poll"] + player_poll_change, 5, 60), 1)

    for party_id, party in parties.items():
        if party_id == player_id:
            continue
        drift = random.gauss(0, 0.12)
        if party_id == "national_front":
            if n["public_trust"] < 40:
                drift += 0.07
            if n["social_tension"] > 65:
                drift += 0.08
        elif party_id == "citizens_union":
            if n["gdp_growth"] < 1:
                drift += 0.04
        party["poll"] = round(clamp(party["poll"] + drift, 1, 55), 1)

    total = sum(p["poll"] for p in parties.values())
    if total > 0:
        for p in parties.values():
            p["poll"] = round((p["poll"] / total) * 100, 1)


def _update_coalition_health_daily(state):
    if state["turn"] % 5 != 0:
        return
    parties = state["parties"]
    coalition = state["parliament"]["coalition"]
    n = state["national"]

    for party_id in coalition:
        if party_id == state["player_party"] or party_id not in parties:
            continue
        p = parties[party_id]
        loyalty_drift = 0.0
        if n["government_stability"] < 50:
            loyalty_drift -= 0.3
        if n["public_trust"] < 40:
            loyalty_drift -= 0.2
        loyalty_drift += random.gauss(0, 0.3)
        current = p.get("coalition_loyalty", 65)
        p["coalition_loyalty"] = int(clamp(current + loyalty_drift))


def _check_election_trigger(state):
    days_left = get_days_to_election(state)
    if days_left <= 0 or state.get("election_triggered"):
        state["phase"] = "election"
        if not state.get("_election_announced"):
            add_news(state, "🗳️",
                     f"ELECTION DAY: Pustinyakovo goes to the polls!",
                     "political")
            state["_election_announced"] = True


def _record_history_daily(state):
    if state["turn"] % 7 != 0:
        return
    n = state["national"]
    state["history"]["approval_history"].append({
        "turn": state["turn"],
        "date": get_date_string(state),
        "public_trust": n["public_trust"],
        "stability": n["government_stability"],
        "poll": state["parties"][state["player_party"]]["poll"]
    })
    state["history"]["economic_history"].append({
        "turn": state["turn"],
        "date": get_date_string(state),
        "gdp": n["gdp_growth"],
        "inflation": n["inflation"],
        "unemployment": n["unemployment"]
    })


def advance_turn(state):
    return advance_day_turn(state)


def advance_multiple_days(state, days):
    for _ in range(days):
        if state.get("active_events"):
            break
        if state.get("game_over"):
            break
        state = advance_day_turn(state)
    return state
