import streamlit as st
from .styles import (PARTY_COLORS, get_indicator_color, progress_bar_html, inject_css, safe_html)
from engine.game_state import get_coalition_seat_total
from engine.calendar_engine import get_upcoming_calendar


def render(state):
    inject_css()

    _render_tip_card(state)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        _render_indicators(state)
        _render_coalition_status(state)
    with col_b:
        _render_upcoming_strip(state)
        _render_news_compact(state)


def _render_tip_card(state):
    """Show the active tip if there is one."""
    tip = st.session_state.get("_active_tip")
    if not tip:
        return

    safe_html(f"""
    <div style="background:linear-gradient(90deg, rgba(251,191,36,0.12), rgba(59,130,246,0.08));
                border:1px solid rgba(251,191,36,0.4);
                border-radius:10px;
                padding:0.7rem 1rem;
                margin-bottom:1rem;
                display:flex;
                align-items:center;
                gap:14px;
                animation: fadeIn 0.5s ease-out">
      <div style="font-size:1.6rem">{tip['icon']}</div>
      <div style="flex:1">
        <div style="color:#FBBF24;font-weight:bold;font-size:0.85rem;letter-spacing:0.05em;text-transform:uppercase">
          💡 Tip · {tip['title']}
        </div>
        <div style="color:#cbd5e1;font-size:0.9rem;line-height:1.4;margin-top:2px">
          {tip['text']}
        </div>
      </div>
    </div>
    """)
    col_dismiss = st.columns([5, 1])[1]
    with col_dismiss:
        if st.button("✕ Dismiss", key="dismiss_tip", use_container_width=True):
            st.session_state.pop("_active_tip", None)
            st.rerun()


def _render_indicators(state):
    n = state["national"]
    st.markdown("### 📊 National Indicators")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**🏛️ Governance**")
        for label, key, inv in [
            ("Democratic Quality", "democratic_quality", False),
            ("Rule of Law", "rule_of_law", False),
            ("Media Freedom", "media_freedom", False),
            ("EU Relations", "eu_relations", False),
        ]:
            color = get_indicator_color(n[key], inverse=inv)
            st.markdown(progress_bar_html(n[key], color=color, label=label), unsafe_allow_html=True)
    with col2:
        st.markdown("**💼 Economy & Resources**")
        for label, val, inv in [
            ("Energy Security", n["energy_security"], False),
            ("Foreign Investment", n["foreign_investment"], False),
            ("Business Confidence", n["business_confidence"], False),
            ("Public Debt (% GDP)", min(100, n["public_debt"]), True),
        ]:
            color = get_indicator_color(val, inverse=inv)
            st.markdown(progress_bar_html(val, color=color, label=label), unsafe_allow_html=True)

    st.markdown("---")


def _render_coalition_status(state):
    st.markdown("### 🤝 Coalition Status")
    coalition = state["parliament"]["coalition"]
    parties = state["parties"]
    majority = state["parliament"]["majority"]
    coalition_seats = get_coalition_seat_total(state)
    margin = coalition_seats - majority
    margin_color = "#22C55E" if margin > 5 else ("#FBBF24" if margin > 0 else "#EF4444")

    parts = []
    for pid in coalition:
        if pid not in parties:
            continue
        p = parties[pid]
        color = PARTY_COLORS.get(pid, "#64748b")
        loyalty = p.get("coalition_loyalty", 65)
        emoji = "✅" if loyalty > 70 else ("⚠️" if loyalty > 50 else "🚨")
        parts.append(f"""
        <div style="background:{color}25;border:1px solid {color};border-radius:8px;padding:8px 12px">
          <div style="color:{color};font-weight:bold;font-size:0.95rem">{p['short']} — {p['name']}</div>
          <div style="color:#cbd5e1;font-size:0.78rem">Seats: <strong>{p['seats']}</strong> · {emoji} Loyalty: <strong>{loyalty}%</strong></div>
        </div>
        """)

    safe_html(f"""
    <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px">{''.join(parts)}</div>
    <div style="font-size:0.85rem;color:#cbd5e1">
      Coalition: <strong style="color:#f1f5f9">{coalition_seats}/240</strong> ·
      Majority: {majority} ·
      <span style="color:{margin_color}">Margin: <strong>{margin:+d}</strong></span>
    </div>
    """)

    st.markdown("**Opposition**")
    opp = [pid for pid in parties if pid not in coalition]
    opp_html = []
    for pid in opp:
        p = parties[pid]
        color = PARTY_COLORS.get(pid, "#64748b")
        opp_html.append(f"""
        <span style="display:inline-block;background:{color}20;border:1px solid {color};border-radius:4px;padding:3px 8px;margin:2px">
          <span style="color:{color};font-weight:bold">{p['short']}</span>
          <span style="color:#cbd5e1;font-size:0.78rem">{p['seats']} seats · {p['poll']:.1f}%</span>
        </span>
        """)
    st.markdown("".join(opp_html), unsafe_allow_html=True)


def _render_upcoming_strip(state):
    st.markdown("### 📅 Next 7 Days")
    upcoming = get_upcoming_calendar(state, days=7)

    rows_html = []
    for item in upcoming:
        d = item["date"]
        bg = "#1e3a5f" if item["is_today"] else ("#1e293b" if item["is_parliament_day"] else "#0f172a")
        marker = "🏛️" if item["is_parliament_day"] else ("🟨" if item["is_weekend"] else "")
        today_label = " (today)" if item["is_today"] else ""

        events_html = ""
        for ev in item["events"][:2]:
            events_html += f'<div style="font-size:0.72rem;color:#cbd5e1;margin-top:2px">{ev["icon"]} {ev["label"][:30]}</div>'
        if not events_html:
            events_html = '<div style="font-size:0.7rem;color:#64748b;margin-top:2px">—</div>'

        rows_html.append(f"""
        <div style="background:{bg};border-radius:5px;padding:5px 8px;margin-bottom:3px;font-size:0.82rem">
          <div style="color:#f1f5f9"><strong>{item['weekday']} {d['day']}</strong>{today_label} {marker}</div>
          {events_html}
        </div>
        """)
    st.markdown("".join(rows_html), unsafe_allow_html=True)


def _render_news_compact(state):
    st.markdown("### 📰 Latest News")
    news = state["news"][:6]
    if not news:
        st.info("No news yet.")
        return

    border_colors = {
        "economic": "#D97706", "political": "#3B82F6",
        "corruption": "#EF4444", "social": "#8B5CF6",
        "security": "#6B7280", "foreign": "#0EA5E9",
        "foreign_policy": "#0EA5E9", "environmental": "#16A34A",
        "media": "#F59E0B"
    }
    rows = []
    for item in news:
        color = border_colors.get(item.get("type", ""), "#475569")
        date_label = item.get("day_str", item.get("month", ""))
        rows.append(f"""
        <div style="border-left:3px solid {color};padding:5px 8px;margin-bottom:4px;background:#0f172a;border-radius:3px;font-size:0.82rem">
          <span style="color:#94a3b8;font-size:0.7rem">{date_label}</span><br>
          <span style="color:#f1f5f9">{item.get('icon','')} {item.get('text','')[:100]}</span>
        </div>
        """)
    st.markdown("".join(rows), unsafe_allow_html=True)
