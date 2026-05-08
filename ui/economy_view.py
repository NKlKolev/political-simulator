import streamlit as st
from .styles import get_indicator_color, inject_css, safe_html
from engine.economy_engine import get_economic_summary

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def render(state):
    inject_css()
    st.markdown("## 💰 Economic Dashboard")

    n = state["national"]
    st.markdown(f"*{get_economic_summary(state)}*")

    tab1, tab2, tab3 = st.tabs(["📊 Indicators", "📈 Trends", "🔧 Actions"])

    with tab1:
        _render_indicators(n)

    with tab2:
        _render_trends(state)

    with tab3:
        _render_actions(state)


def _render_indicators(n):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Macroeconomic")
        metrics = [
            ("GDP Growth", f"{n['gdp_growth']:+.1f}%", n["gdp_growth"] > 0),
            ("Inflation", f"{n['inflation']:.1f}%", n["inflation"] < 5),
            ("Unemployment", f"{n['unemployment']:.1f}%", n["unemployment"] < 10),
            ("Public Debt", f"{n['public_debt']:.1f}% GDP", n["public_debt"] < 60),
            ("Budget Deficit", f"{n['budget_deficit']:.1f}% GDP", n["budget_deficit"] < 3),
        ]
        for label, value, is_good in metrics:
            color = "#22C55E" if is_good else "#EF4444"
            safe_html(f"""
            <div style="display:flex;justify-content:space-between;padding:6px 10px;background:#1e293b;border-radius:6px;margin-bottom:4px">
              <span style="color:#e2e8f0">{label}</span>
              <span style="color:{color};font-weight:bold">{value}</span>
            </div>
            """)

    with col2:
        st.markdown("#### Business & Investment")
        inv_metrics = [
            ("Business Confidence", n["business_confidence"], False),
            ("Foreign Investment", n["foreign_investment"], False),
            ("Energy Security", n["energy_security"], False),
            ("EU Relations", n["eu_relations"], False),
        ]
        for label, val, inv in inv_metrics:
            color = get_indicator_color(val, inverse=inv)
            safe_html(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 10px;background:#1e293b;border-radius:6px;margin-bottom:4px">
              <span style="color:#e2e8f0">{label}</span>
              <div style="display:flex;align-items:center;gap:8px">
                <div style="width:80px;height:8px;background:#334155;border-radius:4px;overflow:hidden">
                  <div style="width:{val}%;height:100%;background:{color}"></div>
                </div>
                <span style="color:{color};font-weight:bold;min-width:30px;text-align:right">{val}</span>
              </div>
            </div>
            """)

    st.markdown("---")
    st.markdown("#### ⚠️ Risk Assessment")

    risks = []
    if n["inflation"] > 9:
        risks.append(("🔥 High Inflation", f"{n['inflation']:.1f}%", "Reducing purchasing power. Social tension rising."))
    if n["public_debt"] > 85:
        risks.append(("💸 Debt Crisis Risk", f"{n['public_debt']:.1f}%", "Debt above sustainable levels. Credit rating at risk."))
    if n["gdp_growth"] < 0:
        risks.append(("📉 Recession", f"{n['gdp_growth']:.1f}%", "Economy contracting. Unemployment rising."))
    if n["budget_deficit"] > 6:
        risks.append(("⚖️ Deficit Too High", f"{n['budget_deficit']:.1f}%", "EU fiscal rules breached. IMF may intervene."))
    if n["unemployment"] > 20:
        risks.append(("😔 Mass Unemployment", f"{n['unemployment']:.1f}%", "Social unrest risk. NF benefitting politically."))

    if risks:
        for icon_label, value, desc in risks:
            st.error(f"**{icon_label}** ({value}) — {desc}")
    else:
        st.success("✅ No immediate economic crisis indicators. Situation manageable.")


def _render_trends(state):
    history = state["history"].get("economic_history", [])
    approval = state["history"].get("approval_history", [])

    if len(history) < 2:
        st.info("Economic trend data will appear after a few turns.")
        return

    if HAS_PLOTLY:
        _render_plotly_charts(history, approval)
    else:
        _render_simple_charts(history, approval)


def _render_plotly_charts(history, approval):
    dates = [h["date"] for h in history]

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=dates, y=[h["gdp"] for h in history],
                               name="GDP Growth %", line=dict(color="#22C55E", width=2)))
    fig1.add_trace(go.Scatter(x=dates, y=[h["inflation"] for h in history],
                               name="Inflation %", line=dict(color="#EF4444", width=2)))
    fig1.add_trace(go.Scatter(x=dates, y=[h["unemployment"] for h in history],
                               name="Unemployment %", line=dict(color="#F97316", width=2)))
    fig1.update_layout(title="Economic Indicators", height=300,
                        paper_bgcolor="#0f172a", plot_bgcolor="#1e293b",
                        font=dict(color="#e2e8f0"), legend=dict(bgcolor="#1e293b"))
    fig1.update_xaxes(gridcolor="#334155")
    fig1.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig1, use_container_width=True)

    if approval:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=[a["date"] for a in approval],
                                   y=[a["public_trust"] for a in approval],
                                   name="Public Trust", line=dict(color="#3B82F6", width=2)))
        fig2.add_trace(go.Scatter(x=[a["date"] for a in approval],
                                   y=[a["poll"] for a in approval],
                                   name="DA Poll %", line=dict(color="#6366F1", width=2, dash="dash")))
        fig2.update_layout(title="Approval & Trust", height=250,
                            paper_bgcolor="#0f172a", plot_bgcolor="#1e293b",
                            font=dict(color="#e2e8f0"))
        fig2.update_xaxes(gridcolor="#334155")
        fig2.update_yaxes(gridcolor="#334155")
        st.plotly_chart(fig2, use_container_width=True)


def _render_simple_charts(history, approval):
    import pandas as pd
    df = {
        "Date": [h["date"] for h in history],
        "GDP Growth": [h["gdp"] for h in history],
        "Inflation": [h["inflation"] for h in history],
        "Unemployment": [h["unemployment"] for h in history]
    }
    st.line_chart(df, x="Date", y=["GDP Growth", "Inflation", "Unemployment"])


def _render_actions(state):
    n = state["national"]
    pc = n["political_capital"]
    st.markdown(f"**Political Capital Available: {pc}**")
    st.markdown("*Economic actions cost political capital and have immediate effects.*")

    actions = [
        {
            "id": "emergency_investment",
            "name": "💼 Emergency Business Stimulus",
            "cost": 8,
            "desc": "Inject stimulus into business sector. Boosts growth short-term but increases deficit.",
            "effects": {"gdp_growth": 0.5, "budget_deficit": 0.4, "business_confidence": 8, "foreign_investment": 3}
        },
        {
            "id": "austerity_measure",
            "name": "✂️ Spending Cuts Package",
            "cost": 10,
            "desc": "Cut non-essential spending to reduce deficit. Hurts public services and trust.",
            "effects": {"budget_deficit": -0.8, "public_debt": -1.0, "public_trust": -6, "social_tension": 8, "eu_relations": 5}
        },
        {
            "id": "anti_inflation_push",
            "name": "🏦 Anti-Inflation Measures",
            "cost": 8,
            "desc": "Coordinate with Central Bank on interest rate adjustments.",
            "effects": {"inflation": -1.0, "gdp_growth": -0.3, "budget_deficit": 0, "public_trust": 3}
        },
        {
            "id": "investment_mission",
            "name": "✈️ Foreign Investment Mission",
            "cost": 6,
            "desc": "PM-led diplomatic mission to attract foreign investment.",
            "effects": {"foreign_investment": 8, "eu_relations": 3, "business_confidence": 5}
        },
        {
            "id": "eu_fund_acceleration",
            "name": "🇪🇺 Accelerate EU Fund Absorption",
            "cost": 6,
            "desc": "Fast-track EU co-funded projects. Requires administrative capacity.",
            "effects": {"gdp_growth": 0.3, "infrastructure": 5, "eu_relations": 4, "corruption": 2}
        },
    ]

    for action in actions:
        col1, col2 = st.columns([3, 1])
        with col1:
            can_afford = pc >= action["cost"]
            eff_preview = ", ".join(
                f"{k.replace('_', ' ').title()}: {'+' if v > 0 else ''}{v}"
                for k, v in action["effects"].items()
            )
            status = "" if can_afford else " _(insufficient capital)_"
            safe_html(f"""
            <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.75rem;margin-bottom:0.5rem">
              <div style="font-weight:bold">{action['name']} — Cost: {action['cost']} PC{status}</div>
              <div style="font-size:0.82rem;color:#94a3b8">{action['desc']}</div>
              <div style="font-size:0.78rem;color:#64748b;margin-top:4px">{eff_preview}</div>
            </div>
            """)
        with col2:
            st.write("")
            if st.button("Enact", key=f"econ_act_{action['id']}",
                          disabled=not can_afford):
                from engine.game_state import apply_national_effects, add_news, clamp
                state["national"]["political_capital"] -= action["cost"]
                apply_national_effects(state, action["effects"])
                add_news(state, "💼", f"Economic action enacted: {action['name'].replace('💼','').replace('✂️','').replace('🏦','').strip()}", "economic")
                st.session_state["game"] = state
                st.rerun()
