# app/cosmos_client.py

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from app.config import get_settings
from datetime import datetime
import uuid


settings = get_settings()

if not settings.cosmos_endpoint or not settings.cosmos_key:
    raise RuntimeError("CosmosDB endpoint or key is not configured in environment variables.")

if not settings.cosmos_db_name or not settings.cosmos_container_name:
    raise RuntimeError("COSMOS_DB_NAME or COSMOS_CONTAINER_NAME is not configured in environment variables.")


_cosmos_client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)

# Create DB and container if they don't exist
_db = _cosmos_client.create_database_if_not_exists(id=settings.cosmos_db_name)

_container = _db.create_container_if_not_exists(
    id=settings.cosmos_container_name,
    partition_key=PartitionKey(path="/classification_label"),
    offer_throughput=400
)


def build_cosmos_document(result: dict, raw_text: str, source_type: str, file_name: str | None):
    language = result.get("language", {})
    sentiment = result.get("sentiment", {})
    classification = result.get("classification", {})
    pii = result.get("pii", [])
    summary_list = result.get("summary", [])
    key_phrases = result.get("key_phrases", [])
    entities = result.get("entities", [])

    pii_categories = sorted({item["category"] for item in pii}) if pii else []

    doc = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",

        "source_type": source_type,          # "file" or "text"
        "file_name": file_name,

        "language": language.get("iso6391"),
        "sentiment": sentiment.get("overall"),
        "sentiment_scores": sentiment.get("scores", {}),

        "classification_label": classification.get("label"),
        "classification_confidence": classification.get("confidence"),

        "has_pii": bool(pii),
        "pii_categories": pii_categories,

        "summary": " ".join(summary_list) if isinstance(summary_list, list) else summary_list,

        "key_phrases": key_phrases,
        "entities": entities,

        "raw_text": raw_text,
    }

    return doc


def save_analysis_to_cosmos(result: dict, raw_text: str, source_type: str, file_name: str | None = None) -> str:
    doc = build_cosmos_document(result, raw_text, source_type, file_name)

    # Make sure partition key exists
    if not doc.get("classification_label"):
        doc["classification_label"] = "Unclassified"

    try:
        _container.create_item(doc)
        return doc["id"]
    except exceptions.CosmosHttpResponseError as e:
        raise RuntimeError(f"Failed to save to CosmosDB: {e}") from e
