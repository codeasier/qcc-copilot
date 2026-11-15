# supplier-quality-8d-copilot

🚀 **Live Demo:** [Open Supplier Quality 8D Copilot](https://supplier-quality-8d-copilot-rl3krl8hhzjqsyi7rhi9op.streamlit.app/)

> **Stop solving the same quality problem twice.**

Supplier Quality 8D Copilot is an evidence-backed semantic search and investigation-support system for manufacturing quality teams.

It transforms historical **8Ds, NCRs, PFMEAs, Control Plans, PPAPs, supplier complaints, engineering deviations, and work instructions** into searchable organizational knowledge—helping engineers quickly discover similar failures, previous root causes, corrective actions, and relevant investigation evidence.

---

## The Problem

Manufacturing companies accumulate years of valuable quality knowledge.

A problem may already have been investigated and solved, but the answer can be buried across:

* 8D reports
* NCRs
* PFMEAs
* Control Plans
* PPAP documentation
* Supplier complaints
* Engineering deviations
* Work instructions

When a similar failure occurs again, engineers may spend significant time searching historical records—or repeat an investigation that the organization has already completed.

**The knowledge exists. Finding it is the problem.**

---

## The Solution

Supplier Quality 8D Copilot converts historical quality documentation into a searchable engineering knowledge base.

An engineer can describe a new problem such as:

> **HV cable terminal resistance increased from 0.18 mΩ to 0.43 mΩ after crimping. Supplier lot B240817.**

The system semantically searches previous quality records and surfaces the most relevant historical incidents together with:

* Similar failure modes
* Historical root causes
* Corrective actions
* Relevant evidence
* Source document references
* Evidence-backed investigation recommendations

The objective is not to replace the Quality Engineer.

It is to give the engineer access to the organization's accumulated problem-solving experience when a new issue occurs.

---

## Current Prototype

The prototype currently contains **65 synthetic automotive manufacturing quality documents across 8 document types**.

| Document Type          | Records |
| ---------------------- | ------: |
| Historical 8Ds         |      15 |
| NCRs                   |      10 |
| PPAPs                  |       8 |
| PFMEAs                 |       5 |
| Control Plans          |       5 |
| Supplier Complaints    |      10 |
| Engineering Deviations |       5 |
| Work Instructions      |       7 |
| **Total**              |  **65** |

The dataset represents a fictional automotive/e-mobility manufacturer and includes interconnected quality incidents involving crimping, HV connections, ultrasonic welding, sealing, terminal retention, conductor damage, component errors, and other manufacturing failure modes.

**No real customer or supplier data is included in the public dataset.**

---

## How It Works

```text
Historical Quality Documents
            │
            ▼
     Document Loader
            │
            ▼
      Section Chunking
            │
            ▼
   MiniLM Embeddings
            │
            ▼
      FAISS Index
            │
            │
            ├─────────────────────┐
            │                     │
            ▼                     │
     New Quality Problem          │
            │                     │
            ▼                     │
      MiniLM Embedding            │
            │                     │
            └────────────► FAISS ◄┘
                           │
                           ▼
                  Similar Evidence
                           │
                           ▼
                 Historical Incidents
                           │
                           ▼
                  5M Investigation
                           │
                           ▼
              Evidence-Backed Guidance
```

The application uses semantic similarity rather than relying only on exact keyword matching.

This means a new problem does not need to use exactly the same terminology as the historical record to retrieve potentially relevant incidents.

---

## 5M Investigation Support

Retrieved historical evidence is also used to generate a structured investigation checklist across the traditional **5M** categories:

### Machine

* Tooling condition
* Tool wear
* Cycle counts
* Preventive maintenance
* Machine setup

### Material

* Supplier lot traceability
* Material condition
* Terminal/component condition
* Contamination
* Plating and oxidation

### Method

* Process parameters
* Work instructions
* Setup changes
* Process specifications

### Measurement

* Calibration
* Measurement fixtures
* Reference parts
* Gauge R&R

### Man

* Operator training
* Setup authorization
* Shift/operator history
* Work instruction compliance

Recommendations are linked back to historical evidence rather than presented as unsupported conclusions.

---

## Tech Stack

* **Python** — application and data pipeline
* **Streamlit** — interactive web application
* **SentenceTransformers** — semantic text embeddings
* **all-MiniLM-L6-v2** — 384-dimensional embedding model
* **FAISS** — vector similarity search
* **NumPy** — numerical processing
* **GitHub** — source control and project management
* **Streamlit Community Cloud** — prototype deployment

---

## Project Structure

```text
supplier-quality-8d-copilot/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── 8d/
│   ├── ncr/
│   ├── ppap/
│   ├── pfmea/
│   ├── control_plans/
│   ├── complaints/
│   ├── deviations/
│   └── work_instructions/
│
├── src/
│   ├── document_loader.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retrieval.py
│   └── investigation.py
│
├── scripts/
│   ├── generate_synthetic_data.py
│   └── build_index.py
│
└── vector_db/
    ├── quality.index
    └── metadata.json
```

---

## G
