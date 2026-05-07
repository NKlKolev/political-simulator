import streamlit as st
from .styles import SEVERITY_COLORS, SEVERITY_LABELS, TYPE_ICONS, inject_css, safe_html
from engine.event_engine import resolve_event


def render(state):
    inject_css()
    st.markdown("## 🚨 Crisis Events & Decisions")

    active = state.get("active_events", [])
    if not active:
        st.success("✅ No active crises. Your government is handling things smoothly.")
        st.info("New events will emerge as the situation develops. Advance the turn to continue.")

        st.markdown("---")
        st.markdown("### 📋 Recent Decisions")
        history = state["history"]["decisions"][-10:]
        if history:
            for dec in reversed(history):
                st.markdown(f"**Turn {dec['turn']}** — {dec['event_title']}: *{dec['choice_text']}*")
        else:
            st.write("No decisions recorded yet.")
        return

    for event in active:
        _render_event(state, event)


def _render_event(state, event):
    severity = event.get("severity", 2)
    color = SEVERITY_COLORS.get(severity, "#64748b")
    sev_label = SEVERITY_LABELS.get(severity, "Unknown")
    type_icon = TYPE_ICONS.get(event.get("type", ""), "📋")

    safe_html(f"""
    <div style="border:2px solid {color};border-radius:12px;padding:1.2rem;margin-bottom:1.5rem;background:#1c1917">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:0.75rem">
        <span style="font-size:1.5rem">{type_icon}</span>
        <div>
          <h3 style="margin:0;color:#f1f5f9">{event['title']}</h3>
          <span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem">
            ⚡ {sev_label} Severity
          </span>
          <span style="margin-left:8px;color:#94a3b8;font-size:0.8rem">
            {event.get('type','').replace('_',' ').title()}
          </span>
        </div>
      </div>
      <p style="color:#cbd5e1;line-height:1.6">{event['description']}</p>
    </div>
    """)

    st.markdown("**Choose your response:**")

    choices = event.get("choices", [])
    cols = st.columns(min(len(choices), 2))

    for i, choice in enumerate(choices):
        col = cols[i % len(cols)]
        with col:
            effects = choice.get("effects", {})
            effect_preview = _format_effects_preview(effects)

            safe_html(f"""
            <div style="background:#1e293b;border:1px solid #334155;border-radius:8px;padding:0.8rem;margin-bottom:0.5rem;min-height:80px">
              <div style="font-weight:bold;color:#e2e8f0;margin-bottom:4px">
                {chr(65 + i)}. {choice['text']}
              </div>
              <div style="font-size:0.8rem;color:#94a3b8">{effect_preview}</div>
            </div>
            """)

            key = f"evt_{event['id']}_choice_{choice['id']}"
            if st.button(f"Choose Option {chr(65 + i)}", key=key, type="primary" if i == 0 else "secondary"):
                resolve_event(state, event["id"], choice["id"])
                st.session_state["game"] = state
                st.rerun()

    st.markdown("---")


def _format_effects_preview(effects):
    parts = []
    national = effects.get("national", {})

    pos = []
    neg = []
    neutral = []

    display_keys = {
        "public_trust": "Trust", "corruption": "Corruption", "eu_relations": "EU Relations",
        "social_tension": "Tension", "government_stability": "Stability",
        "budget_deficit": "Deficit", "gdp_growth": "Growth", "inflation": "Inflation",
        "rule_of_law": "Rule of Law", "democratic_quality": "Democracy",
        "media_freedom": "Media Freedom", "energy_security": "Energy Security",
        "political_capital": "Political Capital", "coalition_stability": "Coalition"
    }

    inverse_good = {"corruption", "social_tension", "budget_deficit", "inflation", "security_risk"}

    for k, v in national.items():
        if k not in display_keys:
            continue
        label = display_keys[k]
        if isinstance(v, (int, float)):
            good = (v > 0 and k not in inverse_good) or (v < 0 and k in inverse_good)
            sym = "+" if v > 0 else ""
            entry = f"{label}: {sym}{v}"
            if good:
                pos.append(entry)
            else:
                neg.append(entry)

    result_parts = []
    if pos:
        result_parts.append("✅ " + ", ".join(pos[:3]))
    if neg:
        result_parts.append("⚠️ " + ", ".join(neg[:3]))

    voter = effects.get("voter_effects", {})
    if voter:
        pos_v = [k.replace("_", " ").title() for k, v in voter.items() if v > 0]
        neg_v = [k.replace("_", " ").title() for k, v in voter.items() if v < 0]
        if pos_v:
            result_parts.append(f"👥 Gains: {', '.join(pos_v[:2])}")
        if neg_v:
            result_parts.append(f"👥 Loses: {', '.join(neg_v[:2])}")

    return " · ".join(result_parts) if result_parts else "Mixed effects"
