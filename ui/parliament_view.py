import streamlit as st
import json
import os
import math
from .styles import PARTY_COLORS, inject_css, safe_html
from engine.bill_engine import (introduce_bill, BILL_STAGES, get_current_stage,
                                  days_to_vote, get_bill_progress_pct)
from engine.mp_generator import calculate_bill_support
from engine.game_state import get_coalition_seat_total
from engine.lobby_engine import LOBBY_ACTIONS, execute_action

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def _load_laws():
    with open(os.path.join(DATA_DIR, "laws.json"), encoding="utf-8") as f:
        return json.load(f)


def render(state):
    inject_css()
    st.markdown("## 🏛️ Parliament")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏛️ Chamber",
        "📜 Active Bills",
        "📋 Propose Bill",
        "🎭 Procedural Moves",
        "✅ Laws & History"
    ])
    with tab1:
        _render_chamber(state)
    with tab2:
        _render_active_bills(state)
    with tab3:
        _render_propose_bill(state)
    with tab4:
        _render_procedural(state)
    with tab5:
        _render_law_history(state)


def _render_procedural(state):
    """Special parliamentary procedural moves."""
    from engine.parliament_actions import PROCEDURAL_ACTIONS, execute_procedural

    cal = state["calendar"]
    pc = state["national"]["political_capital"]
    ap = cal["action_points"]

    st.markdown("### 🎭 Procedural Moves")
    st.caption("Special parliamentary actions outside normal bill flow. Use them strategically — they can save a coalition or sink an opponent.")

    by_category = {}
    for aid, action in PROCEDURAL_ACTIONS.items():
        cat = action.get("category", "other")
        by_category.setdefault(cat, []).append((aid, action))

    cat_labels = {
        "coalition": "🤝 Coalition Management",
        "agenda": "📋 Agenda Control",
        "obstruction": "🛑 Block the Opposition",
        "cabinet": "👔 Cabinet Powers",
        "media": "📺 Media & Authority",
        "reform": "⚖️ Reform Actions",
    }

    for cat, items in by_category.items():
        st.markdown(f"#### {cat_labels.get(cat, cat.title())}")
        cols = st.columns(2)
        for i, (aid, action) in enumerate(items):
            col = cols[i % 2]
            with col:
                can = ap >= action["ap_cost"] and pc >= action["pc_cost"]
                color = "#3B82F6" if can else "#475569"
                safe_html(f"""
                <div style="background:#1e293b;border:1px solid {color};border-radius:8px;padding:0.75rem;margin-bottom:0.5rem;min-height:115px">
                  <div style="font-weight:bold;color:#f1f5f9;font-size:0.95rem">{action['icon']} {action['name']}</div>
                  <div style="font-size:0.82rem;color:#cbd5e1;margin-top:4px;line-height:1.4">{action['description']}</div>
                  <div style="font-size:0.75rem;color:#94a3b8;margin-top:6px">⚡ {action['ap_cost']} AP · 💼 {action['pc_cost']} PC</div>
                </div>
                """)
                if st.button("Execute", key=f"proc_{aid}", disabled=not can, use_container_width=True):
                    ok, msg = execute_procedural(state, aid)
                    if ok:
                        st.session_state["game"] = state
                        st.rerun()


def _render_chamber(state):
    parties = state["parties"]
    coalition = state["parliament"]["coalition"]
    majority = state["parliament"]["majority"]
    coalition_seats = get_coalition_seat_total(state)

    margin = coalition_seats - majority
    margin_color = "#22C55E" if margin > 5 else ("#EAB308" if margin > 0 else "#EF4444")

    safe_html(f"""
    <div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:0.75rem 1rem;margin-bottom:1rem">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;color:#f1f5f9">
        <div style="color:#f1f5f9"><strong style="color:#f1f5f9">Coalition: {coalition_seats}/240</strong> · <span style="color:{margin_color};font-weight:bold">Majority margin: {margin:+d}</span></div>
        <div style="font-size:0.85rem;color:#cbd5e1">Speaker: {state['parliament']['speaker']}</div>
      </div>
    </div>
    """)

    if HAS_PLOTLY:
        _render_chamber_arc(state)
    else:
        _render_chamber_grid(state)

    st.markdown("---")
    _render_party_rows(state)


