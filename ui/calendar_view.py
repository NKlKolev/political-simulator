import streamlit as st
from .styles import inject_css, safe_html
from engine.calendar_engine import (get_upcoming_calendar, format_date, advance_day,
                                      is_parliament_day, is_weekend, get_weekday)
from engine.bill_engine import calculate_bill_support, get_current_stage, days_to_vote, get_bill_progress_pct
from engine.lobby_engine import LOBBY_ACTIONS, execute_action
from engine.turn_engine import advance_multiple_days


def render(state):
    inject_css()
    st.markdown("## 📅 Calendar & Daily Planning")

    cal = state["calendar"]
    today_str = format_date(cal["date"], full=True)

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### Today: **{today_str}**")
    with col2:
        ap = cal["action_points"]
        ap_color = "#22C55E" if ap >= 3 else ("#EAB308" if ap >= 1 else "#EF4444")
        safe_html(f"""
        <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.5rem;text-align:center">
          <div style="color:#94a3b8;font-size:0.75rem">⚡ Action Points</div>
          <div style="color:{ap_color};font-size:1.4rem;font-weight:bold">{ap}/{cal['max_action_points']}</div>
        </div>
        """)
    with col3:
        pc = state["national"]["political_capital"]
        safe_html(f"""
        <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.5rem;text-align:center">
          <div style="color:#94a3b8;font-size:0.75rem">💼 Political Capital</div>
          <div style="color:#3B82F6;font-size:1.4rem;font-weight:bold">{pc}</div>
        </div>
        """)

    st.markdown("---")
    tabs = st.tabs(["📅 14-Day Calendar", "⚡ Today's Actions", "⏩ Skip Days"])

    with tabs[0]:
        _render_calendar(state)
    with tabs[1]:
        _render_today_actions(state)
    with tabs[2]:
        _render_skip_days(state)


def _render_calendar(state):
    upcoming = get_upcoming_calendar(state, days=14)

    st.markdown("**Two-week schedule** — events on each day. 🟦 Parliament days · 🟨 Weekends")

    for week in range(2):
        cols = st.columns(7)
        for i in range(7):
            idx = week * 7 + i
            if idx >= len(upcoming):
                continue
            item = upcoming[idx]
            d = item["date"]
            with cols[i]:
                bg = "#1e3a5f" if item["is_today"] else ("#1e293b" if item["is_parliament_day"] else ("#1f1f2c" if item["is_weekend"] else "#0f172a"))
                border = "2px solid #3B82F6" if item["is_today"] else ("1px solid #334155")

                events_html = ""
                for ev in item["events"][:3]:
                    events_html += f"""
                    <div style="font-size:0.7rem;color:#cbd5e1;background:#0f172a;border-radius:3px;padding:2px 4px;margin-top:2px">
                      {ev['icon']} {ev['label'][:30]}
                    </div>
                    """

                today_label = " (Today)" if item["is_today"] else ""
                pd_marker = " 🏛️" if item["is_parliament_day"] else ""

                safe_html(f"""
                <div style="background:{bg};border:{border};border-radius:6px;padding:6px;min-height:120px">
                  <div style="font-weight:bold;color:#94a3b8;font-size:0.78rem">{item['weekday']}{pd_marker}</div>
                  <div style="font-size:1.1rem;color:#f1f5f9">{d['day']}{today_label}</div>
                  <div style="font-size:0.7rem;color:#64748b">{format_date(d, full=False)}</div>
                  {events_html}
                </div>
                """)
        st.write("")

    st.markdown("---")
    st.markdown("#### 📜 Bills in Progress")
    bills = state.get("active_bills", [])
    if not bills:
        st.info("No bills currently in the pipeline.")
    else:
        for bill in bills:
            support = calculate_bill_support(state, bill)
            stage = get_current_stage(bill)
            days_left = days_to_vote(bill)
            progress = get_bill_progress_pct(bill)

            need_pct = round(state["parliament"]["majority"]/240*100, 1)
            status_color = "#22C55E" if support["pct"] >= need_pct else ("#EAB308" if support["pct"] >= need_pct - 5 else "#EF4444")

            safe_html(f"""
            <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.75rem;margin-bottom:0.5rem">
              <div style="display:flex;justify-content:space-between">
                <strong>{bill['title']}</strong>
                <span style="color:{status_color}">Support: {support['pct']}% / need {need_pct}%</span>
              </div>
              <div style="font-size:0.82rem;color:#94a3b8;margin-top:4px">
                {stage['icon']} {stage['label']} · Vote in {days_left} days · Progress {progress}%
              </div>
              <div style="height:6px;background:#0f172a;border-radius:3px;margin-top:4px;overflow:hidden">
                <div style="width:{progress}%;height:100%;background:linear-gradient(90deg,#3B82F6,#8B5CF6)"></div>
              </div>
            </div>
            """)


