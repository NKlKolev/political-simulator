import random

FIRST_NAMES_M = ["Ivan", "Georgi", "Dimitar", "Stefan", "Petar", "Boyan", "Krasimir",
                  "Nikolay", "Vasil", "Hristo", "Yordan", "Kamen", "Lubomir", "Plamen",
                  "Stoyan", "Todor", "Veselin", "Ognyan", "Atanas", "Borislav", "Daniel",
                  "Emil", "Filip", "Goran", "Iliya", "Kiril", "Martin", "Nikolai",
                  "Pavel", "Rosen", "Simeon", "Tihomir", "Valentin", "Yavor", "Zhivko"]
FIRST_NAMES_F = ["Maria", "Elena", "Vesela", "Petya", "Nadia", "Zorka", "Tsveta",
                  "Iva", "Desislava", "Mariana", "Yana", "Dora", "Kalina", "Lina",
                  "Milena", "Nina", "Olga", "Plamena", "Radka", "Silvia", "Teodora",
                  "Veneta", "Yordanka", "Antonia", "Boryana", "Diana", "Evgenia"]
LAST_NAMES = ["Petrov", "Ivanov", "Dimitrov", "Stoyanov", "Markov", "Tsonev", "Dokov",
               "Nikolov", "Hristov", "Borisov", "Vasilev", "Popov", "Stancheva", "Zarev",
               "Andreev", "Bozhilov", "Cholakov", "Damyanov", "Filipov", "Gospodinov",
               "Iliev", "Kostov", "Lazarov", "Mihaylov", "Nedev", "Ognyanov", "Penev",
               "Radev", "Simeonov", "Tomov", "Uzunov", "Velikov", "Yanev", "Zhelev"]


def generate_mps(parties, regions, total_seats=240):
    mps = []
    mp_id = 1

    region_list = list(regions.items())
    party_seat_list = []
    for party_id, party in parties.items():
        for _ in range(party["seats"]):
            party_seat_list.append(party_id)

    random.shuffle(party_seat_list)

    region_seat_assignments = []
    for region_id, region in region_list:
        region_seats = region.get("seats", 30)
        for _ in range(region_seats):
            region_seat_assignments.append(region_id)
    while len(region_seat_assignments) < len(party_seat_list):
        region_seat_assignments.append(random.choice([r[0] for r in region_list]))
    region_seat_assignments = region_seat_assignments[:len(party_seat_list)]

    for i, party_id in enumerate(party_seat_list):
        region_id = region_seat_assignments[i] if i < len(region_seat_assignments) else random.choice([r[0] for r in region_list])
        mp = _generate_mp(mp_id, party_id, region_id, parties[party_id])
        mps.append(mp)
        mp_id += 1

    return mps


def _generate_mp(mp_id, party_id, region_id, party):
    is_female = random.random() < 0.32
    first_name = random.choice(FIRST_NAMES_F if is_female else FIRST_NAMES_M)
    last_name = random.choice(LAST_NAMES)
    if is_female and not last_name.endswith("a"):
        last_name = last_name + "a"

    party_ideology = party.get("ideology", {})

    mp_ideology = {}
    for key, base in party_ideology.items():
        deviation = random.gauss(0, 0.15)
        mp_ideology[key] = max(-1, min(1, base + deviation))

    factions = ["mainstream", "reformist", "hardliner", "pragmatist", "regional_boss"]
    faction = random.choices(factions, weights=[40, 20, 15, 15, 10])[0]

    return {
        "id": mp_id,
        "name": f"{first_name} {last_name}",
        "gender": "F" if is_female else "M",
        "party": party_id,
        "region": region_id,
        "ideology": mp_ideology,
        "loyalty": int(60 + random.gauss(0, 15)),
        "persuadability": int(35 + random.gauss(0, 20)),
        "personal_relationship": int(50 + random.gauss(0, 10)),
        "ambition": int(50 + random.gauss(0, 20)),
        "corruption_risk": int(party.get("risks", {}).get("corruption", 30) + random.gauss(0, 15)),
        "media_profile": int(30 + random.gauss(0, 20)),
        "faction": faction,
        "vote_intentions": {},
        "ministerial": False,
        "rebellion_count": 0,
        "lobbying_received": 0,
    }


