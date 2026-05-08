import streamlit as st
from .styles import inject_css, get_indicator_color, safe_html
from engine.game_state import add_news


def render(state):
    inject_css()
    st.markdown("## 📺 Media & Public Opinion")

    tab1, tab2, tab3 = st.tabs(["📰 News Archive", "🗣️ Media Actions", "👥 Voter Groups"])

    with tab1:
        _render_news_archive(state)

    with tab2:
        _render_media_actions(state)

    with tab3:
        _render_voter_groups(state)


def _render_news_archive(state):
    news = state.get("news", [])

    type_filter = st.selectbox("Filter by type:", ["All", "political", "economic", "corruption",
                                                     "social", "security", "foreign_policy", "media"])

    if type_filter == "All":
        filtered = news
    else:
        filtered = [n for n in news if n.get("type", "") == type_filter]

    st.markdown(f"*Showing {len(filtered)} items*")

    border_colors = {
        "economic": "#D97706", "political": "#3B82F6",
        "corruption": "#EF4444", "social": "#8B5CF6",
        "security": "#6B7280", "foreign": "#0EA5E9",
        "foreign_policy": "#0EA5E9", "environmental": "#16A34A",
        "media": "#F59E0B", "general": "#475569"
    }

    for item in filtered:
        color = border_colors.get(item.get("type", ""), "#475569")
        safe_html(f"""
        <div style="border-left:4px solid {color};padding:0.5rem 0.75rem;margin-bottom:0.4rem;background:#0f172a;border-radius:4px">
          <span style="color:#64748b;font-size:0.75rem">{item.get('month','')}</span>
          <span style="margin-left:8px">{item.get('icon','')} {item.get('text','')}</span>
        </div>
        """)


def _render_media_actions(state):
    n = state["national"]
    pc = n["political_capital"]

    st.markdown(f"**Political Capital: {pc}**")
    st.markdown("*Use media strategically to shape the narrative and influence public opinion.*")

    media_actions = [
        {
            "id": "press_conference",
            "name": "🎤 Hold Press Conference",
            "cost": 3,
            "desc": "Address media directly. Boosts trust if economy is doing well.",
            "effects": {"political_capital": -3, "public_trust": 4, "media_freedom": 1}
        },
        {
            "id": "media_campaign",
            "name": "📢 Launch Media Campaign",
            "cost": 8,
            "desc": "Promote government achievements. Boosts polls.",
            "effects": {"political_capital": -8, "public_trust": 6}
        },
        {
            "id": "anti_corruption_announcement",
            "name": "🔍 High-Profile Anti-Corruption Statement",
            "cost": 5,
            "desc": "Public commitment to fight corruption. Boosts trust and EU relations.",
            "effects": {"political_capital": -5, "corruption": -4, "public_trust": 5, "eu_relations": 4}
        },
        {
            "id": "economic_statement",
            "name": "💰 Economic Progress Statement",
            "cost": 4,
            "desc": "Highlight economic achievements. More effective when economy is actually good.",
            "effects_conditional": True,
            "effects": {"political_capital": -4, "public_trust": 5, "business_confidence": 4}
        },
        {
            "id": "eu_unity_statement",
            "name": "🇪🇺 European Unity Statement",
            "cost": 4,
            "desc": "Reinforce pro-EU stance. Boosts EU relations, may anger nationalists.",
            "effects": {"political_capital": -4, "eu_relations": 6, "public_trust": 2}
        },
        {
            "id": "national_address",
            "name": "📺 National Television Address",
            "cost": 10,
            "desc": "Address the nation directly. Major trust boost but expensive.",
            "effects": {"political_capital": -10, "public_trust": 10, "government_stability": 5}
        },
        {
            "id": "security_briefing",
            "name": "🛡️ Security Briefing to Public",
            "cost": 5,
            "desc": "Reassure public on security situation. Reduces social tension.",
            "effects": {"political_capital": -5, "social_tension": -6, "security_risk": -3, "public_trust": 3}
        },
    ]

    cols = st.columns(2)
    for i, action in enumerate(media_actions):
        col = cols[i % 2]
        with col:
            can_afford = pc >= action["cost"]
            safe_html(f"""
            <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.75rem;margin-bottom:0.5rem">
              <div style="font-weight:bold">{action['name']} — {action['cost']} PC</div>
              <div style="font-size:0.82rem;color:#94a3b8">{action['desc']}</div>
            </div>
            """)

            if st.button("Launch", key=f"media_{action['id']}", disabled=not can_afford):
                from engine.game_state import apply_national_effects
                apply_national_effects(state, action["effects"])
                add_news(state, "📺", f"Government communication: {action['name'].split(' ', 1)[1]}", "media")
                st.session_state["game"] = state
                st.rerun()


def _render_voter_groups(state):
    voter_groups = state.get("voter_groups", {})
    parties = state["parties"]

    st.markdown("*Each voter group has different priorities and responds differently to your policies.*")

    for group_id, group in voter_groups.items():
        size = group.get("size", 10)
        turnout = group.get("base_turnout", 50)
        protest = group.get("protest_likelihood", 40)
        volatility = group.get("volatility", 50)

        top_parties = sorted(group.get("party_affinity", {}).items(), key=lambda x: -x[1])[:2]
        top_party_names = ", ".join(
            f"{parties[pid]['short']} ({int(v*100)}%)" for pid, v in top_parties if pid in parties
        )

        priorities = group.get("priorities", [])[:3]

        protest_color = get_indicator_color(100 - protest)
        volatility_color = get_indicator_color(100 - volatility)

        with st.expander(f"👥 **{group['name']}** — {size}% of electorate"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Base Turnout:** {turnout}%")
                st.markdown(f"**Protest Risk:** <span style='color:{protest_color}'>{protest}%</span>", unsafe_allow_html=True)
                st.markdown(f"**Volatility:** <span style='color:{volatility_color}'>{volatility}%</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"**Affinities:** {top_party_names}")
                st.markdown(f"**Priorities:** {', '.join(p.replace('_',' ').title() for p in priorities)}")
