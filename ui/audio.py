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
    """Music disabled per user request — kept as no-op so callers don't break."""
    return


def music_toggle_button():
    return False


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


def day_advance_overlay(date_str, day_num, weekday):
    """Brief animated overlay showing the new day after advancing."""
    components.html(f"""
    <style>
      @keyframes overlayFadeIn {{
        0% {{ opacity: 0; transform: scale(0.85); }}
        15% {{ opacity: 1; transform: scale(1); }}
        70% {{ opacity: 1; transform: scale(1); }}
        100% {{ opacity: 0; transform: scale(1.05); }}
      }}
      .day-overlay {{
        position: fixed;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 99999;
        pointer-events: none;
        animation: overlayFadeIn 1.6s ease-out forwards;
      }}
      .day-card {{
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.95), rgba(15, 23, 42, 0.95));
        border: 2px solid #3B82F6;
        border-radius: 16px;
        padding: 1.6rem 3rem;
        text-align: center;
        box-shadow: 0 0 60px rgba(59, 130, 246, 0.6), 0 20px 60px rgba(0,0,0,0.6);
        backdrop-filter: blur(8px);
      }}
      .day-overlay-weekday {{
        font-family: 'Cinzel', serif;
        color: #93c5fd;
        font-size: 1.1rem;
        letter-spacing: 0.4em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
      }}
      .day-overlay-date {{
        font-family: 'Cinzel', serif;
        color: #f1f5f9;
        font-size: 2rem;
        font-weight: 700;
        text-shadow: 0 0 20px rgba(59, 130, 246, 0.6);
      }}
      .day-overlay-day {{
        color: #FBBF24;
        font-size: 0.85rem;
        margin-top: 0.4rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
      }}
    </style>
    <div class="day-overlay">
      <div class="day-card">
        <div class="day-overlay-weekday">{weekday}</div>
        <div class="day-overlay-date">{date_str}</div>
        <div class="day-overlay-day">Day {day_num} in office</div>
      </div>
    </div>
    """, height=0)


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
