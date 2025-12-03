# app/file_loader.py

import json
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document

def load_text_from_file(file_path: str) -> str:
    """
    Convert supported file types to plain text.
    Supported:
        - .txt
        - .pdf (digital)
        - .docx
        - .csv
        - .json
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")

    elif ext == ".pdf":
        return _extract_pdf(path)

    elif ext == ".docx":
        return _extract_docx(path)

    elif ext == ".csv":
        return _extract_csv(path)

    elif ext == ".json":
        return _extract_json(path)

    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def _extract_docx(path: Path) -> str:
    doc = Document(str(path))
    text = "\n".join([p.text for p in doc.paragraphs])
    return text


def _extract_csv(path: Path) -> str:
    df = pd.read_csv(path)
    return df.to_string(index=False)


def _extract_json(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, indent=2)
    except:
        return path.read_text(encoding="utf-8", errors="ignore")
