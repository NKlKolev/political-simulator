import streamlit as st
from .styles import PARTY_COLORS, get_indicator_color, inject_css, safe_html
from engine.election_engine import run_election, calculate_election_forecast
from engine.game_state import get_days_to_election

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def render(state):
    inject_css()

    days_left = get_days_to_election(state)

    if state["phase"] == "election" or days_left <= 0:
        _render_election_night(state)
    else:
        _render_pre_election(state, days_left)


def _render_pre_election(state, days_left):
    st.markdown("## 🗳️ Electoral Forecast")
    months_approx = days_left // 30
    st.markdown(f"**{days_left} days (~{months_approx} months) until the next scheduled election**")

    forecasts = calculate_election_forecast(state)
    parties = state["parties"]

    _render_poll_chart(state, forecasts)
    _render_seat_projection(state, forecasts)
    _render_coalition_calculator(state, forecasts)

    if days_left <= 180:
        st.warning("⚡ **Election approaching!** Consider launching a pre-election campaign.")

    if days_left <= 90:
        st.error("🗳️ **Election imminent!** Campaign mode activates automatically.")

    history_results = state["history"].get("election_results", [])
    if history_results:
        st.markdown("---")
        st.markdown("### 📜 Previous Election Results")
        for res in history_results:
            st.markdown(f"**Election — Turn {res['turn']}**")
            seats = res["results"]["seats"]
            for pid, s in sorted(seats.items(), key=lambda x: -x[1]):
                if pid in parties:
                    color = PARTY_COLORS.get(pid, "#64748b")
                    st.markdown(f'<span style="color:{color}">■</span> **{parties[pid]["short"]}** {s} seats ({res["results"]["vote_shares"].get(pid, 0):.1f}%)', unsafe_allow_html=True)


