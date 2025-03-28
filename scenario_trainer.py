
import streamlit as st
import sqlite3
import pandas as pd
import difflib

st.set_page_config(page_title="Classroom Scenario Trainer", layout="wide")

# Connect to SQLite
conn = sqlite3.connect("scenarios.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        model_answer TEXT,
        category TEXT
    )
""")
conn.commit()

# In-memory responses
if "responses" not in st.session_state:
    st.session_state.responses = {}

def add_scenario(description, model_answer, category):
    cursor.execute("INSERT INTO scenarios (description, model_answer, category) VALUES (?, ?, ?)",
                   (description, model_answer, category))
    conn.commit()

def delete_scenario(scenario_id):
    cursor.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
    conn.commit()

def get_all_categories():
    cursor.execute("SELECT DISTINCT category FROM scenarios")
    return [row[0] for row in cursor.fetchall()]

def get_scenarios(category=None):
    if category and category != "All":
        cursor.execute("SELECT id, description, model_answer, category FROM scenarios WHERE category=?", (category,))
    else:
        cursor.execute("SELECT id, description, model_answer, category FROM scenarios")
    return cursor.fetchall()

def get_feedback(model_answer, trainee_answer):
    model_words = set(model_answer.lower().split())
    trainee_words = set(trainee_answer.lower().split())
    common = model_words & trainee_words
    coverage = len(common) / len(model_words) * 100 if model_words else 0
    similarity = difflib.SequenceMatcher(None, model_answer.lower(), trainee_answer.lower()).ratio() * 100

    feedback = f"🔍 **Overlap**: {coverage:.1f}% | **Similarity**: {similarity:.1f}%\n\n"
    if coverage > 60 and similarity > 60:
        feedback += "✅ Strong response. You've identified many key ideas."
    elif coverage > 30:
        feedback += "🟡 You're on the right track but missing some key elements. Review the model answer."
    else:
        feedback += "🔴 Consider revisiting how to respond to this scenario. Focus on understanding and next steps."
    return feedback

# Sidebar - Add or delete scenarios
with st.sidebar:
    st.header("🛠 Manage Scenarios")
    description = st.text_area("Scenario Description")
    model_answer = st.text_area("Model Answer")
    category = st.selectbox("Category", ["Behaviour", "Assessment", "Safeguarding", "SEND", "Pedagogy", "Other"])
    if st.button("Add Scenario"):
        if description and model_answer:
            add_scenario(description, model_answer, category)
            st.success("Scenario added!")
        else:
            st.warning("Please complete all fields.")

    st.markdown("---")
    st.subheader("🗑 Delete Scenario")
    scenarios = get_scenarios()
    if scenarios:
        del_id = st.selectbox("Select a scenario to delete", [f"{sid}: {desc[:40]}" for sid, desc, _, _ in scenarios])
        del_sid = int(del_id.split(":")[0])
        if st.button("Delete Selected"):
            delete_scenario(del_sid)
            st.success(f"Scenario {del_sid} deleted.")

# Main app interface for trainees
st.title("👩‍🏫 Classroom Scenario Trainer")

trainee_name = st.text_input("Enter your name (for response tracking)", key="trainee_name")
if not trainee_name:
    st.warning("Please enter your name to submit responses.")

selected_category = st.selectbox("Filter by Category", ["All"] + get_all_categories())

scenarios = get_scenarios(selected_category)
if not scenarios:
    st.info("No scenarios found.")
else:
    for sid, desc, model_ans, cat in scenarios:
        with st.expander(f"{cat} - Scenario {sid}: {desc}"):
            response = st.text_area("✍️ Your response:", key=f"resp_{sid}")
            if st.button("Submit", key=f"submit_{sid}") and trainee_name:
                st.session_state.responses[(sid, trainee_name)] = response
                st.success("Response saved.")

            if (sid, trainee_name) in st.session_state.responses:
                st.subheader("💬 Feedback")
                feedback = get_feedback(model_ans, st.session_state.responses[(sid, trainee_name)])
                st.markdown(feedback)
                st.markdown(f"✅ **Model Answer**: {model_ans}")

# Export responses
if st.session_state.responses:
    st.subheader("📦 View/Export Trainee Responses")
    df = pd.DataFrame([
        {
            "Scenario ID": sid,
            "Trainee": name,
            "Response": response
        }
        for (sid, name), response in st.session_state.responses.items()
    ])
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Responses as CSV", csv, "trainee_responses.csv", "text/csv")
