import streamlit as st
from .styles import PARTY_COLORS, get_indicator_color, inject_css, safe_html


def render(state):
    inject_css()
    st.markdown("## 🏛️ Cabinet & Government")

    cabinet = state["cabinet"]
    parties = state["parties"]
    n = state["national"]

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Cabinet Members")
        for ministry_id, minister in cabinet.items():
            _render_minister_card(minister, parties)

    with col2:
        st.markdown("### Cabinet Health")
        _render_cabinet_health(cabinet, n)
        st.markdown("---")
        _render_reshuffle_options(state)


def _render_minister_card(minister, parties):
    party_id = minister.get("party", "")
    party_color = PARTY_COLORS.get(party_id, "#64748b")
    party = parties.get(party_id, {})
    party_short = party.get("short", "?")

    comp = minister.get("competence", 60)
    loyalty = minister.get("loyalty", 65)
    corruption_risk = minister.get("corruption_risk", 30)

    comp_color = get_indicator_color(comp)
    loyalty_color = get_indicator_color(loyalty)
    risk_color = get_indicator_color(100 - corruption_risk)

    icon = minister.get("icon", "👤")

    safe_html(f"""
    <div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:0.9rem;margin-bottom:0.6rem">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div style="font-size:1.1rem;font-weight:bold">{icon} {minister.get('name','Unknown')}</div>
          <div style="color:#94a3b8;font-size:0.85rem">{minister.get('ministry','')}</div>
          <div style="margin-top:2px">
            <span style="background:{party_color}22;color:{party_color};padding:2px 6px;border-radius:4px;font-size:0.75rem">{party_short}</span>
          </div>
        </div>
        <div style="text-align:right;font-size:0.82rem">
          <div>Competence: <span style="color:{comp_color}">{comp}</span></div>
          <div>Loyalty: <span style="color:{loyalty_color}">{loyalty}</span></div>
          <div>Scandal Risk: <span style="color:{risk_color}">{corruption_risk}</span></div>
        </div>
      </div>
      <div style="font-size:0.8rem;color:#64748b;margin-top:6px">{minister.get('description','')[:100]}...</div>
    </div>
    """)


def _render_cabinet_health(cabinet, n):
    total_comp = sum(m.get("competence", 60) for m in cabinet.values())
    avg_comp = total_comp / max(1, len(cabinet))

    total_loyalty = sum(m.get("loyalty", 65) for m in cabinet.values())
    avg_loyalty = total_loyalty / max(1, len(cabinet))

    high_risk = [m["name"] for m in cabinet.values() if m.get("corruption_risk", 0) > 55]

    comp_color = get_indicator_color(avg_comp)
    loyalty_color = get_indicator_color(avg_loyalty)

    safe_html(f"""
    <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.8rem">
      <div style="margin-bottom:6px">
        Avg. Competence: <span style="color:{comp_color};font-weight:bold">{avg_comp:.0f}</span>
      </div>
      <div style="margin-bottom:6px">
        Avg. Loyalty: <span style="color:{loyalty_color};font-weight:bold">{avg_loyalty:.0f}</span>
      </div>
    """)

    if high_risk:
        st.markdown(f"⚠️ **High scandal risk:** {', '.join(high_risk)}")
    else:
        st.markdown("✅ No ministers at critical scandal risk.")

    st.markdown("</div>", unsafe_allow_html=True)

    if avg_loyalty < 55:
        st.warning("⚠️ Cabinet loyalty is low. Risk of ministerial defection.")
    if avg_comp < 50:
        st.error("❌ Cabinet average competence is low. Policy implementation suffering.")


def _render_reshuffle_options(state):
    st.markdown("### 🔄 Cabinet Actions")
    n = state["national"]
    pc = n["political_capital"]

    st.markdown(f"*Political Capital: {pc}*")

    actions = [
        {
            "id": "rally_cabinet",
            "name": "📣 Rally Cabinet Loyalty",
            "cost": 5,
            "desc": "Hold cabinet retreat to boost loyalty and cohesion.",
            "effects": {"political_capital": -5, "coalition_stability": 8, "government_stability": 3}
        },
        {
            "id": "anti_corruption_pledge",
            "name": "🔍 Cabinet Anti-Corruption Pledge",
            "cost": 4,
            "desc": "Require all ministers to sign asset declaration.",
            "effects": {"political_capital": -4, "corruption": -4, "public_trust": 5, "eu_relations": 3}
        },
        {
            "id": "policy_coordination",
            "name": "📋 Policy Coordination Meeting",
            "cost": 3,
            "desc": "Align cabinet on key priorities for the coming months.",
            "effects": {"political_capital": -3, "government_stability": 5, "democratic_quality": 2}
        },
    ]

    for action in actions:
        can_afford = pc >= action["cost"]
        if st.button(f"{action['name']} (cost: {action['cost']} PC)",
                      key=f"cab_act_{action['id']}", disabled=not can_afford):
            from engine.game_state import apply_national_effects, add_news
            apply_national_effects(state, action["effects"])
            add_news(state, "🏛️", f"Cabinet action: {action['name'].split(' ', 1)[1]}", "political")
            st.session_state["game"] = state
            st.rerun()
