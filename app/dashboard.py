# app/dashboard.py

#---------------- PATH FIX FOR LOCAL RUN ----------------
import sys, os
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))      # app/
PARENT_DIR = os.path.dirname(ROOT_DIR)                     # project root
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
    

import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from app.file_loader import load_text_from_file
from app.nlp_service import analyze_text_all, translate_text
from app.cosmos_client import save_analysis_to_cosmos


# ---------------- Page Setup ----------------
st.set_page_config(
    page_title="Azure NLP Text Analytics Dashboard",
    layout="wide"
)

st.title("🔍 Azure NLP Text Analytics Dashboard")
st.caption("Powered by Azure AI Language, Azure OpenAI, and Cosmos DB")


# ---------------- Session State ----------------
if "uploaded_text" not in st.session_state:
    st.session_state["uploaded_text"] = None

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "source_type" not in st.session_state:
    st.session_state["source_type"] = None

if "file_name" not in st.session_state:
    st.session_state["file_name"] = None


# ---------------- Sidebar ----------------
st.sidebar.header("📥 Input Options")

input_mode = st.sidebar.radio(
    "Select Input Type",
    ["Paste text", "Upload file"],
    index=1
)

if input_mode == "Paste text":
    default_text = (
        "Hello, my name is Rahul Sharma. I currently live in Hyderabad and work as a data analyst "
    "at a healthcare startup. My contact number is 98765-12345 and my email is rahul.sharma@example.com. "
    "I am planning to travel to Bengaluru next week for a client meeting. Overall, I feel excited "
    "but a bit nervous about the presentation I need to deliver. "
    "The company is particularly interested in patient data trends, risk predictions, and improving "
    "medical decision support systems using AI solutions."
    )
    text = st.sidebar.text_area("Enter text:", value=default_text, height=150)

    if st.sidebar.button("Analyze Text"):
        st.session_state["uploaded_text"] = text
        st.session_state["analysis_result"] = None
        st.session_state["source_type"] = "text"
        st.session_state["file_name"] = None

else:
    uploaded_file = st.sidebar.file_uploader(
        "Upload file",
        type=["txt", "pdf", "docx", "csv", "json"]
    )

    if uploaded_file is not None and st.sidebar.button("Analyze File"):
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        st.session_state["uploaded_text"] = load_text_from_file(tmp_path)
        st.session_state["analysis_result"] = None
        st.session_state["source_type"] = "file"
        st.session_state["file_name"] = uploaded_file.name


# Stop if no input
if not st.session_state["uploaded_text"]:
    st.info("⬅️ Add text or upload a file to start analysis.")
    st.stop()


# ---------------- Run NLP Analysis ----------------
if st.session_state["analysis_result"] is None:
    with st.spinner("Running Azure NLP Analysis..."):
        st.session_state["analysis_result"] = analyze_text_all(
            st.session_state["uploaded_text"]
        )

result = st.session_state["analysis_result"]
uploaded_text = st.session_state["uploaded_text"]


# ---------------- UI Tabs ----------------
tabs = st.tabs([
    "🧭 Overview",
    "🌐 Language",
    "😊 Sentiment",
    "🏷 Classification",
    "🔑 Key Phrases",
    "🏷 Entities",
    "🛡 PII Detection",
    "🌍 Translation",
    "📄 Raw Text & JSON",
    "💾 Save / Export"
])

# ---------------- TAB: Overview ----------------
with tabs[0]:
    st.header("🧭 Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Summary (GPT-style)")
        summary = result.get("summary", [])
        if summary:
            for i, sent in enumerate(summary, start=1):
                st.write(f"{i}. {sent}")
        else:
            st.write("No summary available.")

    with col2:
        st.subheader("Detected Topics")
        if result.get("classification"):
            st.write(f"**Predicted Category:** `{result['classification']['label']}`")
            st.write(f"**Confidence:** {result['classification']['confidence']:.2f}")
        else:
            st.write("No classification detected.")


