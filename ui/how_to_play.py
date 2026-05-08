import streamlit as st
from .styles import inject_css, safe_html


def render(on_continue=None):
    inject_css()

    safe_html("""
    <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);padding:2rem;border-radius:12px;margin-bottom:1.5rem;text-align:center">
      <h1 style="color:white;margin:0">📖 How to Play</h1>
      <p style="color:#dbeafe;margin:0.5rem 0 0">Political Simulator: Republic in Crisis</p>
    </div>
    """)

    tabs = st.tabs([
        "🎯 The Goal",
        "📅 Daily Cycle",
        "📜 Bills & Voting",
        "🤝 Lobbying",
        "🏛️ Coalition",
        "🚨 Events & Crises",
        "🗳️ Elections",
        "💡 Tips"
    ])

    # ---- The Goal ----
    with tabs[0]:
        st.markdown("""
        ### You are the Prime Minister of Pustinyakovo

        You lead **PM Elena Markova** of the **Democratic Alliance (DA)**, a liberal reformist party
        running a fragile **4-party coalition** with 125 of 240 parliamentary seats — barely a majority.

        ### Your mission
        1. **Survive** the full 4-year term (until the next election)
        2. **Pass meaningful legislation** to reform the country
        3. **Win re-election** at the end of your term

        ### What can kill your government
        - 🟥 **Government Stability ≤ 5%** — coalition collapses
        - 🟥 **Public Trust ≤ 5%** — forced resignation
        - 🟥 **Public Debt ≥ 130%** — debt crisis, IMF takeover
        - 🟥 **Social Tension ≥ 95%** — popular revolution
        - 🟥 Coalition partners may **walk out** if loyalty drops too low

        ### The political landscape
        - **DA** (you, 90 seats) — your party, urban liberal reformist
        - **Citizens' Union** (CU, 68 seats) — main opposition, conservative establishment
        - **National Front** (NF, 47 seats) — populist nationalist, **rising fast**
        - **Social Democrats** (SD, 20 seats) — coalition partner, demands more wage rises
        - **Green Future** (GF, 10 seats) — coalition partner, demands climate action
        - **Liberal Democrats** (LD, 5 seats) — coalition partner, business-friendly
        """)

    # ---- Daily Cycle ----
    with tabs[1]:
        st.markdown("""
        ### Day-by-day gameplay

        Time advances **one day at a time** (like Lawgivers). Each day:

        ### ⚡ 4 Action Points (AP)
        Every morning you wake up with **4 Action Points**. AP is your *time and energy*.
        Spend it on lobbying, press events, meetings, etc. **AP do not carry over** — use them or lose them.

        ### 💼 Political Capital (PC)
        Your *political muscle*. Spent on bigger actions. Recovers slowly (+6 every 30 days)
        and faster when you do well (high public trust, etc).

        ### What you do each day
        1. **Check the dashboard** — see your indicators, polls, news
        2. **Resolve any active crisis events** (must be done before advancing)
        3. **Spend Action Points** — meet MPs, hold press events, lobby parties, push bills
        4. Click **+1 Day** (or +7 Days) to advance

        ### Calendar view (📅)
        Shows the next 14 days with:
        - 🏛️ **Parliament days** (Tue/Wed/Thu) — when votes happen
        - 🟨 **Weekends** (Sat/Sun)
        - 📜 **Scheduled bill stage events** on specific dates

        ### Time scales
        - **1 day** = 1 turn
        - **1 week** = polls update, news cycles shift
        - **1 month** = political capital refreshes, indicators drift, party loyalty shifts
        - **4 years (~1460 days)** = re-election day

        ### Skip-ahead buttons
        On the Calendar page: skip 1, 3, 7 days, or "Until Next Vote".
        Skipping **stops automatically** when a crisis fires.
        """)

    # ---- Bills & Voting ----
    with tabs[2]:
        st.markdown("""
        ### How bills become law

        Bills move through **5 stages over ~14 days**:

        | Stage | Days | What happens |
        |-------|------|--------------|
        | ✍️ **Drafting** | 3 | Bill is written. Initial intentions calculated. |
        | 🏛️ **Committee** | 5 | Goes to committee. Best time to lobby members. |
        | 📖 **First Reading** | 2 | Public + opposition first respond. |
        | 🗣️ **Public Debate** | 3 | Media coverage shifts opinion. |
        | 🗳️ **Final Vote** | 1 | The 240 MPs vote. Need **121 votes** to pass. |

        ### Live percentage tracking
        On every bill, you see real-time:
        - **YES / NO / Undecided / Abstain** counts
        - **Support %** vs **Required % (50.4%)**
        - 🟢 Likely PASS · 🟡 Knife-edge · 🔴 Likely FAIL

        The yellow line on the support bar = **majority threshold**.
        Your job is to push the green bar past it.

        ### How to introduce a bill
        1. Go to **Parliament → Propose Bill**
        2. Browse the 20 available laws by category
        3. Click **📜 Introduce** (costs PC)
        4. Bill enters drafting stage → 14-day clock starts
        5. Lobby during the next 14 days to shift the vote!

        ### Limits
        - Maximum **3 bills active at once**
        - Each bill costs **8–15 PC** to introduce
        - Bills that fail do NOT refund PC
        - You can re-propose failed bills later (they appear in "previously failed")
        """)

    # ---- Lobbying ----
    with tabs[3]:
        st.markdown("""
        ### Lobby actions to flip votes

        Bills don't pass automatically — you must **work the chamber** every day.
        Each lobby action affects MP vote intentions on the active bill.

        ### General actions (any time)
        | Action | AP | PC | Effect |
        |--------|----|----|--------|
        | 🎤 **Press Conference** | 1 | 2 | +3 Trust |
        | 📺 **National TV Address** | 3 | 8 | +8 Trust, +4 Stability |
        | 🔍 **Anti-Corruption Pledge** | 1 | 3 | +3 Trust, -2 Corruption, +2 EU |
        | 🚩 **Rally Supporters** | 2 | 2 | DA poll +0.4%, MP loyalty up |
        | 🇪🇺 **EU Diplomatic Call** | 1 | 2 | +3 EU Relations |

        ### Bill-specific lobbying (target an active bill)
        | Action | AP | PC | Effect |
        |--------|----|----|--------|
        | 🤝 **Meet Individual MP** | 1 | 1 | Strongest impact on **one** MP. Best targeting. |
        | 🗳️ **Negotiate with Party** | 2 | 4 | Boost loyalty across **all** party's MPs |
        | 🏛️ **Lobby Committee** | 2 | 3 | Shift 8 undecided coalition MPs toward YES |
        | 📢 **Media Offensive** | 2 | 5 | Shift up to 12 undecided MPs + public |
        | 🐴 **Horse Trading** | 2 | 6 | **Bribe-flip** opposition MPs. Raises corruption! |

        ### Strategy
        - **Lobby Committee** is best during the 5-day Committee stage
        - **Media Offensive** during Public Debate stage
        - **Meet Individual MP** is the **most efficient** action — target persuadable opposition MPs
        - **Horse Trading** flips opposition but increases your corruption stat (bad long-term!)
        - In Parliament → Active Bills → expand "MP-by-MP support" to find **persuadable MPs** (sorted automatically)

        ### MP attributes that matter
        - **Persuadability**: how easy to influence (>50 = good target)
        - **Personal Relationship**: 0-100, increases with meetings
        - **Loyalty**: party loyalty (high = won't rebel)
        - **Corruption Risk**: high = vulnerable to horse trading
        """)

    # ---- Coalition ----
    with tabs[4]:
        st.markdown("""
        ### Managing your fragile 4-party coalition

        You only have **125/240 seats** — losing any partner means losing power.

        ### Coalition partners
        - **DA** (90 seats) — you
        - **SD** (20) — wants higher wages, social spending. Loyalty drops if you don't pass left-wing laws.
        - **GF** (10) — wants green policies, hates coal/military. Loyalty drops on environmental issues.
        - **LD** (5) — wants tax cuts, less regulation. Loyalty drops on socialism/anti-business laws.

        ### Coalition loyalty (each partner)
        - 🟢 **70-100%** — solid support
        - 🟡 **50-70%** — wavering, may rebel on votes
        - 🔴 **<50%** — at risk of leaving coalition

        ### What lowers loyalty
        - Government stability dropping
        - Public trust collapsing
        - Passing laws against the partner's ideology
        - Ignoring their demands during events
        - Time alone (5% drift per month)

        ### What raises loyalty
        - **🗳️ Negotiate with Party** action
        - Passing laws they ideologically support
        - Conceding to their demands during events
        - Strong polls (everyone wants to ride a winner)

        ### If a partner leaves
        - You lose all their seats from coalition immediately
        - Government Stability drops 20 points
        - You may fall below 121 majority — minority government
        - Bills become much harder to pass
        """)

    # ---- Events & Crises ----
    with tabs[5]:
        st.markdown("""
        ### Crisis events

        Random events fire based on your country's state. Examples:
        - 🔥 **Energy Price Shock** (when inflation high)
        - 🔍 **Minister Corruption Leak** (when corruption high)
        - 💥 **No-Confidence Motion** (when stability low)
        - 🛡️ **Border Incident** (when security risk rising)
        - 🗣️ **Capital Protests** (when social tension high)
        - 🏭 **Major Factory Closure** (when unemployment high)

        Each event has **2-4 choice options**, each with different consequences:
        - National indicator changes (trust, stability, etc)
        - Voter group sympathies shift
        - Coalition partner reactions
        - News coverage
        - Sometimes: trigger early elections

        ### Severity levels
        - 🟢 **Minor** (1) — small impact
        - 🟡 **Moderate** (2)
        - 🟠 **Serious** (3)
        - 🔴 **Critical** (4)
        - 🟣 **Existential** (5) — government-ending stakes

        ### Important rule
        **You CANNOT advance the day with active events unfinished.**
        Always go to the **🚨 Events** tab to resolve them first.
        """)

    # ---- Elections ----
    with tabs[6]:
        st.markdown("""
        ### Election day

        After ~1460 days (4 years), or if **early elections** are triggered, you face the voters.

        ### How votes are calculated
        Each party's vote share comes from:
        - Their **current poll number**
        - **Economic performance** (GDP, inflation, unemployment)
        - **Public trust** (helps incumbents, hurts in crisis)
        - **Corruption perception** (hurts old parties, helps reformers)
        - **Random shock** (Gauss noise — uncertainty)

        ### Seat allocation
        - **D'Hondt method** with **4% national threshold**
        - Parties below 4% get **zero seats** (their votes are wasted)
        - 240 total seats distributed proportionally

        ### Coalition formation after election
        After results, you see:
        - All viable coalition options including your party
        - Pick a coalition (game auto-picks best for you)
        - New term begins, election clock resets to 4 years

        ### Pre-election checks (months before)
        Use the **🗳️ Elections** tab to see:
        - Current polls
        - Forecast vote ranges (low/central/high)
        - Projected seat counts
        - Coalition calculator — which combinations could form a majority

        ### Early elections
        Triggered by:
        - Successful no-confidence motion
        - Some event choices (e.g., "Call snap elections")
        - Coalition collapse (sometimes)
        """)

    # ---- Tips ----
    with tabs[7]:
        st.markdown("""
        ### Strategic tips

        #### 🎯 Opening moves
        - **Don't propose huge bills on day 1** — wait until you understand the chamber
        - First, read **MP profiles** in Parliament → Active Bills → MP-by-MP
        - **Build relationships** with persuadable MPs before you need their votes
        - Save PC for the first crisis (it WILL come within 30 days)

        #### 💼 Political capital management
        - Big bills (anti-corruption, judicial reform) cost 12-15 PC
        - Don't spend below 20 PC unless you have a plan
        - PC refills +6 every 30 days, so plan a monthly budget

        #### 🤝 Lobbying efficiency
        - **Meet Individual MP** is usually the best ROI (1 AP / 1 PC)
        - Target opposition MPs with high persuadability (>55) and high corruption risk (>50)
        - Don't horse-trade unless you absolutely need the bill — corruption stat hurts long-term

        #### 📊 Reading the indicators
        - 🟢 **Public Trust** > 50 = stable
        - 🟢 **Government Stability** > 60 = comfortable
        - 🟥 **Inflation** > 9% = social tension rises fast
        - 🟥 **Corruption** > 65 = trust drops, EU funds at risk
        - 🟥 **NF poll** > 25% = nationalists are surging, big risk

        #### 🚨 Crisis priority
        - **Always resolve events before advancing the day**
        - Hard severity events should be your top priority
        - "Difficult" choices often have better long-term outcomes

        #### 🏛️ Coalition keepers
        - Pass at least one **left-leaning** law to keep SD happy (minimum wage, healthcare)
        - Pass at least one **environmental** law for GF (green energy, transparency)
        - Don't pass anti-business laws or LD will leave
        - **Mix the agenda** — alternate ideological wins

        #### ⏰ Election prep
        - Last 6 months before election: focus on **polls**, not laws
        - Use **Rally Supporters** and **National Address** liberally
        - Avoid risky reforms — they can backfire
        """)

    st.markdown("---")

    if on_continue is None:
        st.info("Use the sidebar to navigate. Click 'Main Menu' to return to game start.")
    else:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("✅ Got it — Start Playing!", type="primary", use_container_width=True):
                on_continue()
                st.rerun()
