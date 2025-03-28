
import streamlit as st
import sqlite3
import pandas as pd
import difflib

st.set_page_config(page_title="Classroom Scenario Trainer", layout="wide")

# Connect to SQLite
conn = sqlite3.connect("scenarios.db", check_same_thread=False)
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT,
        model_answer TEXT,
        category TEXT
    )
""")
conn.commit()

def add_scenario(description, model_answer, category):
    cursor.execute("INSERT INTO scenarios (description, model_answer, category) VALUES (?, ?, ?)",
                   (description, model_answer, category))
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

with st.sidebar:
    st.header("➕ Add a New Scenario")
    description = st.text_area("Scenario Description")
    model_answer = st.text_area("Model Answer")
    category = st.selectbox("Category", ["Behaviour", "Assessment", "Safeguarding", "SEND", "Pedagogy", "Other"])
    if st.button("Add Scenario"):
        if description and model_answer:
            add_scenario(description, model_answer, category)
            st.success("Scenario added!")
        else:
            st.warning("Please complete all fields.")

st.title("👩‍🏫 Classroom Scenario Trainer")
all_categories = get_all_categories()
selected_category = st.selectbox("Filter by Category", ["All"] + all_categories)

scenarios = get_scenarios(selected_category)
if not scenarios:
    st.info("No scenarios found.")
else:
    for sid, desc, model_ans, cat in scenarios:
        with st.expander(f"{cat} - Scenario {sid}: {desc}"):
            response = st.text_area("✍️ Your response:", key=f"resp_{sid}")
            if st.button("Submit", key=f"submit_{sid}"):
                st.session_state[f"submitted_{sid}"] = response

            if f"submitted_{sid}" in st.session_state:
                st.subheader("💬 Feedback")
                feedback = get_feedback(model_ans, st.session_state[f"submitted_{sid}"])
                st.markdown(feedback)
                st.markdown(f"✅ **Model Answer**: {model_ans}")
