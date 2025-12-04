# **AI-Powered Text Analytics Dashboard**  
### Azure Language Services + Azure OpenAI + Streamlit

A production-ready NLP dashboard built using Azure AI services.  
It analyzes text and documents, extracts insights, generates summaries, performs translations, and stores results in CosmosDB.  
The app is fully containerized and deployed using Azure Container Apps + GitHub Actions CI/CD.

---

## 🚀 Features

- Text & file upload (`txt`, `pdf`, `docx`, `csv`, `json`)
- Language detection (single + multiple)
- Sentiment analysis
- Named entity recognition (NER)
- PII detection
- Key phrase extraction
- Single-label classification
- GPT-style summary
- Translation to 10+ languages
- Download results as JSON
- Save insights to Azure CosmosDB
- Deployed via ACR → Azure Container Apps

---

## 🧰 Tech Stack

**Frontend:** Streamlit  
**Backend:** Python  
**Azure Services:**  
- Azure Language Service  
- Azure OpenAI (GPT models)  
- Azure Translator  
- Azure CosmosDB  
- Azure Container Registry  
- Azure Container Apps  
- GitHub Actions (CI/CD)

---

## 📌 Architecture ![Architecture Diagram](https://github.com/praveenreddy82472/nlp-analytics-azure/blob/main/final_archi.png)

---

## 📊 Use Cases

- Customer feedback insights
- Legal/HR document scanning
- Healthcare/finance PII detection
- Automated summarization
- Multi-language systems
- Enterprise NLP dashboards
