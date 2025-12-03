import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env values
load_dotenv()

@dataclass
class Settings:
    # Azure Language Service
    azure_language_endpoint: str
    azure_language_key: str
    azure_language_region: str

    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_key: str
    azure_openai_model: str

    # Azure Translator
    azure_translate_endpoint: str
    azure_translate_key: str
    azure_translate_region: str

    # CosmosDB
    cosmos_endpoint: str
    cosmos_key: str
    cosmos_db_name: str
    cosmos_container_name: str


def get_settings() -> Settings:
    return Settings(
        # Language Service
        azure_language_endpoint=os.getenv("AZURE_LANGUAGE_ENDPOINT"),
        azure_language_key=os.getenv("AZURE_LANGUAGE_KEY"),
        azure_language_region=os.getenv("AZURE_LANGUAGE_REGION"),

        # OpenAI
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_key=os.getenv("AZURE_OPENAI_KEY"),
        azure_openai_model=os.getenv("AZURE_OPENAI_MODEL"),

        # Translator
        azure_translate_endpoint=os.getenv("AZURE_TRANSLATE_ENDPOINT"),
        azure_translate_key=os.getenv("AZURE_TRANSLATE_KEY"),
        azure_translate_region=os.getenv("AZURE_TRANSLATE_REGION"),

        # CosmosDB
        cosmos_endpoint=os.getenv("COSMOS_ENDPOINT"),
        cosmos_key=os.getenv("COSMOS_KEY"),
        cosmos_db_name=os.getenv("COSMOS_DB"),
        cosmos_container_name=os.getenv("COSMOS_CONTAINER")
    )
