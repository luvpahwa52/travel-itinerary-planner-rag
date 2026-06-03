<div align="center">

# 🧭 Travel Itinerary Planner — Multi-Agent RAG System

**AI-powered travel planning with 5 autonomous agents, retrieval-augmented generation, and self-correcting validation**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Framework-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6F00)](https://www.trychroma.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [Demo](#-demo) · [Test Results](#-test-results)

</div>

---

## 📌 What Is This?

A **multi-agent RAG (Retrieval-Augmented Generation) system** that generates **validated, source-grounded travel itineraries** for 10 Indian cities using 5 AI agents orchestrated via LangGraph.

Unlike traditional AI travel planners that hallucinate places and costs, this system:
- ✅ **Retrieves real data** from a curated knowledge base (56 destinations, 176 records)
- ✅ **Validates every recommendation** against source data using code-based checks
- ✅ **Self-corrects** — if validation fails, the Planner automatically revises (up to 2 retries)
- ✅ **Scores accuracy** — faithfulness, relevance, source coverage with weighted overall score
- ✅ **Cites sources** — every hotel, restaurant, attraction traces back to the knowledge base

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **5 AI Agents** | Supervisor → Retriever → Planner → Validator → Scorer |
| 🔗 **LangGraph Orchestration** | Conditional routing with PASS / REVISE / REJECT loops |
| 🔍 **RAG with ChromaDB** | 176 embedded records, cosine similarity search, relevance filtering |
| ✅ **Code-Based Validation** | Budget check (regex), hallucination detection (name matching), completeness (day counting) |
| 📊 **Accuracy Scoring** | Faithfulness, relevance, source coverage, budget adherence, completeness |
| 💬 **User Feedback Loop** | 1-5 ⭐ rating saved to SQLite |
| 🎨 **Streamlit Wizard UI** | Step-by-step trip planning interface |
| ☁️ **AWS Bedrock** | Amazon Nova Micro (LLM) + Titan Embed Text V2 (Embeddings) |

## 🏗️ Architecture

```
User Query: "3 day trip to Goa under ₹15,000 with beaches and food"
    │
    ▼
🧠 SUPERVISOR ─── Extracts: city=Goa, days=3, budget=15000, interests=[beach, food]
    │
    ▼
🔍 RETRIEVER ─── Queries ChromaDB → Returns Top-K relevant chunks (176 records)
    │
    ▼
✍️ PLANNER ──── LLM generates day-wise itinerary with budget breakdown
    │
    ▼
✅ VALIDATOR ── Budget check (regex) + Hallucination check (name matching) + Completeness
    │
    ├── PASS ────→ 📊 SCORER → Faithfulness + Relevance + Coverage → SQLite
    ├── REVISE ──→ ✍️ Back to PLANNER (max 2 retries)
    └── REJECT ──→ 📊 SCORER (logs failure)
    │
    ▼
📋 User sees: Itinerary + Quality Scores + Source Citations + Feedback Form
```

### Key Design Decision

> **Code for math, LLM for reasoning.** Budget validation uses regex (100% accurate). Hallucination detection uses name matching against ChromaDB metadata. The LLM is only used where reasoning is needed — itinerary generation and quality scoring.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- AWS Account with Bedrock access (Nova Micro + Titan Embeddings)
- Miniconda (recommended) or venv

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/travel-itinerary-planner-rag.git
cd travel-itinerary-planner-rag

# Create conda environment
conda create -n travel_planner python=3.11 -y
conda activate travel_planner

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1
```

### Build Vector Database

```bash
python db/build_vectordb.py
```

Expected output:
```
Total chunks: 176
ChromaDB built! Total documents: 176
```

### Run the App

```bash
streamlit run ui/app.py
```

Open `http://localhost:8501` in your browser.

## 🎬 Demo

The Streamlit UI follows a wizard flow:

1. **🏙️ Select Destination** — Choose from 10 Indian cities
2. **📅 Set Duration** — 1 to 7 days
3. **💰 Set Budget** — ₹3,000 to ₹50,000
4. **🎯 Pick Interests** — Beach, Heritage, Food, Adventure, etc.
5. **🚀 Generate** — Watch 5 agents work in real-time
6. **📋 View Results** — Itinerary (bullet points per day) + Quality Metrics + Source Citations + Feedback

## 📊 Test Results

Tested across all 10 cities with different budgets and interests:

| # | City | Budget | Validation | Faithfulness | Relevance | Coverage | Overall |
|---|------|--------|-----------|-------------|-----------|----------|---------|
| 1 | Goa | ₹15K | ✅ PASS | 80% | 90% | 100% | 83% |
| 2 | Delhi | ₹5K | ❌ REJECT | 85% | 95% | 100% | 92% |
| 3 | Jaipur | ₹10K | ✅ PASS | 80% | 90% | 100% | 93% |
| 4 | Kerala | ₹18K | 🔄 REVISE | 60% | 80% | 100% | 87% |
| 5 | Manali | ₹8K | ✅ PASS | 80% | 90% | 100% | 93% |
| 6 | Varanasi | ₹6K | ✅ PASS | 80% | 90% | 100% | 92% |
| 7 | **Mumbai** | ₹8K | ✅ PASS | 85% | 90% | 100% | **95%** |
| 8 | Udaipur | ₹12K | ✅ PASS | 75% | 80% | 100% | 87% |
| 9 | **Rishikesh** | ₹6K | ✅ PASS | 85% | 90% | 100% | **94%** |
| 10 | Agra | ₹5K | ✅ PASS | 60% | 80% | 100% | 84% |

**Pass Rate: 8/10 (80%) · Average Accuracy: 89% · Source Coverage: 100%**

## 🏙️ Supported Cities

| City | Destinations | Highlights |
|------|-------------|------------|
| Goa | 6 | Beaches, nightlife, Portuguese heritage |
| Delhi | 6 | Red Fort, Qutub Minar, street food |
| Jaipur | 6 | Forts, palaces, Rajasthani culture |
| Kerala | 5 | Backwaters, tea gardens, Ayurveda |
| Manali | 5 | Adventure sports, Himalayan views |
| Varanasi | 6 | Ghats, temples, spiritual experiences |
| Mumbai | 6 | Gateway of India, Marine Drive, street food |
| Udaipur | 6 | Lakes, palaces, romantic getaways |
| Rishikesh | 5 | Rafting, yoga, Beatles Ashram |
| Agra | 5 | Taj Mahal, Mughal heritage |

**Total: 56 destinations · 176 knowledge base records**

## 🛠️ Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **LLM** | Amazon Nova Micro (AWS Bedrock) | Cost-effective, fast inference |
| **Embeddings** | Amazon Titan Embed Text V2 | 1024-dim vectors, no local download |
| **Vector DB** | ChromaDB (persistent) | Lightweight, local, fast similarity search |
| **Orchestration** | LangGraph + LangChain | Stateful agent graphs with conditional routing |
| **Validation** | Pure Python (regex + name matching) | 100% deterministic, no LLM dependency |
| **Scoring** | LLM + Python (hybrid) | Weighted accuracy: faithfulness, relevance, coverage |
| **UI** | Streamlit | Rapid prototyping, wizard flow |
| **Logging** | SQLite | Stores all scores + user feedback |
| **Environment** | Miniconda + pip | Corporate-friendly setup |

## 📁 Project Structure

```
travel-itinerary-planner-rag/
├── .streamlit/
│   └── config.toml              # Streamlit theme (light mode)
├── data/
│   ├── attractions.csv           # 56 destinations
│   ├── hotels.csv                # 40 accommodation options
│   ├── food.csv                  # 40 restaurants & eateries
│   └── transport.csv             # 40 transport modes
├── db/
│   └── build_vectordb.py         # Builds ChromaDB from CSVs
├── utils/
│   ├── config.py                 # Central configuration
│   ├── embeddings.py             # Bedrock Titan embedding function
│   └── bedrock_client.py         # Generic Bedrock LLM caller
├── agents/
│   ├── supervisor.py             # Intent extraction agent
│   ├── retriever.py              # ChromaDB query agent
│   ├── planner.py                # Itinerary generation agent
│   ├── validator.py              # Code-based validation agent
│   └── scorer.py                 # Accuracy scoring agent
├── graph/
│   ├── state.py                  # Shared state schema (TypedDict)
│   └── workflow.py               # LangGraph orchestration
├── ui/
│   └── app.py                    # Streamlit wizard UI
├── .env.example                  # AWS credentials template
├── requirements.txt              # Python dependencies
└── README.md
```

## 🔑 Key Learnings

1. **LLMs can't do math** — Tried LLM-based budget validation first. It said "₹8,800 exceeds ₹15,000". Switched to regex-based code validation → 100% accurate.

2. **Prompt engineering is iterative** — The Validator's "be strict" prompt caused 67% false rejections. Rewriting the prompt with explicit rules fixed it.

3. **Hybrid approach works best** — Code for deterministic checks (budget, name matching, counting), LLM for reasoning (itinerary generation, quality scoring).

4. **Self-correction is the real "agentic" feature** — The REVISE loop where Validator sends bad itineraries back to Planner is what makes this truly agentic, not just a chain.

## ⚠️ Known Limitations

| Limitation | Impact | Potential Fix |
|-----------|--------|--------------|
| Planner sometimes picks expensive hotels on tight budgets | Delhi test failed (₹5K/night on ₹5K budget) | Pre-filter hotels by budget before passing to Planner |
| Kerala struggles with tight budgets | Houseboat ₹6K/night hard to fit | Add more budget options for Kerala |
| No geographic validation | Hotel could be assigned to wrong city | Add city-matching in Validator |
| No intent-tier matching | "Luxury trip" might get hostel | Map intent keywords to budget tiers in Supervisor |
| LLM non-determinism | Same query → slightly different output | Inherent to LLMs; Validator ensures quality |

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent orchestration framework
- [ChromaDB](https://www.trychroma.com/) — Vector database
- [AWS Bedrock](https://aws.amazon.com/bedrock/) — LLM and embedding APIs
- [Streamlit](https://streamlit.io/) — UI framework

---

<div align="center">

**Built as a Proof of Concept for Multi-Agent RAG Systems**

⭐ Star this repo if you found it useful!

</div>
