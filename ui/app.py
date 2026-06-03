import streamlit as st
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from graph.workflow import run_travel_planner
from agents.scorer import save_user_feedback

st.set_page_config(page_title="Travel Itinerary Planner", page_icon="🧭", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    #MainMenu,footer,header,.stDeployButton,[data-testid="stToolbar"]{display:none!important}
    .stApp{font-family:'Inter',sans-serif}
</style>
""", unsafe_allow_html=True)

CITIES = ["Goa","Delhi","Jaipur","Kerala","Manali","Varanasi","Mumbai","Udaipur","Rishikesh","Agra"]
INTERESTS = ["Beach","Heritage","Food","Adventure","Shopping","Nature","Religious","Nightlife","Cafes","Culture"]


def format_itinerary_bullets(raw, num_days):
    """Parse LLM output into exactly N day bullet points."""
    lines = raw.strip().split("\n")
    
    days_content = {}
    current_day = None
    budget_section = []
    notes_section = []
    header = ""
    in_budget = False
    sources_line = ""
    
    for line in lines:
        s = line.strip()
        if not s or s == "---":
            continue
        
        # Trip header
        if s.startswith("📍"):
            header = s
            continue
        
        # Day header
        day_match = None
        if "Day" in s:
            import re
            dm = re.search(r"Day\s*(\d+)", s)
            if dm:
                day_match = int(dm.group(1))
        
        if day_match:
            current_day = day_match
            day_title = s.replace("🗓️", "").strip()
            if current_day not in days_content:
                days_content[current_day] = {"title": day_title, "activities": []}
            in_budget = False
            continue
        
        # Budget section
        if "Budget" in s and ("💰" in s or "Breakdown" in s):
            in_budget = True
            continue
        
        if in_budget:
            if s.startswith("📋") or s.startswith("Sources"):
                sources_line = s
                in_budget = False
            elif s.startswith("─") or s.startswith("━"):
                continue
            elif "Note" in s[:10] or s.startswith("**Note") or s.startswith("*"):
                notes_section.append(s)
                in_budget = False
            else:
                budget_section.append(s)
            continue
        
        # Notes
        if "Note" in s[:10] or s.startswith("**Note") or s.startswith("*Note"):
            notes_section.append(s)
            continue
        
        # Sources
        if s.startswith("📋"):
            sources_line = s
            continue
        
        # Activity lines for current day
        if current_day and current_day in days_content:
            if any(s.startswith(e) for e in ["🌅","🌞","🌆","🍽️","🏨"]):
                days_content[current_day]["activities"].append(s)
            elif len(s) > 5:
                days_content[current_day]["activities"].append(s)
    
    # Build final markdown
    md = ""
    if header:
        md += f"### {header}\n\n"
    
    for day_num in sorted(days_content.keys()):
        day = days_content[day_num]
        md += f"**{day['title']}**\n\n"
        for act in day["activities"]:
            md += f"  - {act}\n"
        md += "\n"
    
    if budget_section:
        md += "**💰 Budget Breakdown**\n\n"
        for b in budget_section:
            md += f"  - {b}\n"
        md += "\n"
    
    if sources_line:
        md += f"**{sources_line}**\n\n"
    
    if notes_section:
        for n in notes_section:
            md += f"> 💡 {n}\n"
    
    return md


def pipe_text(step):
    agents = ["🧠 Supervisor","🔍 Retriever","✍️ Planner","✅ Validator","📊 Scorer"]
    parts = []
    for i, a in enumerate(agents):
        if i < step:
            parts.append(f"~~{a}~~ ✓")
        elif i == step:
            parts.append(f"**{a}** ⟵")
        else:
            parts.append(a)
    return " → ".join(parts)


# ══════════════════════════════════════
# SESSION STATE — Controls the step flow
# ══════════════════════════════════════
if "step" not in st.session_state:
    st.session_state.step = 0
if "city" not in st.session_state:
    st.session_state.city = None
if "days" not in st.session_state:
    st.session_state.days = None
if "budget" not in st.session_state:
    st.session_state.budget = None
if "interests" not in st.session_state:
    st.session_state.interests = None
if "result" not in st.session_state:
    st.session_state.result = None


# ══════════════════════════════════════
# HEADER — Always visible
# ══════════════════════════════════════
st.title("🧭 Travel Itinerary Planner")
st.caption("Multi-Agent RAG System — AWS Bedrock · LangGraph · ChromaDB · 56 Destinations · 10 Cities")
st.divider()


# ══════════════════════════════════════
# STEP 0: Landing — "Plan My Trip" button
# ══════════════════════════════════════
if st.session_state.step == 0:
    st.markdown("### Ready to plan your next adventure?")
    st.markdown("Click below to start building your personalized, AI-powered travel itinerary.")
    st.markdown("")
    if st.button("✦  Plan My Trip", use_container_width=True, type="primary"):
        st.session_state.step = 1
        st.rerun()


# ══════════════════════════════════════
# STEP 1: Where do you want to go?
# ══════════════════════════════════════
elif st.session_state.step == 1:
    st.markdown("### 🏙️ Where do you want to go?")
    city = st.selectbox("Choose your destination", CITIES, label_visibility="collapsed")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 0
            st.rerun()
    with c2:
        if st.button("Next →", use_container_width=True, type="primary"):
            st.session_state.city = city
            st.session_state.step = 2
            st.rerun()


# ══════════════════════════════════════
# STEP 2: How many days?
# ══════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown(f"### 📅 How many days in **{st.session_state.city}**?")
    days = st.number_input("Number of days", min_value=1, max_value=7, value=3, label_visibility="collapsed")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with c2:
        if st.button("Next →", use_container_width=True, type="primary"):
            st.session_state.days = days
            st.session_state.step = 3
            st.rerun()


# ══════════════════════════════════════
# STEP 3: What's your budget?
# ══════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown(f"### 💰 What's your budget for **{st.session_state.days} days** in **{st.session_state.city}**?")
    budget = st.number_input("Budget in ₹", min_value=3000, max_value=50000, value=15000, step=1000, label_visibility="collapsed")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with c2:
        if st.button("Next →", use_container_width=True, type="primary"):
            st.session_state.budget = budget
            st.session_state.step = 4
            st.rerun()


# ══════════════════════════════════════
# STEP 4: What are your interests?
# ══════════════════════════════════════
elif st.session_state.step == 4:
    st.markdown(f"### 🎯 What interests you in **{st.session_state.city}**?")
    interests = st.multiselect("Pick your interests", INTERESTS, default=["Heritage", "Food"], label_visibility="collapsed")
    
    # Show summary before generating
    st.divider()
    st.markdown("#### Your Trip Summary")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Destination", st.session_state.city)
    sc2.metric("Duration", f"{st.session_state.days} days")
    sc3.metric("Budget", f"₹{st.session_state.budget:,}")
    sc4.metric("Interests", f"{len(interests)} picked")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with c2:
        if st.button("🚀 Generate Itinerary", use_container_width=True, type="primary"):
            st.session_state.interests = interests
            st.session_state.step = 5
            st.rerun()


# ══════════════════════════════════════
# STEP 5: Generating + Results
# ══════════════════════════════════════
elif st.session_state.step == 5:
    city = st.session_state.city
    days = st.session_state.days
    budget = st.session_state.budget
    interests = st.session_state.interests or ["sightseeing"]
    
    interests_str = ", ".join(x.lower() for x in interests)
    query = f"{days} day trip to {city} under {budget} with {interests_str}"
    
    # Generate only once
    if st.session_state.result is None:
        st.markdown("### ⏳ Generating your itinerary...")
        st.info(f"🔎 *{query}*")
        
        progress = st.empty()
        status = st.empty()
        
        steps = [
            (0, "🧠 Extracting travel intent..."),
            (1, "🔍 Searching knowledge base..."),
            (2, "✍️ Crafting itinerary..."),
        ]
        for idx, msg in steps:
            progress.markdown(pipe_text(idx))
            status.caption(msg)
            time.sleep(0.4)
        
        with st.spinner("AI agents are working..."):
            result = run_travel_planner(query)
        
        progress.markdown(pipe_text(3))
        status.caption("✅ Validating accuracy...")
        time.sleep(0.3)
        progress.markdown(pipe_text(4))
        status.caption("📊 Scoring faithfulness...")
        time.sleep(0.3)
        progress.markdown(pipe_text(5))
        status.empty()
        progress.empty()
        
        st.session_state.result = result
        st.rerun()
    
    # ── Show results ──
    result = st.session_state.result
    
    st.success("✅ Your itinerary is ready!")
    
    # Trip summary
    st.markdown(f"### 📍 {city} · {days} Days · ₹{budget:,}")
    st.divider()
    
    # Metrics
    st.markdown("#### 📊 Quality Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall Accuracy", f"{result.get('overall_accuracy',0):.0%}")
    m2.metric("Faithfulness", f"{result.get('faithfulness_score',0):.0%}")
    m3.metric("Relevance", f"{result.get('relevance_score',0):.0%}")
    m4.metric("Source Coverage", f"{result.get('source_coverage',0):.0%}")
    
    val = result.get("validation_result", "PASS")
    conf = result.get("confidence_level", "MEDIUM")
    ve = {"PASS":"✅","REVISE":"🔄","REJECT":"❌"}.get(val,"❓")
    ce = {"HIGH":"🟢","MEDIUM":"🟡","LOW":"🔴"}.get(conf,"⚪")
    st.markdown(f"**Validation:** {ve} {val}  ·  **Confidence:** {ce} {conf}  ·  **Revisions:** {result.get('revision_count',0)}  ·  **Sources:** {len(result.get('sources_used',[]))}  ·  **Log:** #{result.get('log_id','—')}")
    
    st.divider()
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Itinerary", "📊 Scores", "📚 Sources", "💬 Feedback"])
    
    with tab1:
        disclaimer = result.get("disclaimer", "")
        if disclaimer:
            st.warning(disclaimer)
        
        raw = result.get("itinerary", "No itinerary generated.")
        formatted = format_itinerary_bullets(raw, days)
        st.markdown(formatted)
    
    with tab2:
        st.markdown("#### Quality Breakdown")
        scores = {
            "Faithfulness": result.get("faithfulness_score", 0),
            "Relevance": result.get("relevance_score", 0),
            "Source Coverage": result.get("source_coverage", 0),
            "Overall Accuracy": result.get("overall_accuracy", 0),
        }
        for label, score in scores.items():
            pct = int(score * 100)
            cl, cb, cv = st.columns([1, 3, 0.5])
            cl.markdown(f"**{label}**")
            cb.progress(score)
            cv.markdown(f"**{pct}%**")
        
        st.divider()
        st.markdown("#### Pipeline Details")
        intent = result.get("intent", {})
        bg = intent.get("budget", "N/A")
        bf = f"₹{bg:,}" if isinstance(bg, int) else f"₹{bg}"
        d1, d2 = st.columns(2)
        with d1:
            st.markdown(f"- **Destination:** {intent.get('city','—')}\n- **Duration:** {intent.get('days','—')} days\n- **Budget:** {bf}\n- **Interests:** {', '.join(intent.get('interests',[]))}")
        with d2:
            st.markdown(f"- **Validation:** {result.get('validation_result','—')}\n- **Confidence:** {result.get('confidence_level','—')}\n- **Revisions:** {result.get('revision_count',0)}\n- **Sources:** {len(result.get('sources_used',[]))}\n- **Log ID:** #{result.get('log_id','—')}")
    
    with tab3:
        st.markdown("#### Source Citations")
        st.caption("Every recommendation is grounded in verified source data.")
        ctx = result.get("context", [])
        im = {"attractions":"📍","hotels":"🏨","food":"🍽️","transport":"🚗"}
        for ch in ctx:
            m = ch.get("metadata", {})
            icon = im.get(m.get("source",""), "📄")
            with st.expander(f"{icon} {m.get('name','—')}  —  `{m.get('source','')}` · `{m.get('city','')}` · ₹{m.get('cost',0)}"):
                st.markdown(ch.get("document","")[:200] + "…")
    
    with tab4:
        st.markdown("#### Was this itinerary helpful?")
        st.caption("Your feedback improves future recommendations.")
        rating = st.radio("Rate", [1,2,3,4,5], format_func=lambda x:"⭐"*x, horizontal=True, label_visibility="collapsed")
        fb = st.text_area("Comments (optional)", placeholder="What did you like? What could be improved?", height=80)
        if st.button("Submit Feedback"):
            lid = result.get("log_id", 0)
            if lid:
                save_user_feedback(lid, rating, fb)
                st.success(f"Thank you! Your {rating}-star rating has been recorded.")
    
    # Start over button
    st.divider()
    if st.button("🔄 Plan Another Trip", use_container_width=True):
        st.session_state.step = 0
        st.session_state.result = None
        st.rerun()

# ══════════════════════════════════════
# FOOTER
# ══════════════════════════════════════
st.divider()
st.caption("Built with LangGraph · AWS Bedrock · ChromaDB · Streamlit — Multi-Agent RAG System POC")