def _render_chamber_arc(state):
    parties = state["parties"]
    coalition = state["parliament"]["coalition"]
    sorted_parties = sorted(parties.items(), key=lambda x: x[1].get("ideology", {}).get("economic_left_right", 0))

    total_seats = 240
    angles = []
    colors = []
    labels = []

    seats_drawn = 0
    for party_id, party in sorted_parties:
        for _ in range(party["seats"]):
            angle = math.pi - math.pi * (seats_drawn / max(1, total_seats - 1))
            angles.append(angle)
            colors.append(PARTY_COLORS.get(party_id, "#64748b"))
            in_coalition = party_id in coalition
            border_label = f"{party['short']} ({'C' if in_coalition else 'O'})"
            labels.append(border_label)
            seats_drawn += 1

    rows = 8
    seats_per_row = math.ceil(total_seats / rows)
    xs = []
    ys = []
    for i in range(total_seats):
        row = i // seats_per_row
        col = i % seats_per_row
        radius = 0.35 + 0.08 * row
        angle = math.pi - math.pi * (col / max(1, seats_per_row - 1))
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        xs.append(x)
        ys.append(y)

    fig = go.Figure(go.Scatter(
        x=xs, y=ys, mode="markers",
        marker=dict(size=10, color=colors, line=dict(width=1, color="#0f172a")),
        text=labels, hovertemplate="%{text}<extra></extra>"
    ))
    fig.update_layout(
        height=320,
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.1, 1.1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, 1.0]),
        margin=dict(l=10, r=10, t=20, b=10),
        title=dict(text="Parliament Chamber (sorted left → right)", font=dict(color="#94a3b8", size=12))
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_chamber_grid(state):
    parties = state["parties"]
    coalition = state["parliament"]["coalition"]

    sorted_parties = sorted(parties.items(), key=lambda x: x[1].get("ideology", {}).get("economic_left_right", 0))
    seat_html = '<div style="display:flex;flex-wrap:wrap;gap:2px;justify-content:center;background:#0f172a;padding:1rem;border-radius:8px">'
    for party_id, party in sorted_parties:
        color = PARTY_COLORS.get(party_id, "#64748b")
        in_coalition = party_id in coalition
        for _ in range(party["seats"]):
            border = "2px solid white" if in_coalition else "1px solid #334155"
            seat_html += f'<div style="width:11px;height:18px;background:{color};border-radius:2px;border:{border};opacity:{0.95 if in_coalition else 0.6}"></div>'
    seat_html += "</div>"
    st.markdown(seat_html, unsafe_allow_html=True)


