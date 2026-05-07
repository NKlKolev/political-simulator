import random
from .calendar_engine import advance_day, format_date
from .mp_generator import calculate_bill_support, initialize_vote_intentions, update_mp_vote_intention
from .game_state import clamp, add_news


BILL_STAGES = [
    {"id": "drafting",   "label": "Drafting",         "duration": 3, "icon": "✍️"},
    {"id": "committee",  "label": "Committee",        "duration": 5, "icon": "🏛️"},
    {"id": "first_read", "label": "First Reading",    "duration": 2, "icon": "📖"},
    {"id": "debate",     "label": "Public Debate",    "duration": 3, "icon": "🗣️"},
    {"id": "final_vote", "label": "Final Vote",       "duration": 1, "icon": "🗳️"},
]

STAGE_TOTAL_DAYS = sum(s["duration"] for s in BILL_STAGES)


def introduce_bill(state, bill_template):
    if any(b["id"] == bill_template["id"] for b in state.get("active_bills", [])):
        return False, "Bill already in progress."

    pc_cost = bill_template.get("political_capital_cost", 8)
    if state["national"]["political_capital"] < pc_cost:
        return False, "Not enough political capital."

    state["national"]["political_capital"] -= pc_cost

    current_date = state["calendar"]["date"]

    bill = {
        **bill_template,
        "introduced_on": current_date,
        "stage": "drafting",
        "stage_started": current_date,
        "stage_day": 0,
        "scheduled_events": [],
        "lobbying_log": [],
        "support_history": [],
    }

    cursor = current_date
    for stage in BILL_STAGES:
        bill["scheduled_events"].append({
            "date": cursor,
            "type": "stage_start",
            "label": f"{stage['label']} begins",
            "stage_id": stage["id"],
            "icon": stage["icon"]
        })
        cursor = advance_day(cursor, stage["duration"])

    bill["scheduled_events"].append({
        "date": advance_day(current_date, STAGE_TOTAL_DAYS - 1),
        "type": "vote",
        "label": f"Final vote on {bill['title']}",
        "icon": "🗳️"
    })

    state.setdefault("active_bills", []).append(bill)

    initialize_vote_intentions(state, bill)
    support = calculate_bill_support(state, bill)
    bill["support_history"].append({
        "day": 0,
        "yes": support["yes"],
        "no": support["no"],
        "undecided": support["undecided"],
        "abstain": support["abstain"]
    })

    add_news(state, "📜",
             f"Bill introduced: '{bill['title']}'. Initial support {support['pct']}%.",
             "political")

    return True, bill


def advance_bill_stages(state):
    for bill in list(state.get("active_bills", [])):
        bill["stage_day"] = bill.get("stage_day", 0) + 1
        current_stage = next((s for s in BILL_STAGES if s["id"] == bill["stage"]), None)
        if not current_stage:
            continue

        if bill["stage_day"] >= current_stage["duration"]:
            _move_to_next_stage(state, bill)

        support = calculate_bill_support(state, bill)
        days_in = (state["turn"] - state.get("turn_at_bill_introduce", state["turn"])) if False else len(bill.get("support_history", []))
        bill["support_history"].append({
            "day": days_in,
            "yes": support["yes"],
            "no": support["no"],
            "undecided": support["undecided"],
            "abstain": support["abstain"]
        })

        if random.random() < 0.15:
            _drift_intentions(state, bill)


def _move_to_next_stage(state, bill):
    stages = [s["id"] for s in BILL_STAGES]
    cur_idx = stages.index(bill["stage"])
    if cur_idx + 1 < len(stages):
        next_stage = stages[cur_idx + 1]
        bill["stage"] = next_stage
        bill["stage_day"] = 0
        bill["stage_started"] = state["calendar"]["date"]
        stage_def = next(s for s in BILL_STAGES if s["id"] == next_stage)
        add_news(state, stage_def["icon"],
                  f"Bill '{bill['title']}' moves to {stage_def['label']} stage.",
                  "political")
    else:
        _conduct_final_vote(state, bill)


def _conduct_final_vote(state, bill):
    support = calculate_bill_support(state, bill)
    yes = support["yes"]
    no = support["no"]
    abstain = support["abstain"]
    undecided = support["undecided"]

    yes += int(undecided * 0.4)
    no += int(undecided * 0.4)
    abstain += undecided - int(undecided * 0.4) - int(undecided * 0.4)

    yes += random.randint(-3, 3)
    no = 240 - yes - abstain

    passed = yes >= state["parliament"]["majority"]

    result = {
        "yes": yes, "no": no, "abstain": abstain,
        "passed": passed,
        "majority_needed": state["parliament"]["majority"]
    }

    state.setdefault("active_bills", [])
    state["active_bills"] = [b for b in state["active_bills"] if b["id"] != bill["id"]]

    if passed:
        _pass_bill(state, bill, result)
    else:
        _fail_bill(state, bill, result)


def _pass_bill(state, bill, result):
    state["parliament"].setdefault("passed_laws", []).append({
        "id": bill["id"],
        "title": bill["title"],
        "turn_passed": state["turn"],
        "vote": result,
        "implementing": True,
        "turns_remaining": bill.get("implementation_turns", 90),
    })

    budget_cost = bill.get("budget_cost", 0)
    state["national"]["budget_deficit"] = round(state["national"]["budget_deficit"] + budget_cost, 2)

    state.setdefault("implementing_laws", []).append({
        "bill_id": bill["id"],
        "bill": bill,
        "days_remaining": bill.get("implementation_turns", 3) * 30,
        "introduced_on": bill.get("introduced_on")
    })

    add_news(state, "⚖️",
             bill.get("news_pass", f"Parliament passes: {bill['title']}. Vote: {result['yes']}-{result['no']}."),
             "political")
    state["history"]["laws_passed"].append({
        "turn": state["turn"],
        "bill_id": bill["id"],
        "title": bill["title"],
        "vote": result
    })


def _fail_bill(state, bill, result):
    state["parliament"].setdefault("failed_bills", []).append({
        "id": bill["id"],
        "title": bill["title"],
        "turn_failed": state["turn"],
        "vote": result
    })
    add_news(state, "❌",
              bill.get("news_fail", f"Bill failed: {bill['title']}. Vote: {result['yes']}-{result['no']}."),
              "political")
    state["national"]["government_stability"] = int(clamp(state["national"]["government_stability"] - 4))
    state["national"]["public_trust"] = int(clamp(state["national"]["public_trust"] - 2))


def _drift_intentions(state, bill):
    for mp in state["mps"]:
        if random.random() < 0.05:
            mp["vote_intentions"][bill["id"]] = update_mp_vote_intention(mp, bill, state)


def get_bill_progress_pct(bill):
    stages = BILL_STAGES
    completed_days = 0
    for s in stages:
        if s["id"] == bill["stage"]:
            completed_days += bill.get("stage_day", 0)
            break
        completed_days += s["duration"]
    total = sum(s["duration"] for s in stages)
    return round(completed_days / total * 100, 1)


def get_current_stage(bill):
    return next((s for s in BILL_STAGES if s["id"] == bill["stage"]), BILL_STAGES[0])


def days_to_vote(bill):
    stages = BILL_STAGES
    completed_days = 0
    for s in stages:
        if s["id"] == bill["stage"]:
            completed_days += bill.get("stage_day", 0)
            break
        completed_days += s["duration"]
    total = sum(s["duration"] for s in stages)
    return max(0, total - completed_days)
