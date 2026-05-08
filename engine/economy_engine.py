import random
from .game_state import clamp, add_news


def update_economy(state):
    n = state["national"]
    diff = state["meta"]["diff_mod"]

    _apply_inflation_dynamics(n, diff)
    _apply_growth_dynamics(n, diff)
    _apply_unemployment_dynamics(n, diff)
    _apply_debt_dynamics(n, diff)
    _apply_confidence_dynamics(n)
    _check_economic_news(state)


def _apply_inflation_dynamics(n, diff):
    base_change = 0.0

    if n["gdp_growth"] > 3.5:
        base_change += 0.15
    elif n["gdp_growth"] < 0:
        base_change -= 0.20

    if n["budget_deficit"] > 5:
        base_change += 0.10
    if n["budget_deficit"] > 7:
        base_change += 0.15

    if n["energy_security"] < 45:
        base_change += 0.10

    shock = random.gauss(0, 0.15 * diff)

    n["inflation"] = round(max(0, n["inflation"] + base_change + shock), 2)

    if n["inflation"] > 5:
        n["public_trust"] = int(clamp(n["public_trust"] - 0.3))
        n["social_tension"] = int(clamp(n["social_tension"] + 0.2))
    if n["inflation"] > 10:
        n["public_trust"] = int(clamp(n["public_trust"] - 0.5))
        n["social_tension"] = int(clamp(n["social_tension"] + 0.4))


def _apply_growth_dynamics(n, diff):
    base = 0.0

    if n["business_confidence"] > 60:
        base += 0.05
    elif n["business_confidence"] < 40:
        base -= 0.05

    if n["foreign_investment"] > 55:
        base += 0.05

    if n["eu_relations"] > 70:
        base += 0.04

    if n["corruption"] > 70:
        base -= 0.08

    shock = random.gauss(0, 0.1 * diff)
    n["gdp_growth"] = round(max(-8, min(8, n["gdp_growth"] + base + shock)), 2)

    if n["gdp_growth"] > 2:
        n["public_trust"] = int(clamp(n["public_trust"] + 0.2))
        n["business_confidence"] = int(clamp(n["business_confidence"] + 0.3))
    elif n["gdp_growth"] < 0:
        n["public_trust"] = int(clamp(n["public_trust"] - 0.3))
        n["social_tension"] = int(clamp(n["social_tension"] + 0.3))


def _apply_unemployment_dynamics(n, diff):
    target = 12.0

    if n["gdp_growth"] > 3:
        target -= 2.0
    elif n["gdp_growth"] > 1.5:
        target -= 0.5
    elif n["gdp_growth"] < 0:
        target += 3.0
    elif n["gdp_growth"] < 1:
        target += 1.0

    gap = target - n["unemployment"]
    n["unemployment"] = round(max(3, min(35, n["unemployment"] + gap * 0.05 + random.gauss(0, 0.1 * diff))), 2)

    if n["unemployment"] > 18:
        n["social_tension"] = int(clamp(n["social_tension"] + 0.3))
    elif n["unemployment"] < 8:
        n["public_trust"] = int(clamp(n["public_trust"] + 0.2))


def _apply_debt_dynamics(n, diff):
    if n["budget_deficit"] > 0:
        n["public_debt"] = round(n["public_debt"] + n["budget_deficit"] * 0.08, 2)
    else:
        n["public_debt"] = round(max(0, n["public_debt"] + n["budget_deficit"] * 0.05), 2)

    if n["public_debt"] > 90:
        n["eu_relations"] = int(clamp(n["eu_relations"] - 0.3))
        n["business_confidence"] = int(clamp(n["business_confidence"] - 0.3))


def _apply_confidence_dynamics(n):
    if n["corruption"] > 65:
        n["business_confidence"] = int(clamp(n["business_confidence"] - 0.2))
        n["foreign_investment"] = int(clamp(n["foreign_investment"] - 0.15))

    if n["rule_of_law"] > 65:
        n["business_confidence"] = int(clamp(n["business_confidence"] + 0.15))
        n["foreign_investment"] = int(clamp(n["foreign_investment"] + 0.1))

    if n["eu_relations"] > 72:
        n["foreign_investment"] = int(clamp(n["foreign_investment"] + 0.1))


def _check_economic_news(state):
    n = state["national"]
    t = state["turn"]

    if t > 1:
        if n["gdp_growth"] > 4.0 and random.random() < 0.4:
            add_news(state, "📈", f"GDP growth hits {n['gdp_growth']}% — above expectations. Markets respond positively.", "economic")
        elif n["gdp_growth"] < -0.5 and random.random() < 0.5:
            add_news(state, "📉", f"Economy contracts by {abs(n['gdp_growth'])}%. Recession fears grow.", "economic")

        if n["inflation"] > 12 and random.random() < 0.4:
            add_news(state, "🔥", f"Inflation reaches {n['inflation']}% — highest in over a decade. Households struggle.", "economic")

        if n["unemployment"] > 20 and random.random() < 0.3:
            add_news(state, "😔", f"Unemployment reaches {n['unemployment']}%. Protests expected in industrial regions.", "economic")


def get_economic_summary(state):
    n = state["national"]
    assessment = []

    if n["gdp_growth"] > 3:
        assessment.append("Strong growth")
    elif n["gdp_growth"] > 1:
        assessment.append("Moderate growth")
    elif n["gdp_growth"] > -1:
        assessment.append("Stagnation")
    else:
        assessment.append("Recession")

    if n["inflation"] < 3:
        assessment.append("Low inflation")
    elif n["inflation"] < 6:
        assessment.append("Moderate inflation")
    elif n["inflation"] < 10:
        assessment.append("High inflation")
    else:
        assessment.append("Crisis-level inflation")

    if n["unemployment"] < 8:
        assessment.append("Low unemployment")
    elif n["unemployment"] < 14:
        assessment.append("High unemployment")
    else:
        assessment.append("Mass unemployment")

    return " | ".join(assessment)