def update_mp_vote_intention(mp, bill, state):
    party = state["parties"].get(mp["party"], {})
    coalition = state["parliament"]["coalition"]
    in_coalition = mp["party"] in coalition

    bill_support_for_party = (bill.get("coalition_support", {}) if in_coalition else bill.get("opposition_support", {}))
    base_support_pct = bill_support_for_party.get(mp["party"], 50 if in_coalition else 20)

    score = base_support_pct

    score += _ideology_alignment(mp, bill) * 20

    party_loyalty = max(0, mp["loyalty"]) / 100.0
    relationship = max(0, mp["personal_relationship"]) / 100.0

    if in_coalition:
        score += party_loyalty * 15
        score += relationship * 10
    else:
        score += relationship * 8

    score += (mp.get("lobbying_received", 0)) * 4

    score += random.gauss(0, 5)

    if score >= 60:
        return "yes"
    elif score >= 40:
        return "undecided"
    elif score >= 25:
        return "abstain"
    else:
        return "no"


def _ideology_alignment(mp, bill):
    bill_type = bill.get("type", "")
    ideo = mp.get("ideology", {})

    if bill_type == "anti_corruption":
        return -ideo.get("democratic_authoritarian", 0)
    if bill_type == "social_policy":
        return -ideo.get("economic_left_right", 0)
    if bill_type == "environmental":
        return -ideo.get("green_industrial", 0)
    if bill_type == "foreign_policy":
        return -ideo.get("pro_west_east", 0)
    if bill_type == "security":
        return ideo.get("nationalist_globalist", 0) * 0.5
    if bill_type == "institutional":
        return -ideo.get("democratic_authoritarian", 0) * 0.5
    return 0


def calculate_bill_support(state, bill):
    mps = state.get("mps", [])
    yes = 0
    no = 0
    abstain = 0
    undecided = 0

    for mp in mps:
        intention = mp["vote_intentions"].get(bill["id"], "undecided")
        if intention == "yes":
            yes += 1
        elif intention == "no":
            no += 1
        elif intention == "abstain":
            abstain += 1
        else:
            undecided += 1

    total = len(mps)
    pct = round((yes / total) * 100, 1) if total else 0

    return {
        "yes": yes, "no": no, "abstain": abstain, "undecided": undecided,
        "total": total, "pct": pct,
        "majority": state["parliament"]["majority"],
        "passing": yes >= state["parliament"]["majority"]
    }


def initialize_vote_intentions(state, bill):
    bill_id = bill["id"]
    for mp in state["mps"]:
        if bill_id not in mp["vote_intentions"]:
            mp["vote_intentions"][bill_id] = update_mp_vote_intention(mp, bill, state)


def lobby_mp(state, mp_id, intensity=1):
    for mp in state["mps"]:
        if mp["id"] == mp_id:
            persuadability = mp["persuadability"] / 100.0
            relationship_gain = int(intensity * 8 * (0.5 + persuadability))
            mp["personal_relationship"] = min(100, mp["personal_relationship"] + relationship_gain)
            mp["lobbying_received"] = mp.get("lobbying_received", 0) + intensity

            for bill_id in list(mp["vote_intentions"].keys()):
                bill = next((b for b in state.get("active_bills", []) if b["id"] == bill_id), None)
                if bill:
                    mp["vote_intentions"][bill_id] = update_mp_vote_intention(mp, bill, state)
            return True
    return False


def lobby_party(state, party_id, intensity=2):
    affected = 0
    for mp in state["mps"]:
        if mp["party"] != party_id:
            continue
        gain = int(intensity * 4 + random.gauss(0, 2))
        mp["personal_relationship"] = min(100, mp["personal_relationship"] + gain)
        mp["lobbying_received"] = mp.get("lobbying_received", 0) + 0.5
        for bill_id in list(mp["vote_intentions"].keys()):
            bill = next((b for b in state.get("active_bills", []) if b["id"] == bill_id), None)
            if bill:
                mp["vote_intentions"][bill_id] = update_mp_vote_intention(mp, bill, state)
        affected += 1

    if party_id in state["parties"]:
        state["parties"][party_id]["coalition_loyalty"] = min(
            100, state["parties"][party_id].get("coalition_loyalty", 65) + intensity * 3
        )
    return affected
