# app/nlp_service.py

import json
import requests
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from .config import get_settings
from openai import AzureOpenAI

settings = get_settings()

client = TextAnalyticsClient(
    endpoint=settings.azure_language_endpoint,
    credential=AzureKeyCredential(settings.azure_language_key),
)

openai_client = AzureOpenAI(
    api_key=settings.azure_openai_key,
    api_version="2024-02-15-preview",
    azure_endpoint=settings.azure_openai_endpoint
)


def summarize_using_gpt(text: str) -> str:
    prompt = f"Summarize the following text in 3-4 sentences:\n\n{text}"

    response = openai_client.chat.completions.create(
        model=settings.azure_openai_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes text clearly."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

import re

def detect_languages_multiline(text: str):
    """
    Detect languages across multiple segments of the text.
    Returns a list of {language, iso6391, confidence} aggregated per language.
    """

    # Split on periods and newlines into rough "sentences"
    segments = [
        s.strip()
        for s in re.split(r"[.\n]+", text)
        if len(s.strip()) > 0
    ]

    if not segments:
        return []

    lang_stats = {}  # iso -> {language, iso6391, confidence_sum, count}

    for seg in segments:
        try:
            res = client.detect_language([seg])[0]
            pl = res.primary_language
            code = pl.iso6391_name
            name = pl.name
            conf = pl.confidence_score

            if code not in lang_stats:
                lang_stats[code] = {
                    "language": name,
                    "iso6391": code,
                    "confidence_sum": 0.0,
                    "count": 0,
                }

            lang_stats[code]["confidence_sum"] += conf
            lang_stats[code]["count"] += 1

        except Exception:
            # If any segment fails, just skip it
            continue

    # Build final breakdown with average confidence and filter by threshold
    breakdown = []
    threshold = 0.20

    for code, info in lang_stats.items():
        avg_conf = info["confidence_sum"] / max(info["count"], 1)
        if avg_conf >= threshold:
            breakdown.append(
                {
                    "language": info["language"],
                    "iso6391": info["iso6391"],
                    "confidence": avg_conf,
                }
            )

    # Sort descending by confidence
    breakdown.sort(key=lambda x: x["confidence"], reverse=True)
    return breakdown


def translate_text(text: str, target_lang: str = "en") -> str:
    """
    Translate text to the target language using Azure Translator.
    """
    endpoint = settings.azure_translate_endpoint
    key = settings.azure_translate_key
    region = settings.azure_translate_region

    url = endpoint + "/translate?api-version=3.0"
    url += f"&to={target_lang}"

    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Ocp-Apim-Subscription-Region": region,
        "Content-Type": "application/json"
    }

    payload = [{"text": text}]

    try:
        resp = requests.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data[0]["translations"][0]["text"]
    except Exception as e:
        return f"Translation error: {e}"
    
def classify_text_gpt(text: str) -> dict:
    """
    Single-label GPT classification using Azure OpenAI.
    Robust JSON parsing with fallback.
    """

    CATEGORY_LIST = [
        "Personal Information",
        "Professional / Work",
        "Education",
        "Technical / Engineering",
        "Healthcare / Medical",
        "Finance / Banking",
        "Travel / Location",
        "Legal / Compliance",
        "Sentiment / Opinion",
        "Miscellaneous / Other"
    ]

    settings = get_settings()

    client = AzureOpenAI(
        api_key=settings.azure_openai_key,
        api_version="2024-08-01-preview",
        azure_endpoint=settings.azure_openai_endpoint
    )

    prompt = f"""
    You must classify the text into EXACTLY ONE of these categories:

    {CATEGORY_LIST}

    Return ONLY valid JSON with this structure:

    {{
      "label": "category from list",
      "confidence": 0.0 to 1.0,
      "explanation": "short explanation"
    }}

    Do NOT add anything else.
    Do NOT add comments.
    Do NOT add markdown.
    Do NOT wrap in ```json```.

    Text to classify:
    {text}
    """

    response = client.chat.completions.create(
        model=settings.azure_openai_model,
        temperature=0,
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON."},
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.choices[0].message.content.strip()

    # ---------------------
    # CLEAN OUTPUT
    # ---------------------
    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")
    raw = raw.strip()

    # ---------------------
    # PARSE JSON SAFELY
    # ---------------------
    try:
        data = json.loads(raw)
        return {
            "label": data.get("label", "Miscellaneous / Other"),
            "confidence": float(data.get("confidence", 0.75)),
            "explanation": data.get("explanation", "")
        }
    except Exception:
        # fallback if GPT still fails
        return {
            "label": "Miscellaneous / Other",
            "confidence": 0.70,
            "explanation": "Failed to parse GPT classification output."
        }




def analyze_text_all(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("Text is empty.")

    docs = [text]

    # 1. Language detection
    lang = client.detect_language(docs)[0]

    # 2. Sentiment
    sentiment = client.analyze_sentiment(docs)[0]

    # 3. Key phrases
    key_phrases = client.extract_key_phrases(docs)[0]

    # 4. Named Entities
    entities = client.recognize_entities(docs)[0]

    # 5. PII Entities
    pii = client.recognize_pii_entities(docs)[0]

    # 6. Summarization using GPT
    gpt_summary = summarize_using_gpt(text)
    summary_sentences = [gpt_summary]

    # ------------------------
    # CLEAN MULTI-LANGUAGE
    # ------------------------
    multi_lang = detect_languages_multiline(text)
    multi_lang = [
        lang for lang in multi_lang
        if lang["confidence"] >= 0.20
    ]

    # ------------------------
    # FILTER SENSITIVE PII
    # ------------------------
    SENSITIVE_PII_CATEGORIES = [
        "PhoneNumber",
        "Email",
        "CreditCardNumber",
        "BankAccountNumber",
        "InternationalBankingNumber",
        "USSocialSecurityNumber",
        "USITIN",
        "AadhaarNumber",
        "PassportNumber",
        "UKNHSNumber",
        "CADriversLicenseNumber",
        "IPAddress"
    ]

    pii_filtered = [
        {
            "text": e.text,
            "category": e.category,
            "confidence": e.confidence_score,
        }
        for e in pii.entities
        if e.category in SENSITIVE_PII_CATEGORIES
    ]

    # ------------------------
    # FINAL RETURN
    # ------------------------
    return {
        "language": {
            "name": lang.primary_language.name,
            "iso6391": lang.primary_language.iso6391_name,
            "confidence": lang.primary_language.confidence_score,
        },

        "multi_language": detect_languages_multiline(text),

        "sentiment": {
            "overall": sentiment.sentiment,
            "scores": {
                "positive": sentiment.confidence_scores.positive,
                "neutral": sentiment.confidence_scores.neutral,
                "negative": sentiment.confidence_scores.negative,
            },
        },

        "classification": classify_text_gpt(text),

        "key_phrases": key_phrases.key_phrases,

        "entities": [
            {
                "text": e.text,
                "category": e.category,
                "confidence": e.confidence_score,
            }
            for e in entities.entities
        ],

        "pii": pii_filtered,

        "summary": summary_sentences,
    }

