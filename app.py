import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from engine.game_state import initialize_game
from engine.save_load import save_game, load_game, list_saves
from engine.save_codes import encode_save, decode_save
from engine.supabase_client import is_configured as cloud_is_configured
from ui import auth as auth_ui
from ui import dashboard, parliament_view, economy_view, events_view, regions_view, media_view, election_view, cabinet_view, calendar_view, how_to_play, hud, audio
from ui.styles import inject_css

st.set_page_config(
    page_title="Political Simulator: Republic in Crisis",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def render_main_menu():
    inject_css()

    if st.session_state.get("show_how_to_play"):
        def back_to_menu():
            st.session_state["show_how_to_play"] = False
        how_to_play.render(on_continue=back_to_menu)
        if st.button("◀ Back to Main Menu"):
            st.session_state["show_how_to_play"] = False
            st.rerun()
        return

    audio.render_music_player()
    st.markdown("""
    <style>
      @keyframes titleGlow {
        0%, 100% { text-shadow: 0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.2); }
        50% { text-shadow: 0 0 30px rgba(59, 130, 246, 0.8), 0 0 60px rgba(59, 130, 246, 0.4); }
      }
      @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
      @keyframes shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
      }
      .splash-title {
        font-family: 'Cinzel', serif !important;
        font-size: 3.2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6, #EC4899, #3B82F6);
        background-size: 1000px 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: titleGlow 3s ease-in-out infinite, shimmer 8s linear infinite;
        margin: 0;
        letter-spacing: 0.05em;
      }
      .splash-subtitle {
        font-family: 'Cinzel', serif !important;
        font-size: 1.5rem !important;
        color: #cbd5e1 !important;
        letter-spacing: 0.3em !important;
        text-transform: uppercase;
        margin: 0.5rem 0 1rem !important;
        animation: fadeInUp 0.8s ease-out 0.2s both;
      }
      .splash-tagline {
        color: #94a3b8 !important;
        font-size: 1.05rem;
        max-width: 700px;
        margin: 1.5rem auto !important;
        line-height: 1.6;
        animation: fadeInUp 0.8s ease-out 0.4s both;
      }
      .splash-icons {
        font-size: 1.8rem;
        letter-spacing: 1rem;
        margin: 0.5rem 0;
        animation: fadeInUp 0.8s ease-out 0.5s both;
        opacity: 0.7;
      }
    </style>
    <div style="text-align:center;padding:2.5rem 2rem 1rem">
      <div class="splash-icons">🏛️ ⚖️ 📜 🗳️ 🎤</div>
      <h1 class="splash-title">POLITICAL SIMULATOR</h1>
      <h2 class="splash-subtitle">Republic in Crisis</h2>
      <p class="splash-tagline">
        The Republic of Pustinyakovo stands at the edge.
        Inflation eats wages, corruption rots institutions, the opposition smells blood,
        and your fragile coalition holds parliament by just <b style="color:#FBBF24">4 seats</b>.
      </p>
      <p class="splash-tagline" style="animation-delay:0.6s">
        You are <b style="color:#3B82F6">Prime Minister Elena Markova</b>.
        Survive. Reform. Win re-election. Or watch the Republic collapse on your watch.
      </p>
      <div style="display:flex;justify-content:center;gap:2rem;flex-wrap:wrap;margin-top:1.5rem;animation:fadeInUp 0.8s ease-out 0.7s both">
        <div style="text-align:center"><div style="font-size:1.6rem">🤝</div><div style="color:#94a3b8;font-size:0.85rem">Lobby 240 MPs</div></div>
        <div style="text-align:center"><div style="font-size:1.6rem">📜</div><div style="color:#94a3b8;font-size:0.85rem">Pass 20 bills</div></div>
        <div style="text-align:center"><div style="font-size:1.6rem">🌍</div><div style="color:#94a3b8;font-size:0.85rem">Navigate the EU</div></div>
        <div style="text-align:center"><div style="font-size:1.6rem">🚨</div><div style="color:#94a3b8;font-size:0.85rem">Survive 35+ crises</div></div>
        <div style="text-align:center"><div style="font-size:1.6rem">🗳️</div><div style="color:#94a3b8;font-size:0.85rem">Win the next vote</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📖 How to Play (recommended for first-timers)", use_container_width=True):
            st.session_state["show_how_to_play"] = True
            st.rerun()
        st.markdown("### 🎮 New Game")
        difficulty = st.selectbox(
            "Difficulty:",
            ["easy", "normal", "hard", "nightmare"],
            index=1,
            format_func=lambda x: {
                "easy": "🟢 Easy — Forgiving",
                "normal": "🟡 Normal — Balanced",
                "hard": "🟠 Hard — Volatile",
                "nightmare": "🔴 Nightmare — Crisis from day one"
            }[x]
        )
        st.markdown("""
        <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:1rem;margin-bottom:1rem;font-size:0.92rem;color:#cbd5e1">
          <b>You are PM Elena Markova</b> of the Democratic Alliance, leading a fragile 4-party coalition
          (125/240 seats). Inflation 7.8%, corruption endemic, opposition rising.<br><br>
          <b>How to play:</b><br>
          • Each day you get 4 Action Points<br>
          • Introduce bills — they go through 5 stages over ~14 days<br>
          • Lobby MPs, parties, hold press events to shift support %<br>
          • Watch live vote count change as you act<br>
          • Survive 4 years and win re-election
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚀 Start New Game", type="primary", use_container_width=True):
            with st.spinner("Generating 240 MPs and political map..."):
                st.session_state["game"] = initialize_game(difficulty=difficulty)
                st.session_state["view"] = "dashboard"
                st.session_state.pop("selected_law_id", None)
                st.session_state.pop("last_election_results", None)
            st.rerun()

        if cloud_is_configured():
            st.markdown("---")
            auth_ui.render_login_panel(in_sidebar=False)
            if auth_ui.is_logged_in():
                st.markdown("---")
                auth_ui.render_cloud_saves_panel(state=None)

        st.markdown("---")
        st.markdown("### ☁️ Resume from save code")
        st.caption("Paste a save code from any device to continue your game.")
        pasted = st.text_area("Save code:", key="menu_import_code", height=100, placeholder="PSIM1.xxxxxx....")
        if st.button("📥 Load from code", key="menu_import_btn", use_container_width=True):
            if not pasted.strip():
                st.warning("Paste a save code first.")
            else:
                loaded, err = decode_save(pasted)
                if err:
                    st.error(err)
                else:
                    st.session_state["game"] = loaded
                    st.session_state["view"] = "dashboard"
                    st.success("✅ Game resumed!")
                    st.rerun()

        st.markdown("---")
        st.markdown("### 📂 Local saves (this device)")
        saves = list_saves()
        if saves:
            for sv in saves:
                col_sv1, col_sv2 = st.columns([3, 1])
                with col_sv1:
                    st.markdown(f"Slot {sv['slot']} — Day {sv['turn']} · {sv['game_date']}")
                with col_sv2:
                    if st.button("Load", key=f"load_{sv['slot']}"):
                        loaded = load_game(sv["slot"])
                        if loaded:
                            st.session_state["game"] = loaded
                            st.session_state["view"] = "dashboard"
                            st.rerun()
        else:
            st.info("No local saves on this device. Use save codes to transfer between devices.")


def render_game_over(state):
    inject_css()
    reasons = {
        "coalition_collapse": ("💥", "Coalition Collapse", "Your coalition fractured — government fell."),
        "total_loss_of_trust": ("😔", "Loss of Legitimacy", "Public trust collapsed. Forced resignation."),
        "debt_crisis": ("💸", "Debt Crisis", "Debt unsustainable. Creditors took over."),
        "revolution": ("🔥", "Popular Revolution", "Tensions exploded. Government swept away."),
    }
    icon, title, desc = reasons.get(state.get("game_over_reason", ""), ("❌", "Government Fell", "Your government ended."))

    st.markdown(f"""
    <div style="text-align:center;padding:3rem">
      <div style="font-size:4rem">{icon}</div>
      <h1 style="color:#EF4444">{title}</h1>
      <p style="color:#94a3b8;font-size:1.1rem">{desc}</p>
    </div>
    """, unsafe_allow_html=True)

    n = state["national"]
    history = state["history"]
    days = state["turn"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Days in Office", days)
        st.metric("Final Public Trust", f"{n['public_trust']}%")
    with col2:
        st.metric("Final Corruption", f"{n['corruption']}%")
        st.metric("GDP Growth", f"{n['gdp_growth']:+.1f}%")
    with col3:
        st.metric("Laws Passed", len(history.get("laws_passed", [])))
        st.metric("EU Relations", f"{n['eu_relations']}%")

    if st.button("🔄 Return to Main Menu", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def render_sidebar(state):
    event_count = len(state.get("active_events", []))

    st.sidebar.markdown("""
    <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);padding:0.6rem;border-radius:8px;margin-bottom:0.8rem;text-align:center">
      <div style="color:white;font-weight:bold;font-size:1.0rem">🏛️ Pustinyakovo</div>
      <div style="color:#dbeafe;font-size:0.72rem">Republic in Crisis</div>
    </div>
    """, unsafe_allow_html=True)

    if event_count > 0:
        st.sidebar.error(f"🚨 {event_count} Crisis Active!")

    col_m1, col_m2 = st.sidebar.columns(2)
    with col_m1:
        audio.music_toggle_button()
    with col_m2:
        if st.button("🔊+", key="vol_up", help="Volume up"):
            st.session_state["music_volume"] = min(100, st.session_state.get("music_volume", 30) + 15)
            st.rerun()

    st.sidebar.markdown("### Navigation")
    views = [
        ("🏠", "Dashboard", "dashboard"),
        ("📅", "Calendar & Plan", "calendar"),
        ("🚨", f"Events ({event_count})" if event_count else "Events", "events"),
        ("🏛️", "Parliament", "parliament"),
        ("💰", "Economy", "economy"),
        ("🗺️", "Regions", "regions"),
        ("📺", "Media", "media"),
        ("👔", "Cabinet", "cabinet"),
        ("🗳️", "Elections", "elections"),
        ("📖", "How to Play", "how_to_play"),
    ]
    for icon, label, view_id in views:
        is_active = st.session_state.get("view", "dashboard") == view_id
        btn_type = "primary" if is_active else "secondary"
        full_label = f"{icon} {label}"
        if st.sidebar.button(full_label, key=f"nav_{view_id}",
                              use_container_width=True, type=btn_type):
            st.session_state["view"] = view_id
            st.rerun()

    st.sidebar.markdown("---")
    if cloud_is_configured():
        auth_ui.render_login_panel(in_sidebar=True)
        if auth_ui.is_logged_in():
            with st.sidebar.expander("☁️ Cloud saves"):
                auth_ui.render_cloud_saves_panel(state=state)
        st.sidebar.markdown("---")

    st.sidebar.markdown("**☁️ Save Code (any device, no login)**")

    with st.sidebar.expander("📤 Export save code"):
        code = encode_save(state)
        st.caption(f"Your save code ({len(code):,} chars). Copy and store it anywhere — paste back later to resume from any device or browser.")
        st.code(code, language=None)
        st.caption("💡 Tip: Save this in a text file, email, or password manager. You can paste it on any other Streamlit instance running this game.")

    with st.sidebar.expander("📥 Import save code"):
        pasted = st.text_area("Paste a save code:", key="import_code_box", height=120, placeholder="PSIM1.xxxxxx....")
        if st.button("Load from code", key="import_btn", use_container_width=True):
            if not pasted.strip():
                st.warning("Paste a save code first.")
            else:
                loaded, err = decode_save(pasted)
                if err:
                    st.error(err)
                else:
                    st.session_state["game"] = loaded
                    st.session_state["view"] = "dashboard"
                    st.success("✅ Save loaded! Game resumed.")
                    st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**💾 Local save slots** (this device only)")
    save_slot = st.sidebar.number_input("Slot", min_value=1, max_value=9, value=1, key="save_slot", label_visibility="collapsed")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True, key="save_btn"):
            save_game(state, slot=int(save_slot))
            st.sidebar.success(f"Saved to slot {save_slot}!")
    with col2:
        if st.button("📂 Load", use_container_width=True, key="load_slot_btn"):
            loaded = load_game(int(save_slot))
            if loaded:
                st.session_state["game"] = loaded
                st.sidebar.success(f"Loaded slot {save_slot}!")
                st.rerun()
            else:
                st.sidebar.error("No save in that slot.")

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Main Menu", use_container_width=True, key="main_menu_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main():
    if "game" not in st.session_state:
        render_main_menu()
        return

    state = st.session_state["game"]

    if state.get("game_over"):
        render_game_over(state)
        return

    render_sidebar(state)
    audio.render_music_player()

    if state.pop("_trigger_confetti", False):
        audio.fire_confetti()
        st.toast("🎉 Bill passed parliament!", icon="✅")
    triggered_sfx = state.pop("_trigger_sfx", None)
    if triggered_sfx:
        audio.play_sfx(triggered_sfx)
    toast_msg = state.pop("_toast_msg", None)
    if toast_msg:
        st.toast(toast_msg)

    view = st.session_state.get("view", "dashboard")

    if view != "how_to_play":
        hud.render_hud(state)

    if view == "dashboard":
        dashboard.render(state)
    elif view == "calendar":
        calendar_view.render(state)
    elif view == "events":
        events_view.render(state)
    elif view == "parliament":
        parliament_view.render(state)
    elif view == "economy":
        economy_view.render(state)
    elif view == "regions":
        regions_view.render(state)
    elif view == "media":
        media_view.render(state)
    elif view == "cabinet":
        cabinet_view.render(state)
    elif view == "elections":
        election_view.render(state)
    elif view == "how_to_play":
        how_to_play.render(on_continue=None)
    else:
        dashboard.render(state)

    st.session_state["game"] = state
    audio.render_pending_sfx()


if __name__ == "__main__":
    main()
