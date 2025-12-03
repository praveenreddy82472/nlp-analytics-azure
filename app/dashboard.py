# app/dashboard.py

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
st.write("Analyze text and documents using **Azure Language Service + Azure OpenAI**.")


# ---------------- Session State ----------------
if "uploaded_text" not in st.session_state:
    st.session_state["uploaded_text"] = None

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

if "source_type" not in st.session_state:
    st.session_state["source_type"] = None  # "text" or "file"

if "file_name" not in st.session_state:
    st.session_state["file_name"] = None


# ---------------- Sidebar ----------------
st.sidebar.header("Input")
input_mode = st.sidebar.radio(
    "Choose input type",
    ["Paste text", "Upload file"],
    index=1
)


# ---------------- Input Handling ----------------
if input_mode == "Paste text":
    default_text = (
        "Hi, my name is Rahul Sharma and I live in Hyderabad. "
        "My phone number is 98765-12345."
    )
    text = st.text_area("Enter text:", value=default_text, height=200)

    if st.button("Analyze text"):
        st.session_state["uploaded_text"] = text
        st.session_state["analysis_result"] = None  # reset
        st.session_state["source_type"] = "text"
        st.session_state["file_name"] = None

else:
    uploaded_file = st.file_uploader(
        "Upload a file",
        type=["txt", "pdf", "docx", "csv", "json"],
        help="Supported: .txt, .pdf, .docx, .csv, .json"
    )

    if uploaded_file is not None and st.button("Analyze file"):
        suffix = Path(uploaded_file.name).suffix

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        try:
            st.session_state["uploaded_text"] = load_text_from_file(tmp_path)
            st.session_state["analysis_result"] = None  # reset
            st.session_state["source_type"] = "file"
            st.session_state["file_name"] = uploaded_file.name
        except Exception as e:
            st.error(f"Error reading file: {e}")


# Stop if no input
if not st.session_state["uploaded_text"]:
    st.info("⬆️ Upload a file or paste text, then click Analyze.")
    st.stop()


# ---------------- Run NLP Analysis ----------------
if st.session_state["analysis_result"] is None:
    with st.spinner("Analyzing with Azure NLP..."):
        try:
            st.session_state["analysis_result"] = analyze_text_all(
                st.session_state["uploaded_text"]
            )
        except Exception as e:
            st.error(f"Error calling Azure services: {e}")
            st.stop()


result = st.session_state["analysis_result"]
uploaded_text = st.session_state["uploaded_text"]


# ---------------- Summary (full width) ----------------
st.subheader("📝 Summary (GPT-style)")
summary = result.get("summary", [])

if summary:
    for i, sent in enumerate(summary, start=1):
        st.write(f"{i}. {sent}")
else:
    st.write("No summary available.")


# ---------------- ROW 1: Language + Multi-language ----------------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("🌐 Detected Language")
    lang = result.get("language", {})
    if lang:
        st.metric(
            label="Dominant Language",
            value=f"{lang.get('name')} ({lang.get('iso6391')})",
            delta=f"Confidence: {lang.get('confidence'):.2f}",
        )
    else:
        st.write("No language detected.")

with row1_col2:
    st.subheader("🈯 Multi-language Breakdown")

    ml = result.get("multi_language", [])
    if ml and len(ml) > 1:
        ml_df = pd.DataFrame(ml).set_index("language")[["confidence"]]
        st.bar_chart(ml_df)
    elif ml and len(ml) == 1:
        st.metric(
            label="Only one language detected",
            value=f"{ml[0]['language']} ({ml[0]['iso6391']})",
            delta=f"Confidence: {ml[0]['confidence']:.2f}",
        )
    else:
        st.info("No multi-language content detected.")


# ---------------- ROW 2: Sentiment + Classification ----------------
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("📊 Sentiment")
    sent_scores = result["sentiment"]["scores"]

    sent_df = pd.DataFrame({
        "sentiment": ["positive", "neutral", "negative"],
        "score": [
            sent_scores["positive"],
            sent_scores["neutral"],
            sent_scores["negative"],
        ],
    }).set_index("sentiment")

    st.bar_chart(sent_df)

with row2_col2:
    st.subheader("🧩 Text Classification (Single Label)")

    cls = result.get("classification", {})
    if cls:
        st.write(f"**Predicted Category:** `{cls.get('label')}`")
        st.write(f"**Confidence:** {cls.get('confidence'):.2f}")
        st.write(f"**Explanation:** {cls.get('explanation')}")
    else:
        st.write("No classification available.")


# ---------------- Translation (Automatic) ----------------
st.subheader("🌍 Translation")

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
    "Select target language",
    list(language_map.keys()),
    index=0,
)

target_lang_code = language_map[selected_lang]

if uploaded_text:
    translated_output = translate_text(uploaded_text, target_lang_code)
    st.success(translated_output)
else:
    st.info("Upload text to enable translation.")


# ---------------- KEY PHRASES ----------------
st.subheader("🔑 Key Phrases")

key_phrases = result.get("key_phrases", [])
if key_phrases:
    cols = st.columns(4)
    for i, phrase in enumerate(key_phrases):
        cols[i % 4].markdown(f"- `{phrase}`")
else:
    st.write("No key phrases found.")


# ---------------- ENTITIES + PII ----------------
ent_col, pii_col = st.columns(2)

with ent_col:
    st.subheader("🏷 Named Entities")
    entities = result.get("entities", [])
    if entities:
        st.dataframe(pd.DataFrame(entities), use_container_width=True)
    else:
        st.write("No entities detected.")

with pii_col:
    st.subheader("🛡 PII Entities")
    pii = result.get("pii", [])
    if pii:
        st.dataframe(pd.DataFrame(pii), use_container_width=True)
    else:
        st.write("No PII entities detected.")


# ---------------- RAW TEXT + JSON DOWNLOAD ----------------
with st.expander("📄 View raw text"):
    st.text(uploaded_text[:5000])

result_json = json.dumps(result, indent=2, ensure_ascii=False)

st.download_button(
    label="⬇️ Download results as JSON",
    data=result_json.encode("utf-8"),
    file_name="nlp_analysis_result.json",
    mime="application/json",
)


# ---------------- SAVE TO COSMOS DB ----------------
from app.cosmos_client import save_analysis_to_cosmos
st.subheader("Analysis")
if st.button("Save analysis to CosmosDB"):
    try:
        doc_id = save_analysis_to_cosmos(
            result=result,
            raw_text=uploaded_text,
            source_type=st.session_state.get("source_type", "text"),
            file_name=st.session_state.get("file_name"),
        )
        st.success(f"Saved to CosmosDB with id: {doc_id}")
    except Exception as e:
        st.error(f"Failed to save: {e}")
