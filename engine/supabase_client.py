"""Supabase client wrapper for cloud saves and authentication.

If Supabase credentials are not set, all functions return None / False —
the game remains fully playable with local saves and save codes.

Configuration:
- For local dev: create .streamlit/secrets.toml with [supabase] url and anon_key
- For Streamlit Cloud: paste same TOML into Settings → Secrets in the dashboard
"""
import os
import json
from typing import Optional


_client = None
_init_attempted = False


def _get_credentials():
    """Read Supabase URL + anon key from Streamlit secrets or env vars."""
    try:
        import streamlit as st
        if "supabase" in st.secrets:
            return (
                st.secrets["supabase"].get("url"),
                st.secrets["supabase"].get("anon_key"),
            )
    except Exception:
        pass

    return (
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_ANON_KEY"),
    )


def get_client():
    """Returns the Supabase client, or None if not configured."""
    global _client, _init_attempted
    if _client is not None:
        return _client
    if _init_attempted:
        return None
    _init_attempted = True

    url, key = _get_credentials()
    if not url or not key:
        return None

    try:
        from supabase import create_client
        _client = create_client(url, key)
        return _client
    except Exception:
        return None


def is_configured():
    """Returns True if Supabase credentials are set up."""
    url, key = _get_credentials()
    return bool(url and key)


# ===========================
# AUTH FUNCTIONS
# ===========================

def sign_up(email: str, password: str):
    """Create a new account. Returns (user_dict_or_none, error_message)."""
    client = get_client()
    if not client:
        return None, "Cloud features not configured."
    try:
        result = client.auth.sign_up({"email": email, "password": password})
        if result.user:
            return _user_to_dict(result.user), None
        return None, "Sign up failed."
    except Exception as e:
        return None, _format_error(e)


def sign_in(email: str, password: str):
    """Log in. Returns (session_dict_or_none, error_message)."""
    client = get_client()
    if not client:
        return None, "Cloud features not configured."
    try:
        result = client.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
        if result.user and result.session:
            return {
                "user": _user_to_dict(result.user),
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
            }, None
        return None, "Login failed: invalid credentials."
    except Exception as e:
        return None, _format_error(e)


def sign_out():
    client = get_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass


def restore_session(access_token: str, refresh_token: str):
    """Restore a previous session from saved tokens."""
    client = get_client()
    if not client:
        return None
    try:
        result = client.auth.set_session(access_token, refresh_token)
        if result.user:
            return _user_to_dict(result.user)
    except Exception:
        return None
    return None


def _user_to_dict(user):
    return {
        "id": str(user.id),
        "email": user.email,
    }


def _format_error(e):
    msg = str(e)
    if "Invalid login credentials" in msg:
        return "Wrong email or password."
    if "already registered" in msg.lower() or "already exists" in msg.lower():
        return "An account with that email already exists."
    if "Email not confirmed" in msg:
        return "Please confirm your email first (check your inbox)."
    if "Password should" in msg:
        return msg
    return f"Error: {msg[:120]}"


# ===========================
# CLOUD SAVE FUNCTIONS
# ===========================

def list_user_saves(user_id: str):
    """Return list of save metadata for a user, sorted by slot."""
    client = get_client()
    if not client:
        return []
    try:
        result = (client.table("saves")
                  .select("slot,turn,game_date,updated_at,name")
                  .eq("user_id", user_id)
                  .order("slot")
                  .execute())
        return result.data or []
    except Exception as e:
        print(f"list_user_saves error: {e}")
        return []


def save_to_cloud(user_id: str, slot: int, state: dict, name: str = ""):
    """Upsert a save to the cloud. Returns (ok, error_message)."""
    client = get_client()
    if not client:
        return False, "Cloud not configured."
    try:
        date = state.get("calendar", {}).get("date", {})
        game_date = f"{date.get('day','?')}/{date.get('month','?')}/{date.get('year','?')}"

        record = {
            "user_id": user_id,
            "slot": slot,
            "name": name or f"Save slot {slot}",
            "turn": state.get("turn", 0),
            "game_date": game_date,
            "state_json": state,
        }
        client.table("saves").upsert(record, on_conflict="user_id,slot").execute()
        return True, None
    except Exception as e:
        return False, _format_error(e)


def load_from_cloud(user_id: str, slot: int):
    """Load a save from the cloud. Returns (state_or_none, error_message)."""
    client = get_client()
    if not client:
        return None, "Cloud not configured."
    try:
        result = (client.table("saves")
                  .select("state_json")
                  .eq("user_id", user_id)
                  .eq("slot", slot)
                  .single()
                  .execute())
        if result.data:
            return result.data["state_json"], None
        return None, "Save not found."
    except Exception as e:
        return None, _format_error(e)


def delete_cloud_save(user_id: str, slot: int):
    client = get_client()
    if not client:
        return False
    try:
        client.table("saves").delete().eq("user_id", user_id).eq("slot", slot).execute()
        return True
    except Exception:
        return False
