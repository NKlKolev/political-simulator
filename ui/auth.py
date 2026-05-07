import streamlit as st
from .styles import inject_css, safe_html
from engine.supabase_client import (sign_up, sign_in, sign_out, restore_session,
                                      is_configured, list_user_saves, save_to_cloud,
                                      load_from_cloud, delete_cloud_save)


def get_current_user():
    """Returns the logged-in user dict, or None."""
    return st.session_state.get("auth_user")


def is_logged_in():
    return get_current_user() is not None


def render_login_panel(in_sidebar=False):
    """Show login/signup UI."""
    container = st.sidebar if in_sidebar else st

    if not is_configured():
        if not in_sidebar:
            container.info("☁️ Cloud saves not configured. Using save codes only.")
        return

    user = get_current_user()
    if user:
        if in_sidebar:
            container.success(f"☁️ Signed in: {user['email']}")
            if container.button("Sign out", key="signout_btn", use_container_width=True):
                sign_out()
                for k in ["auth_user", "auth_access_token", "auth_refresh_token"]:
                    st.session_state.pop(k, None)
                st.rerun()
        return

    if in_sidebar:
        container.markdown("**☁️ Cloud Saves**")
        with container.expander("🔐 Sign in / Sign up"):
            _render_login_form(in_sidebar=True)
    else:
        st.markdown("### 🔐 Sign in for cloud saves")
        st.caption("Optional. Cloud saves let you resume from any device with one click. Skip to play with save codes only.")
        _render_login_form(in_sidebar=False)


def _render_login_form(in_sidebar):
    tab_in, tab_up = st.tabs(["Sign in", "Create account"])

    key_prefix = "sb" if in_sidebar else "main"

    with tab_in:
        email = st.text_input("Email", key=f"{key_prefix}_login_email")
        password = st.text_input("Password", type="password", key=f"{key_prefix}_login_pw")
        if st.button("Sign in", key=f"{key_prefix}_login_btn", use_container_width=True, type="primary"):
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
                    st.success(f"Welcome back, {session['user']['email']}!")
                    st.rerun()

    with tab_up:
        new_email = st.text_input("Email", key=f"{key_prefix}_signup_email")
        new_password = st.text_input("Password (min 6 chars)", type="password", key=f"{key_prefix}_signup_pw")
        st.caption("⚠️ If your Supabase project has email confirmation enabled, check your inbox after signing up.")
        if st.button("Create account", key=f"{key_prefix}_signup_btn", use_container_width=True):
            if not new_email or not new_password:
                st.warning("Enter email and password.")
            elif len(new_password) < 6:
                st.warning("Password must be at least 6 characters.")
            else:
                with st.spinner("Creating account..."):
                    user, err = sign_up(new_email, new_password)
                if err:
                    st.error(err)
                else:
                    st.success("✅ Account created! Sign in to start playing.")


def render_cloud_saves_panel(state=None):
    """Show user's cloud saves. If state is given, also show 'save current game'."""
    user = get_current_user()
    if not user:
        return

    saves = list_user_saves(user["id"])

    st.markdown("**☁️ Your cloud saves**")

    if state is not None:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            slot_to_save = st.number_input("Save to slot:", min_value=1, max_value=10, value=1, key="cloud_save_slot", label_visibility="collapsed")
        with col2:
            save_name = st.text_input("Name", value="", key="cloud_save_name", label_visibility="collapsed", placeholder="(optional)")
        with col3:
            if st.button("💾 Save", key="cloud_save_btn", use_container_width=True):
                ok, err = save_to_cloud(user["id"], int(slot_to_save), state, save_name)
                if ok:
                    st.success(f"Saved to slot {slot_to_save}!")
                    st.rerun()
                else:
                    st.error(err or "Save failed.")

    if not saves:
        st.caption("No cloud saves yet.")
        return

    for sv in saves:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            label = sv.get("name") or f"Slot {sv['slot']}"
            updated = sv.get("updated_at", "")[:16].replace("T", " ")
            safe_html(f"""
            <div style="padding:6px 10px;background:#1e293b;border-radius:6px;border-left:3px solid #3B82F6">
              <div style="color:#f1f5f9;font-weight:bold;font-size:0.9rem">Slot {sv['slot']} — {label}</div>
              <div style="color:#94a3b8;font-size:0.75rem">Day {sv.get('turn', '?')} · {sv.get('game_date', '?')} · {updated}</div>
            </div>
            """)
        with col2:
            if st.button("📂 Load", key=f"cloud_load_{sv['slot']}", use_container_width=True):
                state_loaded, err = load_from_cloud(user["id"], sv["slot"])
                if err:
                    st.error(err)
                else:
                    st.session_state["game"] = state_loaded
                    st.session_state["view"] = "dashboard"
                    st.rerun()
        with col3:
            if st.button("🗑️", key=f"cloud_del_{sv['slot']}", use_container_width=True):
                delete_cloud_save(user["id"], sv["slot"])
                st.rerun()