# ---------------- TAB: Language ----------------
with tabs[1]:
    st.header("🌐 Language Detection")

    lang = result.get("language", {})
    if lang:
        st.metric("Primary Language", f"{lang['name']} ({lang['iso6391']})")
        st.metric("Confidence", f"{lang['confidence']:.2f}")

    st.subheader("Multi-language Breakdown")
    ml = result.get("multi_language", [])
    if ml:
        ml_df = pd.DataFrame(ml).set_index("language")[["confidence"]]
        st.bar_chart(ml_df)
    else:
        st.info("No multilingual content detected.")


# ---------------- TAB: Sentiment ----------------
with tabs[2]:
    st.header("😊 Sentiment Analysis")

    sent_scores = result["sentiment"]["scores"]
    sentiment_df = pd.DataFrame({
        "sentiment": ["positive", "neutral", "negative"],
        "score": [
            sent_scores["positive"],
            sent_scores["neutral"],
            sent_scores["negative"],
        ],
    }).set_index("sentiment")

    st.bar_chart(sentiment_df)


# ---------------- TAB: Classification ----------------
with tabs[3]:
    st.header("🏷 Text Classification")

    cls = result.get("classification")
    if cls:
        st.write(f"**Label:** {cls['label']}")
        st.write(f"**Confidence:** {cls['confidence']:.2f}")
        st.write(f"**Explanation:** {cls['explanation']}")
    else:
        st.info("No classification available.")


# ---------------- TAB: Key Phrases ----------------
with tabs[4]:
    st.header("🔑 Key Phrases")

    kp = result.get("key_phrases", [])
    if kp:
        cols = st.columns(3)
        for i, phrase in enumerate(kp):
            cols[i % 3].markdown(f"- `{phrase}`")
    else:
        st.write("No key phrases found.")


# ---------------- TAB: Entities ----------------
with tabs[5]:
    st.header("🏷 Named Entities")

    entities = result.get("entities", [])
    if entities:
        st.dataframe(pd.DataFrame(entities), use_container_width=True)
    else:
        st.write("No entities detected.")


# ---------------- TAB: PII ----------------
with tabs[6]:
    st.header("🛡 PII Detection")

    pii = result.get("pii", [])
    if pii:
        st.dataframe(pd.DataFrame(pii), use_container_width=True)
    else:
        st.write("No PII entities found.")


# ---------------- TAB: Translation ----------------
with tabs[7]:
    st.header("🌍 Translate Text")

    language_map = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "Hindi": "hi",
        "Arabic": "ar",
        "Japanese": "ja",
        "Tamil": "ta",
        "Telugu": "te",
        "German": "de",
        "Chinese": "zh",
    }

    selected_lang = st.selectbox(
        "Select output language",
        list(language_map.keys())
    )

    translated_output = translate_text(uploaded_text, language_map[selected_lang])
    st.success(translated_output)


# ---------------- TAB: Raw Data ----------------
with tabs[8]:
    st.header("📄 Raw Text")
    st.text(uploaded_text[:5000])

    st.subheader("JSON Output")
    st.json(result)


# ---------------- TAB: Save / Export ----------------
with tabs[9]:
    st.header("💾 Save Analysis")

    if st.button("Save to Cosmos DB"):
        try:
            doc_id = save_analysis_to_cosmos(
                result=result,
                raw_text=uploaded_text,
                source_type=st.session_state["source_type"],
                file_name=st.session_state["file_name"]
            )
            st.success(f"Saved! Document ID: {doc_id}")
        except Exception as e:
            st.error(f"Failed to save: {e}")

    result_json = json.dumps(result, indent=2, ensure_ascii=False)

    if "json_cache" not in st.session_state:
        st.session_state["json_cache"] = result_json.encode("utf-8")

    st.download_button(
        "⬇️ Download results as JSON",
        st.session_state["json_cache"],
        file_name="nlp_analysis_result.json",
        mime="application/json",
        key="json_download"
    )
