import streamlit as st
from .styles import PARTY_COLORS, get_indicator_color, progress_bar_html, inject_css, safe_html


def render(state):
    inject_css()
    st.markdown("## 🗺️ Regional Overview — Republic of Pustinyakovo")

    regions = state["regions"]
    n = state["national"]

    _render_region_grid(regions, state)
    st.markdown("---")
    _render_region_detail(state)


def _render_region_grid(regions, state):
    st.markdown("#### Regional Status Map")
    cols = st.columns(4)

    region_list = list(regions.items())
    for i, (region_id, region) in enumerate(region_list):
        col = cols[i % 4]
        with col:
            _render_region_card(region_id, region, state)


def _render_region_card(region_id, region, state):
    pol = region.get("politics", {})
    econ = region.get("economy", {})
    coalition = state["parliament"]["coalition"]
    player_party = state["player_party"]

    unrest = pol.get("unrest", 50)
    corruption = pol.get("corruption", 50)
    unemployment = econ.get("unemployment", 15)

    unrest_color = get_indicator_color(100 - unrest)
    party_support = pol.get("party_support", {})
    top_party = max(party_support.items(), key=lambda x: x[1])[0] if party_support else "unknown"
    top_color = PARTY_COLORS.get(top_party, "#64748b")
    player_support = party_support.get(player_party, 0)
    player_color = get_indicator_color(player_support)

    type_icons = {
        "capital": "🏙️", "industrial": "🏭", "agricultural": "🌾",
        "border": "🛡️", "tourist": "🏖️", "rural": "⛰️",
        "minority": "👥", "mixed": "🚢"
    }
    icon = type_icons.get(region.get("type", ""), "📍")

    problems = region.get("problems", [])[:2]
    problems_str = ", ".join(p.replace("_", " ") for p in problems)

    safe_html(f"""
    <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.75rem;margin-bottom:0.75rem;min-height:160px">
      <div style="font-weight:bold;margin-bottom:4px">{icon} {region['name']}</div>
      <div style="font-size:0.75rem;color:#94a3b8">{region.get('type','').title()} · Pop: {region['population']:,}</div>
      <div style="margin-top:6px;font-size:0.8rem">
        <div>🔥 Unrest: <span style="color:{unrest_color}">{unrest}</span></div>
        <div>💼 Unemployed: {unemployment:.1f}%</div>
        <div>👤 Your support: <span style="color:{player_color}">{player_support}%</span></div>
        <div style="margin-top:4px;color:#64748b;font-size:0.72rem">{problems_str}</div>
      </div>
    </div>
    """)


