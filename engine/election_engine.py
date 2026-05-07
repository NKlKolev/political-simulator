import random
import math
from .game_state import clamp, add_news


THRESHOLD = 4.0
TOTAL_SEATS = 240


def run_election(state):
    party_votes = _calculate_votes(state)
    party_votes_filtered = _apply_threshold(party_votes)
    seat_allocation = _dhondt(party_votes_filtered, TOTAL_SEATS)

    for party_id, seats in seat_allocation.items():
        if party_id in state["parties"]:
            state["parties"][party_id]["seats"] = seats
            state["parties"][party_id]["vote_share"] = round(party_votes.get(party_id, 0), 1)

    wasted_parties = [
        pid for pid, votes in party_votes.items()
        if votes < THRESHOLD and pid not in seat_allocation
    ]

    winner = max(seat_allocation.items(), key=lambda x: x[1])[0] if seat_allocation else None

    results = {
        "vote_shares": {pid: round(v, 1) for pid, v in party_votes.items()},
        "filtered_shares": {pid: round(v, 1) for pid, v in party_votes_filtered.items()},
        "seats": seat_allocation,
        "winner": winner,
        "wasted_parties": wasted_parties,
        "majority": state["parliament"]["majority"],
        "coalition_options": _calculate_coalition_options(seat_allocation, state)
    }

    state["parliament"]["total_seats"] = TOTAL_SEATS
    state["election_triggered"] = False
    state["history"]["election_results"].append({
        "turn": state["turn"],
        "date": f"{state['date']['month']}/{state['date']['year']}",
        "results": results
    })

    add_news(state, "🗳️",
             f"Election results: {state['parties'][winner]['name']} leads with {seat_allocation.get(winner, 0)} seats.",
             "political")

    _schedule_next_election(state)

    return results


def _calculate_votes(state):
    parties = state["parties"]
    n = state["national"]
    voter_groups = state["voter_groups"]

    raw_scores = {}

    for party_id, party in parties.items():
        score = party["poll"]

        score += _economy_effect(party_id, n)
        score += _trust_effect(party_id, n, state["parliament"]["coalition"])
        score += _corruption_effect(party_id, party, n)
        score += _scandal_effect(party_id, n)

        score += random.gauss(0, 1.5)
        raw_scores[party_id] = max(0.5, score)

    total = sum(raw_scores.values())
    return {pid: (v / total) * 100 for pid, v in raw_scores.items()}


def _economy_effect(party_id, n):
    effect = 0
    if party_id in ("democratic_alliance", "social_democrats", "green_future", "liberal_democrats"):
        if n["gdp_growth"] > 2.5:
            effect += 1.5
        elif n["gdp_growth"] < 0:
            effect -= 2.0
        if n["inflation"] > 9:
            effect -= 2.5
        elif n["inflation"] < 4:
            effect += 1.0
        if n["unemployment"] > 18:
            effect -= 1.5
    else:
        if n["gdp_growth"] < 0:
            effect += 2.0
        if n["inflation"] > 9:
            effect += 2.5
        if n["unemployment"] > 18:
            effect += 1.5
    return effect


def _trust_effect(party_id, n, coalition):
    if party_id in coalition:
        trust_mod = (n["public_trust"] - 50) / 20
        return trust_mod
    else:
        if n["public_trust"] < 40:
            return 1.5
        return 0


def _corruption_effect(party_id, party, n):
    if party_id in ("democratic_alliance", "green_future"):
        if n["corruption"] > 65:
            return 1.5
        return 0
    elif party_id == "national_front":
        if n["corruption"] > 60:
            return 2.0
        return 0
    return 0


def _scandal_effect(party_id, n):
    if n["democratic_quality"] < 55 and party_id == "national_front":
        return 1.5
    return 0


def _apply_threshold(vote_shares):
    filtered = {pid: v for pid, v in vote_shares.items() if v >= THRESHOLD}
    if not filtered:
        max_party = max(vote_shares.items(), key=lambda x: x[1])[0]
        filtered = {max_party: vote_shares[max_party]}
    return filtered


def _dhondt(vote_shares, total_seats):
    parties = list(vote_shares.keys())
    votes = {p: vote_shares[p] for p in parties}
    seats = {p: 0 for p in parties}
    quotients = {p: votes[p] for p in parties}

    for _ in range(total_seats):
        winner = max(quotients.items(), key=lambda x: x[1])[0]
        seats[winner] += 1
        quotients[winner] = votes[winner] / (seats[winner] + 1)

    return seats


def _calculate_coalition_options(seats, state):
    parties = list(seats.keys())
    majority = state["parliament"]["majority"]
    options = []

    player_party = state["player_party"]
    player_seats = seats.get(player_party, 0)

    for i in range(len(parties)):
        for j in range(i + 1, len(parties)):
            combo = [parties[i], parties[j]]
            total = sum(seats[p] for p in combo)
            if total >= majority:
                options.append(combo)

    for i in range(len(parties)):
        for j in range(i + 1, len(parties)):
            for k in range(j + 1, len(parties)):
                combo = [parties[i], parties[j], parties[k]]
                total = sum(seats[p] for p in combo)
                already_covered = any(
                    set(opt).issubset(set(combo)) for opt in options
                )
                if total >= majority and not already_covered:
                    options.append(combo)

    player_options = [opt for opt in options if player_party in opt]
    return player_options[:5]


def _schedule_next_election(state):
    d = state["date"]
    state["election_due"] = {
        "year": d["year"] + 4,
        "month": d["month"]
    }


def calculate_election_forecast(state):
    parties = state["parties"]
    n = state["national"]

    forecasts = {}
    for party_id, party in parties.items():
        base = party["poll"]
        trend = _economy_effect(party_id, n) * 0.5
        forecasts[party_id] = {
            "low": max(1, round(base + trend - 3, 1)),
            "central": round(base + trend, 1),
            "high": round(base + trend + 3, 1)
        }

    return forecasts
