"""Audio system: background music + sound effects.

Uses HTML5 Audio API via injected JavaScript. Music URLs use royalty-free
tracks from Pixabay/Bensound (CDN-hosted, CORS-friendly).

Users can toggle music in the HUD. Sound effects play once per event.
"""
import streamlit as st
import streamlit.components.v1 as components


# Royalty-free, CORS-friendly URLs (Pixabay / public CDN)
MUSIC_TRACKS = {
    "ambient_political": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3?filename=cinematic-documentary-piano-118023.mp3",
    "tense": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=tense-corporate-110501.mp3",
    "victory": "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bbc4ff.mp3?filename=success-1-6297.mp3",
}

SFX = {
    "click":     "https://cdn.pixabay.com/download/audio/2022/03/24/audio_d1fb15b146.mp3?filename=click-21156.mp3",
    "vote_pass": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c0c97c8ac6.mp3?filename=success-fanfare-trumpets-6185.mp3",
    "vote_fail": "https://cdn.pixabay.com/download/audio/2022/03/10/audio_c8a9bbe19e.mp3?filename=error-126627.mp3",
    "notification": "https://cdn.pixabay.com/download/audio/2022/03/10/audio_a8e602753c.mp3?filename=notification-126626.mp3",
    "day_advance": "https://cdn.pixabay.com/download/audio/2021/08/04/audio_c668c33e5d.mp3?filename=clock-ticking-60-second-countdown-118453.mp3",
    "crisis": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a18bb43c.mp3?filename=alarm-clock-90867.mp3",
}


def render_music_player():
    """Render the persistent background music player. Call once per page render."""
    if "music_enabled" not in st.session_state:
        st.session_state["music_enabled"] = False
    if "music_volume" not in st.session_state:
        st.session_state["music_volume"] = 30

    track_url = MUSIC_TRACKS["ambient_political"]
    enabled = st.session_state.get("music_enabled", False)
    volume = st.session_state.get("music_volume", 30) / 100.0

    autoplay = "autoplay" if enabled else ""
    muted = "" if enabled else "muted"

    components.html(f"""
    <audio id="bgmusic" loop {autoplay} {muted} preload="auto" style="display:none">
      <source src="{track_url}" type="audio/mpeg">
    </audio>
    <script>
      (function() {{
        const audio = document.getElementById('bgmusic');
        if (!audio) return;
        audio.volume = {volume};
        // Try to play (may need user interaction)
        if ({str(enabled).lower()}) {{
          audio.play().catch(() => {{}});
        }}
      }})();
    </script>
    """, height=0)


def play_sfx(sfx_name):
    """Trigger a sound effect. Stored in session state so it plays on next render."""
    st.session_state.setdefault("_pending_sfx", []).append(sfx_name)


def render_pending_sfx():
    """Play any queued sound effects. Call at the bottom of each page render."""
    pending = st.session_state.pop("_pending_sfx", [])
    if not pending:
        return
    for sfx_name in pending[:3]:
        url = SFX.get(sfx_name)
        if url:
            components.html(f"""
            <audio autoplay style="display:none">
              <source src="{url}" type="audio/mpeg">
            </audio>
            """, height=0)


def music_toggle_button():
    """Render a tiny music on/off toggle. Returns True if state changed."""
    enabled = st.session_state.get("music_enabled", False)
    icon = "🔊" if enabled else "🔇"
    label = f"{icon} Music"
    if st.button(label, key="music_toggle_btn", help="Toggle background music"):
        st.session_state["music_enabled"] = not enabled
        return True
    return False


def fire_confetti():
    """Inject a one-shot confetti animation."""
    components.html("""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js"></script>
    <script>
      (function() {
        if (typeof confetti === 'undefined') return;
        const colors = ['#3B82F6', '#22C55E', '#FBBF24', '#EC4899', '#8B5CF6'];
        const duration = 1500;
        const end = Date.now() + duration;
        (function frame() {
          confetti({
            particleCount: 4,
            angle: 60,
            spread: 55,
            origin: { x: 0, y: 0.7 },
            colors: colors
          });
          confetti({
            particleCount: 4,
            angle: 120,
            spread: 55,
            origin: { x: 1, y: 0.7 },
            colors: colors
          });
          if (Date.now() < end) requestAnimationFrame(frame);
        })();
      })();
    </script>
    """, height=0)