def _render_poll_chart(state, forecasts):
    parties = state["parties"]

    st.markdown("#### 📊 Current Polls")

    if HAS_PLOTLY:
        labels = []
        values = []
        colors_list = []
        for party_id, party in sorted(parties.items(), key=lambda x: -x[1]["poll"]):
            labels.append(f"{party['short']}<br>{party['poll']:.1f}%")
            values.append(party["poll"])
            colors_list.append(PARTY_COLORS.get(party_id, "#64748b"))

        fig = go.Figure(go.Bar(
            x=labels, y=values,
            marker_color=colors_list,
            text=[f"{v:.1f}%" for v in values],
            textposition="outside"
        ))
        fig.update_layout(height=300, paper_bgcolor="#0f172a", plot_bgcolor="#1e293b",
                           font=dict(color="#e2e8f0"), showlegend=False,
                           yaxis=dict(range=[0, 55], gridcolor="#334155"),
                           xaxis=dict(gridcolor="#334155"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        for party_id, party in sorted(parties.items(), key=lambda x: -x[1]["poll"]):
            color = PARTY_COLORS.get(party_id, "#64748b")
            safe_html(f"""
            <div style="margin-bottom:4px">
              <div style="display:flex;justify-content:space-between;font-size:0.85rem">
                <span style="color:{color}"><b>{party['short']}</b> {party['name']}</span>
                <span>{party['poll']:.1f}%</span>
              </div>
              <div style="height:12px;background:#334155;border-radius:4px;overflow:hidden">
                <div style="width:{party['poll']}%;height:100%;background:{color}"></div>
              </div>
            </div>
            """)


def _render_seat_projection(state, forecasts):
    parties = state["parties"]
    majority = state["parliament"]["majority"]

    st.markdown("#### 🪑 Projected Seat Ranges")

    total = sum(f["central"] for f in forecasts.values())
    if total <= 0:
        return

    seat_html = '<div style="display:flex;flex-wrap:wrap;gap:2px;margin-bottom:1rem">'
    for party_id, party in sorted(parties.items(), key=lambda x: -x[1]["poll"]):
        forecast = forecasts.get(party_id, {"central": party["poll"]})
        projected_share = forecast["central"] / total
        projected_seats = int(projected_share * 240)
        color = PARTY_COLORS.get(party_id, "#64748b")
        for _ in range(max(1, projected_seats)):
            seat_html += f'<div style="width:12px;height:20px;background:{color};border-radius:2px;opacity:0.8"></div>'
    seat_html += f'</div><div style="font-size:0.8rem;color:#94a3b8">Majority threshold: {majority} seats</div>'
    st.markdown(seat_html, unsafe_allow_html=True)

    for party_id, party in sorted(parties.items(), key=lambda x: -x[1]["poll"]):
        forecast = forecasts.get(party_id, {})
        color = PARTY_COLORS.get(party_id, "#64748b")
        low = forecast.get("low", party["poll"] - 3)
        central = forecast.get("central", party["poll"])
        high = forecast.get("high", party["poll"] + 3)
        below_threshold = central < 4.0

        seats_central = int(central / 100 * 240) if not below_threshold else 0

        threshold_warn = " ⚠️ BELOW 4% THRESHOLD" if below_threshold else ""
        st.markdown(f'<span style="color:{color}">■</span> **{party["short"]}** — {low:.1f}–{high:.1f}% (central: {central:.1f}% ≈ {seats_central} seats){threshold_warn}', unsafe_allow_html=True)


def _render_coalition_calculator(state, forecasts):
    st.markdown("---")
    st.markdown("#### 🤝 Coalition Calculator")
    st.markdown("*Estimated seat totals for possible coalitions:*")

    parties = state["parties"]
    majority = state["parliament"]["majority"]
    player_party = state["player_party"]

    total = sum(f["central"] for f in forecasts.values())
    if total <= 0:
        return

    projected_seats = {
        pid: max(0, int(forecasts.get(pid, {"central": parties[pid]["poll"]})["central"] / total * 240))
        if forecasts.get(pid, {"central": parties[pid]["poll"]})["central"] >= 4.0 else 0
        for pid in parties
    }

    party_ids = [pid for pid, seats in projected_seats.items() if seats > 0]
    player_seats = projected_seats.get(player_party, 0)

    combinations = []
    if player_seats > 0:
        for other in party_ids:
            if other == player_party:
                continue
            combo_seats = player_seats + projected_seats[other]
            combinations.append(([player_party, other], combo_seats))

        for i, other1 in enumerate(party_ids):
            if other1 == player_party:
                continue
            for other2 in party_ids[i+1:]:
                if other2 == player_party:
                    continue
                combo_seats = player_seats + projected_seats[other1] + projected_seats[other2]
                combo = [player_party, other1, other2]
                if combo_seats > projected_seats[other1] + projected_seats[other2]:
                    combinations.append((combo, combo_seats))

    combinations.sort(key=lambda x: -x[1])
    seen = set()
    for combo, seats in combinations[:6]:
        key = frozenset(combo)
        if key in seen:
            continue
        seen.add(key)
        names = " + ".join(parties[pid]["short"] for pid in combo)
        possible = seats >= majority
        color = "#22C55E" if possible else "#EF4444"
        margin_str = f"(+{seats - majority})" if possible else f"({seats - majority})"
        st.markdown(f'<span style="color:{color}">{"✅" if possible else "❌"}</span> **{names}** — {seats} seats {margin_str}', unsafe_allow_html=True)


def _render_election_night(state):
    st.markdown("## 🗳️ ELECTION NIGHT")
    st.markdown("---")

    if st.button("🗳️ Run the Election!", type="primary"):
        results = run_election(state)
        st.session_state["last_election_results"] = results
        st.session_state["game"] = state
        state["phase"] = "coalition_talks"
        st.rerun()

    if "last_election_results" in st.session_state:
        _display_results(state, st.session_state["last_election_results"])


def _display_results(state, results):
    parties = state["parties"]
    majority = results["majority"]

    st.markdown("### 📊 Final Results")

    seats = results["seats"]
    shares = results["vote_shares"]
    winner = results["winner"]

    player_party = state["player_party"]
    player_seats = seats.get(player_party, 0)
    majority_threshold = majority

    if player_seats >= majority_threshold:
        st.success(f"🎉 **{parties[player_party]['name']} wins a majority!** {player_seats} seats.")
    else:
        st.warning(f"Coalition talks needed. {parties[player_party]['name']}: {player_seats} seats (need {majority_threshold} for majority).")

    for party_id, party in sorted(parties.items(), key=lambda x: -seats.get(x[0], 0)):
        s = seats.get(party_id, 0)
        share = shares.get(party_id, 0)
        color = PARTY_COLORS.get(party_id, "#64748b")
        below = "⚠️ Below threshold" if share < 4.0 and s == 0 else ""

        safe_html(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:8px;background:#1e293b;border-radius:8px;margin-bottom:4px">
          <span style="color:{color};font-size:1.2rem">■</span>
          <div style="flex:1"><strong>{party['short']} — {party['name']}</strong></div>
          <div>{share:.1f}% → <strong>{s} seats</strong> {below}</div>
        </div>
        """)

    if results.get("coalition_options"):
        st.markdown("---")
        st.markdown("### 🤝 Viable Coalition Options")
        for option in results["coalition_options"]:
            names = " + ".join(parties[pid]["short"] for pid in option)
            total = sum(seats.get(pid, 0) for pid in option)
            st.markdown(f"✅ **{names}** — {total} seats (majority: {majority})")

    if st.button("🏛️ Form Government & Continue"):
        coalition = results.get("coalition_options", [state["parliament"]["coalition"]])
        if coalition:
            state["parliament"]["coalition"] = coalition[0]
            for pid in state["parties"]:
                state["parties"][pid]["in_government"] = pid in coalition[0]
        state["phase"] = "governance"
        state["parliament"]["votes_this_turn"] = 0
        ed = state["election_due"]
        from engine.game_state import get_date_string
        st.session_state.pop("last_election_results", None)
        st.session_state["game"] = state
        st.rerun()