def _render_today_actions(state):
    cal = state["calendar"]
    pc = state["national"]["political_capital"]

    st.markdown(f"#### Spend your **{cal['action_points']} Action Points** today")
    st.markdown("*Each day you have action points. Use them to lobby, hold press events, or work the cabinet.*")

    general_actions = ["press_conference", "national_address", "anti_corruption_pledge",
                        "rally_supporters", "diplomatic_call"]

    cols = st.columns(2)
    for i, action_id in enumerate(general_actions):
        action = LOBBY_ACTIONS[action_id]
        col = cols[i % 2]
        with col:
            can_afford = (cal["action_points"] >= action["ap_cost"] and pc >= action["pc_cost"])
            color = "#22C55E" if can_afford else "#475569"
            safe_html(f"""
            <div style="background:#1e293b;border:1px solid {color};border-radius:8px;padding:0.75rem;margin-bottom:0.5rem">
              <div style="font-weight:bold">{action['icon']} {action['name']}</div>
              <div style="font-size:0.8rem;color:#94a3b8">{action['description']}</div>
              <div style="font-size:0.75rem;color:#64748b;margin-top:4px">⚡ {action['ap_cost']} AP · 💼 {action['pc_cost']} PC</div>
            </div>
            """)
            if st.button("Execute", key=f"gen_act_{action_id}", disabled=not can_afford):
                ok, msg = execute_action(state, action_id)
                if ok:
                    st.session_state["game"] = state
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("---")
    st.markdown("#### 🤝 Party Negotiation")
    st.markdown("*Lobby an entire party. Costs 2 AP + 4 PC. Affects all their MPs.*")

    parties = state["parties"]
    party_options = ["—"] + list(parties.keys())
    target_party = st.selectbox(
        "Which party to lobby?",
        options=party_options,
        format_func=lambda x: parties[x]["name"] + f" ({parties[x]['short']}, {parties[x]['seats']} seats)" if x in parties else "Select party...",
        key="lobby_party_select"
    )
    if target_party != "—" and target_party in parties:
        action = LOBBY_ACTIONS["lobby_party"]
        can_afford = (cal["action_points"] >= action["ap_cost"] and pc >= action["pc_cost"])
        if st.button(f"🗳️ Negotiate with {parties[target_party]['name']}", disabled=not can_afford):
            ok, msg = execute_action(state, "lobby_party", target_id=target_party)
            if ok:
                st.session_state["game"] = state
                st.rerun()


def _render_skip_days(state):
    st.markdown("#### Skip ahead in time")
    st.markdown("*Skip multiple days at once. Will stop early if a crisis event fires.*")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("⏭️ +1 Day", type="primary", use_container_width=True):
            from engine.turn_engine import advance_day_turn
            updated = advance_day_turn(state)
            st.session_state["game"] = updated
            st.rerun()
    with col2:
        if st.button("⏭️ +3 Days", use_container_width=True):
            updated = advance_multiple_days(state, 3)
            st.session_state["game"] = updated
            st.rerun()
    with col3:
        if st.button("⏭️ +7 Days (Week)", use_container_width=True):
            updated = advance_multiple_days(state, 7)
            st.session_state["game"] = updated
            st.rerun()
    with col4:
        if st.button("⏭️ Until Next Vote", use_container_width=True):
            bills = state.get("active_bills", [])
            if bills:
                min_days = min(days_to_vote(b) for b in bills)
                updated = advance_multiple_days(state, max(1, min_days))
                st.session_state["game"] = updated
                st.rerun()
            else:
                updated = advance_multiple_days(state, 7)
                st.session_state["game"] = updated
                st.rerun()
