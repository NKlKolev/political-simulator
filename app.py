import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from engine.game_state import initialize_game
from engine.save_load import save_game, load_game, list_saves
from engine.save_codes import encode_save, decode_save
from engine.supabase_client import (is_configured as cloud_is_configured,
                                      sign_up, sign_in, sign_out)
from ui import auth as auth_ui
from ui import dashboard, parliament_view, economy_view, events_view, regions_view, media_view, election_view, cabinet_view, calendar_view, how_to_play, hud, audio
from ui.styles import inject_css, safe_html

st.set_page_config(
    page_title="Political Simulator: Republic in Crisis",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def _menu_screen():
    """Returns the current menu screen: 'main', 'new_game', 'load_game', 'how_to_play', 'account'."""
    return st.session_state.get("menu_screen", "main")


def _set_menu(screen):
    st.session_state["menu_screen"] = screen


# ============================================================
# MAIN MENU — game-style start screen
# ============================================================

def render_main_menu():
    inject_css()
    _inject_menu_css()

    screen = _menu_screen()

    _render_account_pill()

    if screen == "how_to_play":
        if st.button("◀ Back to Main Menu", key="back_htp"):
            _set_menu("main")
            st.rerun()
        how_to_play.render(on_continue=None)
        return

    if screen == "new_game":
        _render_new_game_screen()
        return

    if screen == "load_game":
        _render_load_game_screen()
        return

    if screen == "account":
        _render_account_screen()
        return

    _render_hero_splash()
    _render_main_buttons()
    _render_footer()


def _inject_menu_css():
    st.markdown("""
    <style>
      @keyframes titleGlow {
        0%, 100% { text-shadow: 0 0 20px rgba(59, 130, 246, 0.5), 0 0 40px rgba(59, 130, 246, 0.2); }
        50% { text-shadow: 0 0 35px rgba(59, 130, 246, 0.8), 0 0 70px rgba(139, 92, 246, 0.4); }
      }
      @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
      @keyframes shimmer { 0% { background-position: -1000px 0; } 100% { background-position: 1000px 0; } }
      @keyframes neonPulse {
        0%, 100% { text-shadow: 0 0 8px currentColor, 0 0 16px currentColor; opacity: 0.95; }
        50% { text-shadow: 0 0 14px currentColor, 0 0 28px currentColor; opacity: 1; }
      }
      .splash-title {
        font-family: 'Cinzel', serif !important;
        font-size: 4rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6, #EC4899, #3B82F6);
        background-size: 1000px 100%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: titleGlow 3s ease-in-out infinite, shimmer 8s linear infinite;
        margin: 0;
        letter-spacing: 0.06em;
        text-align: center;
      }
      .splash-subtitle {
        font-family: 'Cinzel', serif !important;
        font-size: 1.4rem !important;
        color: #FBBF24 !important;
        letter-spacing: 0.4em !important;
        text-transform: uppercase;
        text-align: center;
        margin: 0.3rem 0 1.5rem !important;
        animation: neonPulse 2.5s ease-in-out infinite;
      }
      .splash-tagline {
        color: #cbd5e1 !important;
        font-size: 1.05rem;
        max-width: 720px;
        margin: 1.2rem auto !important;
        line-height: 1.7;
        text-align: center;
        animation: fadeInUp 0.9s ease-out 0.4s both;
      }
      .splash-icons {
        font-size: 1.7rem;
        letter-spacing: 0.8rem;
        text-align: center;
        margin: 0.5rem 0 1rem;
        animation: fadeInUp 0.8s ease-out 0.2s both;
        opacity: 0.85;
      }
      .stat-callouts {
        display: flex;
        justify-content: center;
        gap: 2.4rem;
        flex-wrap: wrap;
        margin: 2rem auto 1rem;
        animation: fadeInUp 0.9s ease-out 0.7s both;
      }
      .stat-callout {
        text-align: center;
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 10px;
        padding: 0.7rem 1.1rem;
        min-width: 110px;
        backdrop-filter: blur(8px);
        transition: all 0.2s ease;
      }
      .stat-callout:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.6);
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
      }
      .stat-callout-icon { font-size: 1.7rem; margin-bottom: 0.2rem; }
      .stat-callout-text { color: #cbd5e1; font-size: 0.82rem; line-height: 1.3; }

      /* Account pill in top-right */
      .account-pill {
        position: fixed;
        top: 1rem;
        right: 1.5rem;
        z-index: 1000;
        background: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(59, 130, 246, 0.4);
        border-radius: 999px;
        padding: 0.4rem 1rem;
        backdrop-filter: blur(12px);
        font-size: 0.85rem;
        color: #f1f5f9;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
        animation: fadeInUp 0.5s ease-out;
      }
      .account-pill .ap-email {
        color: #93c5fd; font-weight: 500; margin-left: 6px;
      }
      .account-pill .ap-prompt {
        color: #FBBF24; font-weight: 500;
      }

      /* Big menu buttons */
      .menu-button-grid {
        max-width: 480px;
        margin: 0 auto;
        animation: fadeInUp 0.9s ease-out 0.9s both;
      }
      div[data-testid="column"] .stButton > button {
        font-family: 'Cinzel', serif !important;
        letter-spacing: 0.08em !important;
      }

      /* Section headers in screens */
      .menu-section-title {
        font-family: 'Cinzel', serif !important;
        font-size: 2rem !important;
        text-align: center;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem !important;
        letter-spacing: 0.05em;
      }
      .menu-section-sub {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
      }
      .menu-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(8px);
      }

      .menu-footer {
        position: fixed;
        bottom: 1rem;
        left: 50%;
        transform: translateX(-50%);
        font-size: 0.72rem;
        color: #475569;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        text-align: center;
      }
    </style>
    """, unsafe_allow_html=True)


def _render_account_pill():
    """Top-right account widget."""
    if not cloud_is_configured():
        return

    user = auth_ui.get_current_user()
    if user:
        email = user["email"]
        safe_html(f"""
        <div class="account-pill">
          ☁️ Signed in <span class="ap-email">{email}</span>
        </div>
        """)
    else:
        safe_html("""
        <div class="account-pill">
          🔐 <span class="ap-prompt">Not signed in</span>
        </div>
        """)


def _render_hero_splash():
    safe_html("""
    <div style="text-align:center;padding:2rem 2rem 0">
      <div class="splash-icons">🏛️ ⚖️ 📜 🗳️ 🎤</div>
      <h1 class="splash-title">POLITICAL SIMULATOR</h1>
      <h2 class="splash-subtitle">Republic in Crisis</h2>
      <p class="splash-tagline">
        The Republic of Pustinyakovo stands at the edge.
        Inflation eats wages, corruption rots institutions,
        the opposition smells blood, and your fragile coalition holds parliament by just <b style="color:#FBBF24">4 seats</b>.
      </p>
      <p class="splash-tagline" style="animation-delay:0.6s">
        You are <b style="color:#3B82F6">Prime Minister Elena Markova</b>.
        Survive. Reform. Win re-election. Or watch the Republic collapse on your watch.
      </p>
      <div class="stat-callouts">
        <div class="stat-callout"><div class="stat-callout-icon">🤝</div><div class="stat-callout-text">Lobby<br>240 MPs</div></div>
        <div class="stat-callout"><div class="stat-callout-icon">📜</div><div class="stat-callout-text">Pass<br>20 bills</div></div>
        <div class="stat-callout"><div class="stat-callout-icon">🌍</div><div class="stat-callout-text">Navigate<br>the EU</div></div>
        <div class="stat-callout"><div class="stat-callout-icon">🚨</div><div class="stat-callout-text">Survive<br>35+ crises</div></div>
        <div class="stat-callout"><div class="stat-callout-icon">🗳️</div><div class="stat-callout-text">Win the<br>next vote</div></div>
      </div>
    </div>
    """)


def _render_main_buttons():
    saves = list_saves()
    has_local_saves = len(saves) > 0

    st.markdown('<div class="menu-button-grid">', unsafe_allow_html=True)
    col1 = st.container()
    with col1:
        if st.button("⚔️  NEW CAMPAIGN", key="menu_new", type="primary", use_container_width=True):
            _set_menu("new_game"); st.rerun()
        if st.button(("📂  CONTINUE" if has_local_saves else "📂  LOAD GAME"),
                      key="menu_continue", use_container_width=True):
            _set_menu("load_game"); st.rerun()
        if st.button("📖  HOW TO PLAY", key="menu_htp", use_container_width=True):
            _set_menu("how_to_play"); st.rerun()
        if cloud_is_configured():
            user = auth_ui.get_current_user()
            label = "👤  ACCOUNT" if user else "🔐  SIGN IN"
            if st.button(label, key="menu_account", use_container_width=True):
                _set_menu("account"); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def _render_footer():
    safe_html("""
    <div class="menu-footer">
      Republic of Pustinyakovo · Political Simulator v1.1 · Made with ❤️
    </div>
    """)


# ============================================================
# NEW GAME screen
# ============================================================

def _render_new_game_screen():
    if st.button("◀ Back", key="back_ng"):
        _set_menu("main"); st.rerun()

    safe_html('<h1 class="menu-section-title">⚔️ New Campaign</h1>')
    safe_html('<p class="menu-section-sub">Choose your difficulty and begin.</p>')

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        difficulty = st.selectbox(
            "Difficulty:",
            ["easy", "normal", "hard", "nightmare"],
            index=1,
            format_func=lambda x: {
                "easy": "🟢  Easy — Forgiving economy, gentle crises",
                "normal": "🟡  Normal — Balanced challenge",
                "hard": "🟠  Hard — Volatile voters, hostile media",
                "nightmare": "🔴  Nightmare — Crisis from day one"
            }[x]
        )

        safe_html("""
        <div class="menu-card">
          <div style="font-size:1.05rem;color:#f1f5f9;margin-bottom:0.5rem">
            <b>📍 The setting</b>
          </div>
          <div style="color:#cbd5e1;font-size:0.9rem;line-height:1.6">
            March 2024. You are PM <b style="color:#3B82F6">Elena Markova</b> of the Democratic Alliance,
            leading a fragile 4-party coalition (125/240 seats).
            Inflation 7.8%, corruption endemic, opposition rising.
          </div>
          <div style="margin-top:0.8rem;color:#cbd5e1;font-size:0.88rem;line-height:1.6">
            <b>How it plays:</b><br>
            • Each day → 4 Action Points to spend<br>
            • Bills go through 5 stages over ~14 days<br>
            • Lobby individual MPs, parties, hold press events<br>
            • Survive 4 years and win re-election
          </div>
        </div>
        """)

        if st.button("🚀  BEGIN CAMPAIGN", type="primary", use_container_width=True, key="ng_start"):
            with st.spinner("Generating 240 MPs and political map..."):
                st.session_state["game"] = initialize_game(difficulty=difficulty)
                st.session_state["view"] = "dashboard"
                st.session_state.pop("selected_law_id", None)
                st.session_state.pop("last_election_results", None)
                st.session_state["menu_screen"] = "main"
            st.rerun()


# ============================================================
# LOAD GAME screen
# ============================================================

def _render_load_game_screen():
    if st.button("◀ Back", key="back_lg"):
        _set_menu("main"); st.rerun()

    safe_html('<h1 class="menu-section-title">📂 Load Game</h1>')
    safe_html('<p class="menu-section-sub">Resume a saved campaign.</p>')

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if cloud_is_configured() and auth_ui.is_logged_in():
            safe_html('<div class="menu-card">')
            st.markdown("**☁️ Cloud saves**")
            auth_ui.render_cloud_saves_panel(state=None)
            safe_html('</div>')

        safe_html('<div class="menu-card">')
        st.markdown("**💾 Local saves**")
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
                            st.session_state["menu_screen"] = "main"
                            st.rerun()
        else:
            st.info("No local saves on this device.")
        safe_html('</div>')

        safe_html('<div class="menu-card">')
        st.markdown("**🔑 Resume from save code**")
        st.caption("Paste a save code to continue from any device.")
        pasted = st.text_area("Save code:", key="menu_import_code", height=100, placeholder="PSIM1.xxxxxx....", label_visibility="collapsed")
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
                    st.session_state["menu_screen"] = "main"
                    st.success("✅ Game resumed!")
                    st.rerun()
        safe_html('</div>')


# ============================================================
# ACCOUNT screen
# ============================================================

def _render_account_screen():
    if st.button("◀ Back", key="back_acc"):
        _set_menu("main"); st.rerun()

    safe_html('<h1 class="menu-section-title">👤 Account</h1>')

    if not cloud_is_configured():
        st.info("Cloud accounts not configured. Use save codes to transfer between devices.")
        return

    user = auth_ui.get_current_user()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if user:
            safe_html(f"""
            <div class="menu-card" style="text-align:center">
              <div style="font-size:2rem">👤</div>
              <div style="font-size:1.1rem;color:#f1f5f9;margin-top:0.3rem">
                Signed in as<br><b style="color:#3B82F6">{user['email']}</b>
              </div>
            </div>
            """)
            if st.button("🚪 Sign out", use_container_width=True, key="acc_signout"):
                sign_out()
                for k in ["auth_user", "auth_access_token", "auth_refresh_token"]:
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            safe_html('<p class="menu-section-sub">Sign in to save your campaigns to the cloud and play across devices.</p>')
            safe_html('<div class="menu-card">')
            tab_in, tab_up = st.tabs(["🔐 Sign in", "✨ Create account"])
            with tab_in:
                email = st.text_input("Email", key="acc_login_email")
                password = st.text_input("Password", type="password", key="acc_login_pw")
                if st.button("Sign in", key="acc_login_btn", use_container_width=True, type="primary"):
                    if not email or not password:
                        st.warning("Enter email and password.")
                    else:
                        with st.spinner("Signing in..."):
                            session, err = sign_in(email, password)
                        if err:
                            st.error(err)
                        else:
                            st.session_state["auth_user"] = session["user"]
                            st.session_state["auth_access_token"] = session["access_token"]
                            st.session_state["auth_refresh_token"] = session["refresh_token"]
                            st.success(f"Welcome, {session['user']['email']}!")
                            st.rerun()
            with tab_up:
                ne = st.text_input("Email", key="acc_su_email")
                nw = st.text_input("Password (min 6)", type="password", key="acc_su_pw")
                if st.button("Create account", key="acc_su_btn", use_container_width=True):
                    if not ne or len(nw) < 6:
                        st.warning("Email + password (min 6 chars) required.")
                    else:
                        with st.spinner("Creating account..."):
                            u, err = sign_up(ne, nw)
                        if err:
                            st.error(err)
                        else:
                            st.success("✅ Account created! Sign in.")
            safe_html('</div>')


# ============================================================
# GAME OVER
# ============================================================

def render_game_over(state):
    inject_css()
    reasons = {
        "coalition_collapse": ("💥", "Coalition Collapse", "Your coalition fractured — government fell."),
        "total_loss_of_trust": ("😔", "Loss of Legitimacy", "Public trust collapsed. Forced resignation."),
        "debt_crisis": ("💸", "Debt Crisis", "Debt unsustainable. Creditors took over."),
        "revolution": ("🔥", "Popular Revolution", "Tensions exploded. Government swept away."),
    }
    icon, title, desc = reasons.get(state.get("game_over_reason", ""), ("❌", "Government Fell", "Your government ended."))

    safe_html(f"""
    <div style="text-align:center;padding:3rem">
      <div style="font-size:4rem">{icon}</div>
      <h1 style="color:#EF4444">{title}</h1>
      <p style="color:#94a3b8;font-size:1.1rem">{desc}</p>
    </div>
    """)

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


# ============================================================
# IN-GAME SIDEBAR (slimmer now)
# ============================================================

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
    save_slot = st.sidebar.number_input("Save slot", min_value=1, max_value=9, value=1, key="save_slot")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True, key="save_btn"):
            save_game(state, slot=int(save_slot))
            if cloud_is_configured() and auth_ui.is_logged_in():
                from engine.supabase_client import save_to_cloud
                user = auth_ui.get_current_user()
                save_to_cloud(user["id"], int(save_slot), state)
            st.sidebar.success(f"Saved slot {save_slot}!")
    with col2:
        if st.button("📂 Load", use_container_width=True, key="load_slot_btn"):
            loaded = load_game(int(save_slot))
            if loaded:
                st.session_state["game"] = loaded
                st.sidebar.success(f"Loaded slot {save_slot}!")
                st.rerun()
            else:
                st.sidebar.error("No save in that slot.")

    with st.sidebar.expander("📤 Export save code"):
        code = encode_save(state)
        st.caption(f"{len(code):,} chars. Copy to resume on any device.")
        st.code(code, language=None)

    with st.sidebar.expander("📥 Import save code"):
        pasted = st.text_area("Save code:", key="import_code_box", height=100, placeholder="PSIM1.xxxxxx....", label_visibility="collapsed")
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
                    st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🏠 Main Menu", use_container_width=True, key="main_menu_btn"):
        for key in list(st.session_state.keys()):
            if key not in ("auth_user", "auth_access_token", "auth_refresh_token"):
                del st.session_state[key]
        st.rerun()


# ============================================================
# MAIN ROUTER
# ============================================================

def main():
    if "game" not in st.session_state:
        render_main_menu()
        return

    state = st.session_state["game"]

    if state.get("game_over"):
        render_game_over(state)
        return

    render_sidebar(state)

    if state.pop("_show_day_overlay", False):
        from engine.calendar_engine import format_date, get_weekday
        d = state["calendar"]["date"]
        weekday_full = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday",
                         "Thu": "Thursday", "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}
        audio.day_advance_overlay(
            date_str=format_date(d, full=False),
            day_num=state["turn"],
            weekday=weekday_full.get(get_weekday(d), get_weekday(d))
        )

    if state.pop("_trigger_confetti", False):
        audio.fire_confetti()
        st.toast("🎉 Bill passed parliament!", icon="✅")
    triggered_sfx = state.pop("_trigger_sfx", None)
    if triggered_sfx:
        audio.play_sfx(triggered_sfx)
    toast_msg = state.pop("_toast_msg", None)
    if toast_msg:
        st.toast(toast_msg)

    from engine.tips_engine import maybe_show_tip
    tip = maybe_show_tip(state)
    if tip:
        st.session_state["_active_tip"] = tip

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
