import os
import json
from datetime import date
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="StudyPilot AI", page_icon="🎓", layout="wide")

st.title("🎓 StudyPilot AI")
st.caption("An agentic study assistant that routes your goal to the right study tool.")

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "Groq API key",
        value=os.getenv("GROQ_API_KEY", ""),
        type="password",
        help="Get a key from console.groq.com. Your key is used only for this session unless you save it in your environment."
    )
    model="openai/gpt-oss-120b"
    st.markdown("---")
    st.markdown("**Agent workflow**")
    st.write("1. Identify the task")
    st.write("2. Route to a specialist tool")
    st.write("3. Generate and validate a structured response")

TOOLS = {
    "Tutor": "Explain a concept clearly, step by step, using an intuitive example and equations where appropriate.",
    "Quiz Generator": "Create a quiz from the topic. Include the requested number of MCQs, four options each, correct answer, and a short explanation.",
    "Study Planner": "Create a realistic study schedule using the subjects, deadline, and available study time supplied by the user. Use a table.",
    "Notes Summarizer": "Summarize the supplied notes into key ideas, definitions, important equations, and a short revision checklist."
}

def call_ai(task, prompt, api_key, model):
    if not api_key:
        st.error("Add a Groq API key in the sidebar to run the AI agent.")
        st.info("Get a free API key at https://console.groq.com/keys")
        return None
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        system = f"""You are StudyPilot AI, a careful student-learning assistant.
The agent has selected the specialist tool: {task}.
Tool objective: {TOOLS[task]}
Follow the objective closely. Use clear headings and concise, accurate educational language.
For technical topics, state assumptions and units. Do not invent citations or claim to have read files that were not supplied."""
        result = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
        )
        return result.choices[0].message.content
    except Exception as e:
        st.error(f"AI request failed: {e}")
        return None

def route_task(goal):
    """Simple intent router: selects a specialist tool based on the user's goal."""
    text = goal.lower()
    if any(k in text for k in ["summarize", "summary", "condense", "revision notes"]):
        return "Notes Summarizer"
    if any(k in text for k in ["quiz", "mcq", "multiple choice", "test me"]):
        return "Quiz Generator"
    if any(k in text for k in ["timetable", "study plan", "schedule", "plan my study"]):
        return "Study Planner"
    return "Tutor"

tabs = st.tabs(["🤖 Agent Workspace", "🧰 Direct Tools", "ℹ️ About"])

with tabs[0]:
    st.subheader("Tell the agent what you want to achieve")
    goal = st.text_area(
        "Your goal",
        placeholder="Example: Make a 5-question MCQ quiz on thermodynamics, with explanations.",
        height=110,
        key="agent_goal"
    )
    col1, col2 = st.columns([1, 3])
    with col1:
        run_agent = st.button("Run agent", type="primary", use_container_width=True)
    with col2:
        st.caption("The router chooses a specialist tool from your request. You can review the selected tool before running.")
    if goal.strip():
        selected = route_task(goal)
        st.info(f"**Agent route selected:** {selected}")
        st.caption(f"Tool objective: {TOOLS[selected]}")
    if run_agent:
        if not goal.strip():
            st.warning("Enter a goal first.")
        else:
            selected = route_task(goal)
            with st.spinner(f"Agent is using {selected}..."):
                answer = call_ai(selected, goal, api_key, model)
            if answer:
                st.markdown("### Agent result")
                st.markdown(answer)
                st.download_button("Download result (.md)", answer, file_name="studypilot_result.md", mime="text/markdown")

with tabs[1]:
    st.subheader("Run a specialist tool directly")
    tool = st.selectbox("Choose a tool", list(TOOLS.keys()))
    if tool == "Tutor":
        topic = st.text_input("Topic", placeholder="e.g., Brayton cycle")
        level = st.selectbox("Explanation level", ["Beginner", "Undergraduate engineering", "Exam revision"])
        extra = st.text_area("Specific question (optional)", placeholder="What should the explanation focus on?")
        prompt = f"Topic: {topic}\nLevel: {level}\nSpecific question: {extra}"
    elif tool == "Quiz Generator":
        topic = st.text_input("Quiz topic", placeholder="e.g., heat transfer")
        n = st.slider("Number of questions", 3, 15, 5)
        difficulty = st.selectbox("Difficulty", ["Easy", "Moderate", "Hard", "Mixed"])
        prompt = f"Create {n} MCQs on {topic}. Difficulty: {difficulty}. Include four options, correct answer, and explanation for each."
    elif tool == "Study Planner":
        subjects = st.text_area("Subjects and topics", placeholder="Thermodynamics, manufacturing, fluid mechanics...")
        hours = st.slider("Study hours per day", 1, 10, 3)
        deadline = st.date_input("Target date", value=date.today())
        prompt = f"Create a study plan for these subjects: {subjects}\nAvailable study time: {hours} hours per day.\nTarget date: {deadline.isoformat()}.\nAsk no follow-up; state any assumptions and create a practical table."
    else:
        notes = st.text_area("Paste your notes", height=220, placeholder="Paste lecture notes or textbook excerpts here...")
        style = st.selectbox("Summary style", ["Exam revision", "Bullet-point summary", "Detailed structured notes"])
        prompt = f"Summarize these notes. Style: {style}.\n\nNOTES:\n{notes}"

    if st.button("Run selected tool", key="direct_run", type="primary"):
        prompt_ready = prompt.strip()
        if not prompt_ready or (tool == "Tutor" and not topic.strip()) or (tool == "Quiz Generator" and not topic.strip()) or (tool == "Notes Summarizer" and not notes.strip()):
            st.warning("Please fill in the required field(s).")
        else:
            with st.spinner(f"Running {tool}..."):
                answer = call_ai(tool, prompt_ready, api_key, model)
            if answer:
                st.markdown("### Result")
                st.markdown(answer)
                st.download_button("Download result (.md)", answer, file_name=f"{tool.lower().replace(' ', '_')}.md", mime="text/markdown", key="download_direct")

with tabs[2]:
    st.subheader("Project overview")
    st.write("StudyPilot AI demonstrates an agentic workflow: a request is interpreted, routed to a specialist capability, and passed to an AI model to produce a task-specific result.")
    st.markdown("**Core concepts demonstrated**")
    st.markdown("- Intent routing and tool selection\n- Specialized task prompts\n- AI model integration\n- User input validation\n- Exportable outputs")
    st.warning("Educational prototype: verify technical facts before relying on them for exams or engineering decisions.")
