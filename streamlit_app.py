import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="KenByte Research Agent",
    page_icon="🔍",
    layout="centered"
)

st.title("🔍 KenByte Research Agent")
st.caption("Multi-source AI research powered by Google + Reddit")

@st.cache_resource(show_spinner="Loading agent...")
def load_graph():
    from main import graph
    return graph

graph = load_graph()

if "history" not in st.session_state:
    st.session_state.history = []

for entry in st.session_state.history:
    with st.chat_message("user"):
        st.write(entry["question"])
    with st.chat_message("assistant"):
        st.markdown(entry["answer"])
        with st.expander("📊 Google Analysis"):
            st.write(entry.get("google_analysis") or "N/A")
        with st.expander("💬 Reddit Analysis"):
            st.write(entry.get("reddit_analysis") or "N/A")

question = st.chat_input("Ask me anything...")

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        status = st.status("🚀 Researching...", expanded=True)
        with status:
            st.write("🔍 Launching Google and Reddit searches in parallel...")

            initial_state = {
                "messages":             [{"role": "user", "content": question}],
                "user_question":        question,
                "google_results":       None,
                "reddit_results":       None,
                "selected_reddit_urls": None,
                "reddit_post_data":     None,
                "google_analysis":      None,
                "reddit_analysis":      None,
                "final_answer":         None,
            }

            try:
                final_state = graph.invoke(initial_state)
                status.update(label="✅ Research complete!", state="complete")
            except Exception as e:
                status.update(label="❌ Error during research", state="error")
                st.error(f"Agent error: {e}")
                st.stop()

        final_answer    = final_state.get("final_answer") or "No answer generated."
        google_analysis = final_state.get("google_analysis") or "N/A"
        reddit_analysis = final_state.get("reddit_analysis") or "N/A"

        st.markdown(final_answer)
        with st.expander("📊 Google Analysis"):
            st.write(google_analysis)
        with st.expander("💬 Reddit Analysis"):
            st.write(reddit_analysis)

    st.session_state.history.append({
        "question":        question,
        "answer":          final_answer,
        "google_analysis": google_analysis,
        "reddit_analysis": reddit_analysis,
    })
