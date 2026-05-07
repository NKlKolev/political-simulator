"""Top HUD - persistent header rendered on every game page."""
import textwrap
import streamlit as st
from .styles import PARTY_COLORS, get_indicator_color
from engine.calendar_engine import format_date
from engine.game_state import get_days_to_election, get_coalition_seat_total
from engine.bill_engine import calculate_bill_support, days_to_vote, get_current_stage
from engine.lobby_engine import LOBBY_ACTIONS, execute_action
from engine.turn_engine import advance_day_turn, advance_multiple_days


def _html(s):
    """Render HTML stripped of indentation so markdown doesn't treat it as code."""
    cleaned = textwrap.dedent(s).strip()
    cleaned = " ".join(line.strip() for line in cleaned.splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def render_hud(state):
    n = state["national"]
    cal = state["calendar"]
    player = state["parties"][state["player_party"]]
    ap = cal["action_points"]
    max_ap = cal["max_action_points"]
    pc = n["political_capital"]
    days_left = get_days_to_election(state)

    ap_color = "#22C55E" if ap >= 3 else ("#FBBF24" if ap >= 1 else "#EF4444")
    pc_color = "#22C55E" if pc >= 30 else ("#FBBF24" if pc >= 15 else "#EF4444")
    trust_color = get_indicator_color(n["public_trust"])
    stab_color = get_indicator_color(n["government_stability"])
    poll_color = "#22C55E" if player["poll"] >= 30 else ("#FBBF24" if player["poll"] >= 25 else "#EF4444")

    coalition_seats = get_coalition_seat_total(state)
    margin = coalition_seats - state["parliament"]["majority"]
    margin_color = "#22C55E" if margin > 5 else ("#FBBF24" if margin > 0 else "#EF4444")

    events_count = len(state.get("active_events", []))
    bills_count = len(state.get("active_bills", []))

    event_badge = f'<span style="background:#DC2626;color:white;padding:2px 8px;border-radius:10px;margin-left:6px;font-size:0.8rem;font-weight:bold">🚨 {events_count}</span>' if events_count > 0 else ""
    bills_badge = f'<span style="background:#3B82F6;color:white;padding:2px 8px;border-radius:10px;margin-left:6px;font-size:0.8rem;font-weight:bold">📜 {bills_count}</span>' if bills_count > 0 else ""

    inflation_color = "#EF4444" if n["inflation"] > 7 else "#FBBF24" if n["inflation"] > 4 else "#22C55E"
    unemp_color = "#EF4444" if n["unemployment"] > 16 else "#FBBF24" if n["unemployment"] > 10 else "#22C55E"
    corr_color = "#EF4444" if n["corruption"] > 65 else "#FBBF24" if n["corruption"] > 50 else "#22C55E"
    tension_color = "#EF4444" if n["social_tension"] > 65 else "#FBBF24" if n["social_tension"] > 50 else "#22C55E"
    gdp_color = "#22C55E" if n["gdp_growth"] > 0 else "#EF4444"

    hud = (
        '<div style="background:linear-gradient(180deg,#1e3a5f,#0f172a);border:1px solid #3B82F6;border-radius:10px;padding:10px 14px;margin-bottom:10px">'
        '<div style="display:grid;grid-template-columns: 1.2fr 0.7fr 0.7fr 0.7fr 0.7fr 0.7fr 0.9fr;gap:10px;align-items:center">'
        '<div style="border-right:1px solid #334155;padding-right:10px">'
        '<div style="color:#93c5fd;font-size:0.68rem;text-transform:uppercase;letter-spacing:0.5px">📅 Date</div>'
        f'<div style="color:#f1f5f9;font-weight:bold;font-size:1rem;line-height:1.1">{format_date(cal["date"])}</div>'
        f'<div style="color:#cbd5e1;font-size:0.72rem">Day {state["turn"]} · {days_left}d to election</div>'
        '</div>'
        f'<div style="text-align:center;background:#0f172a;border:1px solid {ap_color}40;border-radius:6px;padding:4px 6px">'
        f'<div style="color:{ap_color};font-size:0.68rem;text-transform:uppercase;font-weight:bold">⚡ Action Points</div>'
        f'<div style="color:{ap_color};font-size:1.4rem;font-weight:bold;line-height:1.1">{ap}<span style="font-size:0.9rem;color:#64748b">/{max_ap}</span></div>'
        '</div>'
        f'<div style="text-align:center;background:#0f172a;border:1px solid {pc_color}40;border-radius:6px;padding:4px 6px">'
        f'<div style="color:{pc_color};font-size:0.68rem;text-transform:uppercase;font-weight:bold">💼 Pol. Capital</div>'
        f'<div style="color:{pc_color};font-size:1.4rem;font-weight:bold;line-height:1.1">{pc}</div>'
        '</div>'
        '<div style="text-align:center">'
        '<div style="color:#94a3b8;font-size:0.68rem;text-transform:uppercase">🤝 Trust</div>'
        f'<div style="color:{trust_color};font-size:1.3rem;font-weight:bold;line-height:1.1">{n["public_trust"]}%</div>'
        '</div>'
        '<div style="text-align:center">'
        '<div style="color:#94a3b8;font-size:0.68rem;text-transform:uppercase">🏛️ Stability</div>'
        f'<div style="color:{stab_color};font-size:1.3rem;font-weight:bold;line-height:1.1">{n["government_stability"]}%</div>'
        '</div>'
        '<div style="text-align:center">'
        '<div style="color:#94a3b8;font-size:0.68rem;text-transform:uppercase">📊 DA Poll</div>'
        f'<div style="color:{poll_color};font-size:1.3rem;font-weight:bold;line-height:1.1">{player["poll"]:.1f}%</div>'
        '</div>'
        '<div style="text-align:center;border-left:1px solid #334155;padding-left:10px">'
        '<div style="color:#94a3b8;font-size:0.68rem;text-transform:uppercase">Coalition / Status</div>'
        f'<div style="font-size:0.95rem;font-weight:bold;line-height:1.1"><span style="color:#f1f5f9">{coalition_seats}/240</span> <span style="color:{margin_color}">({margin:+d})</span></div>'
        f'<div style="font-size:0.75rem;line-height:1.2">{event_badge}{bills_badge}</div>'
        '</div>'
        '</div>'
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr;gap:6px;margin-top:8px;padding-top:8px;border-top:1px solid #334155">'
        f'<div style="text-align:center;font-size:0.78rem"><span style="color:#94a3b8">📈 GDP </span><span style="color:{gdp_color};font-weight:bold">{n["gdp_growth"]:+.1f}%</span></div>'
        f'<div style="text-align:center;font-size:0.78rem"><span style="color:#94a3b8">🔥 Inflation </span><span style="color:{inflation_color};font-weight:bold">{n["inflation"]:.1f}%</span></div>'
        f'<div style="text-align:center;font-size:0.78rem"><span style="color:#94a3b8">😔 Unemploy </span><span style="color:{unemp_color};font-weight:bold">{n["unemployment"]:.1f}%</span></div>'
        f'<div style="text-align:center;font-size:0.78rem"><span style="color:#94a3b8">🔍 Corruption </span><span style="color:{corr_color};font-weight:bold">{n["corruption"]}</span></div>'
        f'<div style="text-align:center;font-size:0.78rem"><span style="color:#94a3b8">😡 Tension </span><span style="color:{tension_color};font-weight:bold">{n["social_tension"]}</span></div>'
        '</div>'
        '</div>'
    )
    st.markdown(hud, unsafe_allow_html=True)

    if events_count > 0:
        st.error(f"🚨 **{events_count} crisis event{'s' if events_count > 1 else ''} unresolved** — go to Events tab. You cannot advance the day until they're handled.")

    _render_quick_action_bar(state)
    _render_active_bills_strip(state)


def _render_quick_action_bar(state):
    cal = state["calendar"]
    pc = state["national"]["political_capital"]
    ap = cal["action_points"]

    quick_actions = [
        ("press_conference",       "🎤", "Press Conf"),
        ("anti_corruption_pledge", "🔍", "Anti-Corrupt"),
        ("rally_supporters",       "🚩", "Rally"),
        ("diplomatic_call",        "🇪🇺", "EU Call"),
        ("national_address",       "📺", "TV Address"),
    ]

    cols = st.columns([1, 1, 1, 1, 1, 1.2, 1.2])

    for i, (action_id, icon, short_label) in enumerate(quick_actions):
        action = LOBBY_ACTIONS[action_id]
        with cols[i]:
            can = ap >= action["ap_cost"] and pc >= action["pc_cost"]
            label = f"{icon} {short_label} ({action['ap_cost']}⚡{action['pc_cost']}💼)"
            if st.button(label, key=f"hud_qa_{action_id}",
                          use_container_width=True, disabled=not can,
                          help=action["description"]):
                ok, msg = execute_action(state, action_id)
                if ok:
                    st.session_state["game"] = state
                    st.rerun()

    with cols[5]:
        if st.button("⏭️ Next Day", key="hud_next_day", use_container_width=True, type="primary"):
            if state.get("active_events"):
                st.warning("Resolve crisis first!")
            else:
                updated = advance_day_turn(state)
                st.session_state["game"] = updated
                st.rerun()
    with cols[6]:
        if st.button("⏩ +7 Days", key="hud_next_week", use_container_width=True):
            if state.get("active_events"):
                st.warning("Resolve crisis first!")
            else:
                updated = advance_multiple_days(state, 7)
                st.session_state["game"] = updated
                st.rerun()


def _render_active_bills_strip(state):
    bills = state.get("active_bills", [])
    if not bills:
        return
    majority = state["parliament"]["majority"]
    need_pct = round(majority / 240 * 100, 1)

    st.markdown('<div style="color:#cbd5e1;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;margin:6px 0 4px">📜 ACTIVE BILLS — LIVE TRACKING</div>', unsafe_allow_html=True)

    for bill in bills:
        support = calculate_bill_support(state, bill)
        stage = get_current_stage(bill)
        d_left = days_to_vote(bill)
        pct = support["pct"]

        if pct >= need_pct + 5:
            color = "#22C55E"; status = "✅ PASS"
        elif pct >= need_pct:
            color = "#84CC16"; status = "✅ Slim"
        elif pct >= need_pct - 5:
            color = "#EAB308"; status = "⚠️ Edge"
        elif pct >= need_pct - 15:
            color = "#F97316"; status = "⚠️ Behind"
        else:
            color = "#EF4444"; status = "❌ FAIL"

        bill_html = (
            f'<div style="background:#1e293b;border-left:4px solid {color};border-radius:6px;padding:8px 12px;margin-bottom:4px">'
            '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px">'
            '<div style="flex:1;min-width:200px">'
            f'<div style="color:#f1f5f9;font-weight:bold;font-size:0.9rem">{bill["title"]}</div>'
            f'<div style="color:#94a3b8;font-size:0.75rem">{stage["icon"]} {stage["label"]} · 🗳️ in {d_left} day{"s" if d_left != 1 else ""}</div>'
            '</div>'
            '<div style="display:flex;gap:6px;flex-wrap:wrap">'
            f'<span style="background:#14532d;color:#86EFAC;padding:2px 8px;border-radius:4px;font-size:0.78rem">YES <strong>{support["yes"]}</strong></span>'
            f'<span style="background:#7f1d1d;color:#FCA5A5;padding:2px 8px;border-radius:4px;font-size:0.78rem">NO <strong>{support["no"]}</strong></span>'
            f'<span style="background:#374151;color:#D1D5DB;padding:2px 8px;border-radius:4px;font-size:0.78rem">UND <strong>{support["undecided"]}</strong></span>'
            f'<span style="background:{color}30;color:{color};padding:2px 10px;border-radius:4px;font-size:0.78rem;font-weight:bold;border:1px solid {color}">{pct}% {status}</span>'
            '</div>'
            '</div>'
            '<div style="height:6px;background:#0f172a;border-radius:3px;margin-top:6px;overflow:hidden;position:relative">'
            f'<div style="width:{pct}%;height:100%;background:{color}"></div>'
            f'<div style="position:absolute;left:{need_pct}%;top:-2px;width:2px;height:10px;background:#fbbf24"></div>'
            '</div>'
            '</div>'
        )
        st.markdown(bill_html, unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