def _render_party_rows(state):
    parties = state["parties"]
    coalition = state["parliament"]["coalition"]

    for party_id, party in sorted(parties.items(), key=lambda x: -x[1]["seats"]):
        color = PARTY_COLORS.get(party_id, "#64748b")
        in_coalition = party_id in coalition
        loyalty = party.get("coalition_loyalty", 65) if in_coalition else None

        loyalty_html = ""
        if in_coalition and party_id != state["player_party"]:
            loy = loyalty
            loy_color = "#22C55E" if loy > 70 else ("#EAB308" if loy > 50 else "#EF4444")
            loyalty_html = f'<span style="color:{loy_color};margin-left:8px">Loyalty: {loy}%</span>'

        status_badge = '<span style="background:#1d4ed8;color:white;padding:2px 6px;border-radius:4px;font-size:0.7rem">COALITION</span>' if in_coalition else '<span style="background:#7f1d1d;color:white;padding:2px 6px;border-radius:4px;font-size:0.7rem">OPPOSITION</span>'

        safe_html(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:8px 10px;background:#1e293b;border-left:4px solid {color};border-radius:6px;margin-bottom:4px">
          <div style="font-weight:bold;min-width:50px">{party['short']}</div>
          <div style="flex:1">
            <div>{party['name']} <span style="color:#94a3b8;font-size:0.85rem">— {party['leader']}</span></div>
            <div style="font-size:0.78rem;color:#64748b">Poll: {party['poll']:.1f}% {loyalty_html}</div>
          </div>
          <div style="font-weight:bold;color:{color}">{party['seats']} seats</div>
          <div>{status_badge}</div>
        </div>
        """)


def _render_active_bills(state):
    bills = state.get("active_bills", [])
    if not bills:
        st.info("📭 No bills currently in progress. Go to **Propose Bill** to introduce one.")
        return

    st.markdown(f"### {len(bills)} Bill{'s' if len(bills) > 1 else ''} in Progress")

    for bill in bills:
        _render_bill_progress_card(state, bill)


def _render_bill_progress_card(state, bill):
    support = calculate_bill_support(state, bill)
    current_stage = get_current_stage(bill)
    progress = get_bill_progress_pct(bill)
    days_left = days_to_vote(bill)

    pct = support["pct"]
    majority = state["parliament"]["majority"]
    needed_pct = round(majority / 240 * 100, 1)

    if pct >= needed_pct + 5:
        status_color = "#22C55E"
        status_label = "✅ Likely PASS"
    elif pct >= needed_pct:
        status_color = "#84CC16"
        status_label = "✅ Slim PASS"
    elif pct >= needed_pct - 5:
        status_color = "#EAB308"
        status_label = "⚠️ Knife-edge"
    elif pct >= needed_pct - 15:
        status_color = "#F97316"
        status_label = "⚠️ Trailing"
    else:
        status_color = "#EF4444"
        status_label = "❌ Likely FAIL"

    safe_html(f"""
    <div style="background:#1e293b;border:2px solid #334155;border-radius:10px;padding:1rem;margin-bottom:1rem">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem">
        <div style="flex:1">
          <h4 style="margin:0;color:#f1f5f9">{bill['title']}</h4>
          <div style="font-size:0.82rem;color:#94a3b8">{bill['description'][:140]}</div>
        </div>
        <div style="text-align:right">
          <div style="background:{status_color};color:white;padding:4px 10px;border-radius:6px;font-weight:bold">{status_label}</div>
          <div style="font-size:0.75rem;color:#94a3b8;margin-top:4px">Vote in {days_left} day{'s' if days_left != 1 else ''}</div>
        </div>
      </div>
      <div style="margin:0.6rem 0">
        <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:#94a3b8">
          <span>{current_stage['icon']} Stage: {current_stage['label']} (Day {bill['stage_day']+1}/{current_stage['duration']})</span>
          <span>Bill progress: {progress}%</span>
        </div>
        <div style="height:6px;background:#0f172a;border-radius:3px;margin-top:4px;overflow:hidden">
          <div style="width:{progress}%;height:100%;background:linear-gradient(90deg,#3B82F6,#8B5CF6)"></div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:0.5rem">
        <div style="background:#14532d;color:#86EFAC;padding:8px;border-radius:6px;text-align:center">
          <div style="font-size:0.7rem">YES</div>
          <div style="font-size:1.2rem;font-weight:bold">{support['yes']}</div>
        </div>
        <div style="background:#7f1d1d;color:#FCA5A5;padding:8px;border-radius:6px;text-align:center">
          <div style="font-size:0.7rem">NO</div>
          <div style="font-size:1.2rem;font-weight:bold">{support['no']}</div>
        </div>
        <div style="background:#374151;color:#D1D5DB;padding:8px;border-radius:6px;text-align:center">
          <div style="font-size:0.7rem">UNDECIDED</div>
          <div style="font-size:1.2rem;font-weight:bold">{support['undecided']}</div>
        </div>
        <div style="background:#1f2937;color:#9CA3AF;padding:8px;border-radius:6px;text-align:center">
          <div style="font-size:0.7rem">ABSTAIN</div>
          <div style="font-size:1.2rem;font-weight:bold">{support['abstain']}</div>
        </div>
      </div>
      <div style="margin-top:0.6rem">
        <div style="display:flex;justify-content:space-between;font-size:0.78rem;color:#94a3b8">
          <span>Current support: <strong style="color:{status_color}">{pct}%</strong></span>
          <span>Needed: {needed_pct}% ({majority} votes)</span>
        </div>
        <div style="height:14px;background:#0f172a;border-radius:7px;margin-top:4px;overflow:hidden;position:relative">
          <div style="width:{pct}%;height:100%;background:{status_color}"></div>
          <div style="position:absolute;left:{needed_pct}%;top:-2px;width:2px;height:18px;background:#fbbf24"></div>
        </div>
      </div>
    </div>
    """)

    with st.expander(f"🎯 Lobbying actions for '{bill['title']}'"):
        _render_bill_lobby_actions(state, bill)

    with st.expander(f"👥 MP-by-MP support ({bill['title']})"):
        _render_mp_breakdown(state, bill)


def _render_bill_lobby_actions(state, bill):
    cal = state["calendar"]
    pc = state["national"]["political_capital"]
    bill_actions = ["lobby_committee", "media_offensive", "horse_trading"]

    cols = st.columns(len(bill_actions))
    for i, action_id in enumerate(bill_actions):
        action = LOBBY_ACTIONS[action_id]
        with cols[i]:
            can_afford = (cal["action_points"] >= action["ap_cost"] and pc >= action["pc_cost"])
            safe_html(f"""
            <div style="background:#0f172a;border:1px solid #334155;border-radius:6px;padding:0.5rem;min-height:90px">
              <div style="font-weight:bold">{action['icon']} {action['name']}</div>
              <div style="font-size:0.75rem;color:#94a3b8">{action['description']}</div>
              <div style="font-size:0.72rem;color:#64748b;margin-top:4px">⚡ {action['ap_cost']} AP · 💼 {action['pc_cost']} PC</div>
            </div>
            """)
            if st.button("Execute", key=f"act_{action_id}_{bill['id']}", disabled=not can_afford):
                ok, msg = execute_action(state, action_id, target_id=bill["id"])
                if ok:
                    st.session_state["game"] = state
                    st.rerun()
                else:
                    st.error(msg)


def _render_mp_breakdown(state, bill):
    coalition = state["parliament"]["coalition"]
    parties = state["parties"]

    party_breakdown = {}
    for mp in state["mps"]:
        intent = mp["vote_intentions"].get(bill["id"], "undecided")
        pid = mp["party"]
        party_breakdown.setdefault(pid, {"yes": 0, "no": 0, "undecided": 0, "abstain": 0})
        party_breakdown[pid][intent] += 1

    for party_id in sorted(parties.keys(), key=lambda x: -parties[x]["seats"]):
        if party_id not in party_breakdown:
            continue
        p = parties[party_id]
        b = party_breakdown[party_id]
        total = b["yes"] + b["no"] + b["undecided"] + b["abstain"]
        if total == 0:
            continue
        color = PARTY_COLORS.get(party_id, "#64748b")
        in_coal = party_id in coalition
        marker = "🤝" if in_coal else "⚔️"

        yes_pct = round(b["yes"]/total*100)
        no_pct = round(b["no"]/total*100)
        und_pct = round(b["undecided"]/total*100)
        abs_pct = 100 - yes_pct - no_pct - und_pct

        safe_html(f"""
        <div style="margin-bottom:8px">
          <div style="display:flex;justify-content:space-between;font-size:0.85rem">
            <span style="color:{color}">{marker} <strong>{p['short']}</strong> ({p['name']})</span>
            <span>YES {b['yes']} · NO {b['no']} · UND {b['undecided']} · ABS {b['abstain']}</span>
          </div>
          <div style="height:14px;border-radius:3px;overflow:hidden;display:flex;margin-top:2px">
            <div style="width:{yes_pct}%;background:#22C55E"></div>
            <div style="width:{no_pct}%;background:#EF4444"></div>
            <div style="width:{und_pct}%;background:#6B7280"></div>
            <div style="width:{abs_pct}%;background:#374151"></div>
          </div>
        </div>
        """)

    st.markdown("**🎯 Persuadable MPs** (sorted by who's most worth lobbying)")
    swayable = [m for m in state["mps"]
                 if m["vote_intentions"].get(bill["id"]) in ("undecided", "no", "abstain")]
    swayable.sort(key=lambda m: -m["persuadability"])
    for mp in swayable[:10]:
        intention = mp["vote_intentions"].get(bill["id"], "undecided")
        intent_emoji = {"yes":"✅","no":"❌","undecided":"❓","abstain":"⚪"}[intention]
        color = PARTY_COLORS.get(mp["party"], "#64748b")
        rel = mp["personal_relationship"]
        rel_color = "#22C55E" if rel > 60 else ("#EAB308" if rel > 40 else "#EF4444")

        col1, col2 = st.columns([4, 1])
        with col1:
            safe_html(f"""
            <div style="display:flex;align-items:center;gap:8px;padding:4px 8px;background:#0f172a;border-radius:4px">
              <span style="color:{color}">{intent_emoji}</span>
              <span style="flex:1"><strong>{mp['name']}</strong> <span style="color:{color};font-size:0.78rem">({state['parties'][mp['party']]['short']})</span></span>
              <span style="font-size:0.78rem">Persuade: {mp['persuadability']} · <span style="color:{rel_color}">Rel: {rel}</span></span>
            </div>
            """)
        with col2:
            cal = state["calendar"]
            pc = state["national"]["political_capital"]
            can = cal["action_points"] >= 1 and pc >= 1
            if st.button("🤝 Meet", key=f"meet_mp_{mp['id']}_{bill['id']}", disabled=not can):
                ok, msg = execute_action(state, "meet_mp", target_id=mp["id"])
                if ok:
                    st.session_state["game"] = state
                    st.rerun()


def _render_propose_bill(state):
    all_laws = _load_laws()
    parliament = state["parliament"]
    n = state["national"]
    pc = n["political_capital"]
    cal = state["calendar"]

    passed_ids = {l["id"] for l in parliament["passed_laws"]}
    active_ids = {b["id"] for b in state.get("active_bills", [])}
    available = [l for l in all_laws if l["id"] not in passed_ids and l["id"] not in active_ids]

    st.markdown(f"💼 **Political Capital: {pc}** · ⚡ **Action Points: {cal['action_points']}/{cal['max_action_points']}**")
    st.info("📋 Bills go through 5 stages: Drafting → Committee → First Reading → Debate → Final Vote (~14 days). Lobby during the process to improve your chances!")

    if len(state.get("active_bills", [])) >= 3:
        st.warning("⚠️ Maximum of 3 bills active at once. Wait for one to complete.")
        return

    categories = {}
    for law in available:
        cat = law.get("category", "other")
        categories.setdefault(cat, []).append(law)

    cat_icons = {
        "governance": "🏛️", "economy": "💰", "social": "🏥",
        "energy": "⚡", "defense": "🛡️", "foreign": "🌍"
    }

    for cat, laws in sorted(categories.items()):
        icon = cat_icons.get(cat, "📋")
        with st.expander(f"{icon} {cat.title()} ({len(laws)})"):
            for law in laws:
                cost = law.get("political_capital_cost", 8)
                can_afford = pc >= cost
                difficulty = law.get("parliament_difficulty", 50)
                diff_color = "#22C55E" if difficulty < 45 else ("#EAB308" if difficulty < 65 else "#EF4444")

                col1, col2 = st.columns([4, 1])
                with col1:
                    safe_html(f"""
                    <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.7rem;margin-bottom:0.5rem">
                      <div style="font-weight:bold">{law['title']}</div>
                      <div style="font-size:0.82rem;color:#94a3b8;margin-top:4px">{law['description'][:140]}</div>
                      <div style="margin-top:6px;font-size:0.78rem">
                        💼 {cost} PC · <span style="color:{diff_color}">Difficulty: {difficulty}%</span> · ⏱ ~14 days to vote
                      </div>
                    </div>
                    """)
                with col2:
                    st.write("")
                    if st.button("📜 Introduce", key=f"intro_{law['id']}", disabled=not can_afford):
                        ok, result = introduce_bill(state, law)
                        if ok:
                            st.session_state["game"] = state
                            st.success(f"Bill introduced: {law['title']}")
                            st.rerun()
                        else:
                            st.error(result)


def _render_law_history(state):
    parliament = state["parliament"]
    passed = parliament.get("passed_laws", [])
    failed = parliament.get("failed_bills", [])

    if passed:
        st.markdown(f"#### ✅ Passed Laws ({len(passed)})")
        for law in passed:
            vote = law.get("vote", {})
            st.markdown(f"- **{law['title']}** — Vote: {vote.get('yes','?')}-{vote.get('no','?')}")
    if failed:
        st.markdown(f"#### ❌ Failed Bills ({len(failed)})")
        for law in failed:
            vote = law.get("vote", {})
            st.markdown(f"- **{law['title']}** — Vote: {vote.get('yes','?')}-{vote.get('no','?')}")
    if not passed and not failed:
        st.info("No legislation completed yet.")
