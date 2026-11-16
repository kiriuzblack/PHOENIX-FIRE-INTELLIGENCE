# 🔥 PHOENIX FIRE INTELLIGENCE

### Turning Microgravity Fire Research into an Immersive Scientific Experience

**Team PHOENIX Orbit | NASA Space Apps Challenge 2026 | Flame in Freefall**

*Explore the physics. Follow the evidence. Rethink fire safety beyond Earth.*

**[GitHub Repository](https://github.com/kiriuzblack/PHOENIX-FIRE-INTELLIGENCE)** | **[NASA Technical Reports Server](https://ntrs.nasa.gov/)**

---

## 🌌 Our Mission

**Fire behaves differently beyond Earth.**

On Earth, buoyancy influences the familiar upward movement of flames. In microgravity, combustion develops under different physical conditions, making oxygen availability, airflow, fuel properties, and transport processes especially important.

Understanding these differences is essential for advancing our knowledge of combustion and improving fire-safety research for future space missions.

However, valuable research is distributed across complex experimental datasets, scientific reports, and technical archives.

**PHOENIX FIRE INTELLIGENCE transforms that information into an immersive, interactive scientific experience.**

Our mission is to bridge the gap between advanced space research and accessible scientific understanding.

> **How can we make microgravity combustion research easier to explore, analyze, and understand without losing its scientific foundations?**

That is the challenge PHOENIX was built to address.

---

## 🚀 The Solution

PHOENIX FIRE INTELLIGENCE is an interactive platform combining immersive 3D experiences, scientific data visualization, experimental comparisons, and AI-assisted research.

Instead of presenting scientific information as isolated tables and documents, PHOENIX invites users to enter a virtual research environment and investigate the evidence themselves.

### Key Features

**🌌 Cinematic 3D Experience**

An immersive space-inspired journey featuring interactive plasma visuals, camera transitions, and animated environments built with Three.js and React Three Fiber.

**🔬 Interactive Research Laboratory**

A virtual laboratory that provides access to experiment descriptions, scientific comparisons, structured data, and analytical interfaces.

**📊 Scientific Data Dashboard**

A visualization environment for exploring processed research data related to combustion in microgravity.

**🔥 Experiment Exploration**

Interactive analysis of research programs including:

- **FLEX — Flame Extinguishment Experiment**
- **SAFFIRE — Spacecraft Fire Experiment**
- **BASS-II — Burning and Suppression of Solids II**, through the scientific document-retrieval prototype

**📈 Data Visualization**

Interactive charts and animated plots designed to help users investigate patterns and characteristics in the available research data.

**🤖 PHOENIX AI — Scientific Research Assistant Prototype**

A retrieval-augmented generation (RAG) system using Google Gemini to retrieve information from indexed scientific PDFs and generate answers accompanied by document and page references.

The standalone RAG pipeline has been successfully tested with a NASA BASS-II report excerpt. Full integration of the AI chat into the main application remains under development.

---

## 🔬 Scientific Data

PHOENIX incorporates processed experimental information designed for accessible exploration.

The current dataset includes:

- **285 processed experimental records**
- **285 evidence-matrix entries**
- Data-quality annotations
- A SAFFIRE-specific research subset
- Interactive experiment comparisons and scientific charts

The structured data currently focuses on FLEX and SAFFIRE research.

For document-based exploration, the AI prototype has indexed **46 text fragments** from a limited excerpt of the NASA BASS-II technical report.

**Scientific integrity matters.** The prototype distinguishes available evidence from missing information and does not claim to represent a complete NASA combustion database.

---

## 🧠 How PHOENIX AI Works

The research assistant uses retrieval-augmented generation rather than relying on an unrestricted chatbot alone.

1. Scientific PDF documents are uploaded and indexed.
2. Document text is divided into searchable fragments.
3. Gemini embedding models convert those fragments into numerical representations.
4. A user question is converted into an embedding.
5. Relevant fragments are retrieved using vector similarity.
6. Gemini generates an answer using the retrieved scientific context.
7. The system returns document names, pages, and relevance scores alongside the answer.

**Why this matters:** the goal is to connect natural-language explanations to identifiable research evidence.

Retrieval scores indicate semantic similarity—not guaranteed scientific accuracy. Users should verify important claims against the original publications.

---

## 🛠 Technology Stack

| Component | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| 3D Visualization | Three.js, React Three Fiber |
| Animation | GSAP |
| Main Backend | Python, FastAPI |
| Data | Processed CSV datasets |
| AI Model | Google Gemini |
| Research Retrieval | RAG and vector embeddings |
| Document Processing | PDF text extraction and scientific source indexing |
| Version Control | Git and GitHub |

---

## 🏗 System Architecture

**Frontend**

React + Three.js powers the cinematic experience, research laboratory, scientific dashboard, and visualization components.

**Main Backend**

FastAPI serves structured scientific data and provides a bridge between the frontend and the AI research service.

**AI Research Backend**

A separate FastAPI service handles PDF indexing, semantic retrieval, Gemini embeddings, and scientific question answering.

**Scientific Evidence**

Processed experiment records and NASA technical literature support the analytical experience.

The project follows a modular architecture so that visualization, scientific data, and AI research can evolve independently.

---

## 💻 Running the Project Locally

### Requirements

- Node.js and npm
- Python 3.11 or newer
- Python dependencies for the backend services
- A modern browser supporting WebGL
- A Google Gemini API key for optional AI functionality

### Clone the repository

`git clone https://github.com/kiriuzblack/PHOENIX-FIRE-INTELLIGENCE.git`

`cd PHOENIX-FIRE-INTELLIGENCE`

### Start the frontend

Open a terminal in the `frontend` directory and run:

`npm install`

`npm run dev`

Open **http://localhost:5173**.

### Start the scientific data API

With the backend's Python dependencies installed, run the following command from the repository root:

`python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`

The API will be available at:

**http://127.0.0.1:8000**

### Optional: Start the Gemini RAG service

The separate research backend is located under the team's `PHOENIX_ORBIT_FASTAPI_GitHub` directory.

From that service's backend directory, install its requirements and run:

`python -m uvicorn main:app --host 127.0.0.1 --port 8002`

Required server configuration includes:

- `GEMINI_API_KEY`: private Gemini API credential
- `GEMINI_CHAT_MODEL`: the available model used for generation
- `PHOENIX_RAG_URL`: address of the RAG service used by the main backend

**Security:** Never commit API keys, secret environment files, or virtual environments to GitHub.

---

## 🔌 API Endpoints

### Main Scientific API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Service status |
| GET | `/api/data/summary` | Scientific dataset overview |
| GET | `/api/data/experiments` | Experiment records |
| GET | `/api/data/evidence` | Evidence matrix |
| GET | `/api/data/quality-flags` | Quality annotations |
| GET | `/api/data/saffire` | SAFFIRE research subset |
| POST | `/api/ai/chat` | AI assistant bridge |

### Research RAG API

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Service status |
| GET | `/documents` | Indexed research documents |
| POST | `/documents` | Scientific PDF ingestion |
| POST | `/chat` | Document-grounded question answering |

---

## 🌍 Access and Deployment

**Localhost is intended for development and is not publicly accessible.**

A public deployment requires hosting the React frontend and the FastAPI data service, then configuring the frontend to communicate with the hosted API.

The optional AI research service may be deployed independently.

**Project repository:** [PHOENIX FIRE INTELLIGENCE](https://github.com/kiriuzblack/PHOENIX-FIRE-INTELLIGENCE)

**Live demonstration:** Add the verified public deployment URL before submitting.

**Video walkthrough:** Add the uploaded video link before submitting.

---

## 📚 Scientific References

PHOENIX FIRE INTELLIGENCE is informed by publicly available scientific research, including:

- [NASA Technical Reports Server](https://ntrs.nasa.gov/)
- [BASS-II Summary Report](https://ntrs.nasa.gov/citations/20210011385)
- NASA research related to the FLEX and SAFFIRE programs

The project is an independent scientific exploration prototype and is not an official NASA product or endorsement.

---

## ⚠️ Prototype Scope

PHOENIX is designed for scientific communication, exploration, and education. It is not an operational spacecraft fire-risk prediction system.

The interactive frontend, scientific datasets, and data visualizations constitute the core prototype.

The standalone Gemini RAG pipeline has demonstrated document-grounded responses with page references. The end-to-end application AI chat is still being stabilized due to request timeouts.

---

## 👩‍🚀 Team PHOENIX Orbit

**NASA Space Apps Challenge 2026**

**Challenge: Flame in Freefall**

Our vision is to make complex space-science research accessible through compelling interaction, transparent evidence, and immersive technology.

**PHOENIX FIRE INTELLIGENCE**

*From data to discovery. From research to impact.*

🔥 **Explore. Understand. Innovate.**