def _render_region_detail(state):
    regions = state["regions"]
    region_names = {rid: r["name"] for rid, r in regions.items()}

    selected = st.selectbox("Select region for details:", options=list(regions.keys()),
                             format_func=lambda x: region_names[x])

    if not selected:
        return

    region = regions[selected]
    pol = region.get("politics", {})
    econ = region.get("economy", {})
    soc = region.get("social", {})
    coalition = state["parliament"]["coalition"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Economic Profile**")
        for label, key in [("Unemployment", "unemployment"), ("Poverty", "poverty"),
                             ("GDP per capita (rel.)", "gdp_per_capita")]:
            val = econ.get(key, 0)
            color = get_indicator_color(val if key == "gdp_per_capita" else 100 - val)
            suffix = "%" if key != "gdp_per_capita" else ""
            safe_html(f"""
            <div style="display:flex;justify-content:space-between;padding:4px 8px;background:#1e293b;border-radius:4px;margin-bottom:3px">
              <span style="color:#94a3b8">{label}</span>
              <span style="color:{color};font-weight:bold">{val:.1f}{suffix}</span>
            </div>
            """)

        sectors = econ.get("main_sectors", [])
        st.markdown(f"**Key sectors:** {', '.join(sectors)}")

    with col2:
        st.markdown("**Social Indicators**")
        for label, key in [("Education", "education"), ("Healthcare", "healthcare"),
                             ("Infrastructure", "infrastructure")]:
            val = soc.get(key, 50)
            color = get_indicator_color(val)
            st.markdown(progress_bar_html(val, color=color, label=label), unsafe_allow_html=True)

        st.markdown("**Political**")
        for label, key, inv in [("Unrest", "unrest", True), ("Corruption", "corruption", True),
                                   ("Protest Potential", "protest_potential", True)]:
            val = pol.get(key, 50)
            color = get_indicator_color(val, inverse=inv)
            st.markdown(progress_bar_html(val, color=color, label=label), unsafe_allow_html=True)

    with col3:
        st.markdown("**Party Support in Region**")
        party_support = pol.get("party_support", {})
        for party_id, support in sorted(party_support.items(), key=lambda x: -x[1]):
            if party_id == "other":
                continue
            if party_id not in state["parties"]:
                continue
            party = state["parties"][party_id]
            color = PARTY_COLORS.get(party_id, "#64748b")
            in_coal = party_id in coalition
            marker = "🤝" if in_coal else ""
            safe_html(f"""
            <div style="margin-bottom:4px">
              <div style="display:flex;justify-content:space-between;font-size:0.85rem">
                <span style="color:{color}">{marker} {party['short']}</span>
                <span>{support}%</span>
              </div>
              <div style="height:6px;background:#334155;border-radius:3px;overflow:hidden">
                <div style="width:{support}%;height:100%;background:{color}"></div>
              </div>
            </div>
            """)

    st.markdown("**Problems:**")
    for prob in region.get("problems", []):
        st.markdown(f"• {prob.replace('_', ' ').title()}")

    st.markdown("---")
    st.markdown("**🔧 Regional Actions** (costs Political Capital)")
    _render_region_actions(state, selected, region)


def _render_region_actions(state, region_id, region):
    n = state["national"]
    pc = n["political_capital"]

    actions = [
        {
            "id": f"invest_{region_id}",
            "name": "💰 Infrastructure Investment",
            "cost": 8,
            "desc": "Fund infrastructure projects. Reduces unrest, improves support.",
            "effects_national": {"budget_deficit": 0.2, "political_capital": -8},
            "effects_region": {"infrastructure": 8, "unrest": -8, "party_support_da": 5}
        },
        {
            "id": f"anticorrupt_{region_id}",
            "name": "🔍 Anti-Corruption Audit",
            "cost": 6,
            "desc": "Deploy anti-corruption teams. Improves rule of law locally.",
            "effects_national": {"corruption": -3, "political_capital": -6, "rule_of_law": 3},
            "effects_region": {"corruption": -10, "unrest": -3, "party_support_da": 3}
        },
        {
            "id": f"jobs_{region_id}",
            "name": "🏭 Jobs Program",
            "cost": 10,
            "desc": "Emergency employment program. Reduces unemployment and unrest.",
            "effects_national": {"budget_deficit": 0.3, "unemployment": -0.5, "political_capital": -10},
            "effects_region": {"unemployment": -3, "unrest": -10, "party_support_da": 8}
        },
    ]

    cols = st.columns(3)
    for i, action in enumerate(actions):
        with cols[i]:
            can_afford = pc >= action["cost"]
            safe_html(f"""
            <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.75rem;margin-bottom:0.5rem">
              <div style="font-weight:bold">{action['name']}</div>
              <div style="font-size:0.8rem;color:#94a3b8">{action['desc']}</div>
              <div style="font-size:0.75rem;color:#64748b">Cost: {action['cost']} PC</div>
            </div>
            """)

            if st.button("Enact", key=f"reg_act_{action['id']}", disabled=not can_afford):
                from engine.game_state import apply_national_effects, apply_region_effects, add_news
                apply_national_effects(state, action["effects_national"])
                apply_region_effects(state, {region_id: action["effects_region"]})
                add_news(state, "🗺️",
                          f"Regional action in {region['name']}: {action['name'].split(' ', 1)[1]}",
                          "political")
                st.session_state["game"] = state
                st.rerun()
