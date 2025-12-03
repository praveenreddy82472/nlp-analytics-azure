# app/main.py

from tabulate import tabulate
from app.file_loader import load_text_from_file
from app.nlp_service import analyze_text_all

def main():
    print("Enter 1 to input text")
    print("Enter 2 to upload a file")
    choice = input("> ")

    if choice == "1":
        text = input("Enter your text:\n")
    else:
        path = input("Enter file path: ")
        text = load_text_from_file(path)

    result = analyze_text_all(text)

    print("\n\n===== SUMMARY =====")
    print("\n".join(result["summary"]))
    
    print("\n===== LANGUAGE DETECTION =====")
    lang = result["language"]
    print(f"Language: {lang['name']} ({lang['iso6391']}) — Confidence: {lang['confidence']:.2f}")


    print("\n===== SENTIMENT =====")
    print(result["sentiment"])

    print("\n===== KEY PHRASES =====")
    print(result["key_phrases"])

    print("\n===== ENTITIES =====")
    print(tabulate(result["entities"], headers="keys"))

    print("\n===== PII =====")
    print(tabulate(result["pii"], headers="keys"))

if __name__ == "__main__":
    main()
