# Policy-Aware Multi-Agent RAG Insurance Claim Decision Engine

A policy-aware multi-agent RAG system for analyzing health-insurance claims against an authoritative policy document.

The system combines structured claim analysis, hybrid retrieval, reranking, deterministic policy-rule evaluation, multi-agent orchestration, citation validation, and abstention when required evidence is missing.

## Architecture

```text
Claim Input
    |
    v
Case Analysis Agent
    |
    v
Policy Evidence Agent
    |
    +--> Dense Retrieval (BGE + FAISS)
    +--> Sparse Retrieval (BM25)
    +--> Reciprocal Rank Fusion
    +--> BGE Reranker
    |
    v
Coverage Agent
    |
    v
Decision Agent
    |
    v
Validation Agent
    |
    v
Structured Decision
```

## Multi-Agent Design

### Case Analysis Agent
Extracts and normalizes policy dates, hospitalization details, diagnosis, treatment, evidence availability, missing information, and coverage duration.

### Policy Evidence Agent
Generates policy-focused queries and performs:
1. Dense retrieval
2. Sparse BM25 retrieval
3. Reciprocal Rank Fusion
4. Candidate deduplication
5. BGE reranking
6. Policy evidence selection with metadata

### Coverage Agent
Applies structured policy rules including waiting periods, pre-existing disease, specified disease waiting, hospitalization duration, hospital eligibility, domiciliary treatment, experimental treatment, cosmetic treatment, policy limits, and pre/post-hospitalization limits.

### Decision Agent
Produces one of:
- `ADMISSIBLE`
- `ADMISSIBLE_WITH_LIMITS`
- `PARTIALLY_ADMISSIBLE`
- `NOT_ADMISSIBLE`
- `NEEDS_REVIEW`

### Validation Agent
Validates decision consistency, required evidence, citation metadata, policy chunk references, and abstention behavior.

The system records operational trace information rather than hidden chain-of-thought.

## RAG Pipeline

The supplied policy PDF is extracted page-by-page and converted into searchable chunks.

**Dense retrieval:** `BAAI/bge-small-en-v1.5` with FAISS.

**Sparse retrieval:** BM25 for lexical matching.

**Fusion:** Reciprocal Rank Fusion combines dense and sparse candidates.

**Reranking:** `BAAI/bge-reranker-base` reranks the fused candidates.

## Policy Citations

Each policy chunk contains:

```text
source
page
section
chunk_id
text
```

Example:

```json
{
  "claim": "Room rent is limited to 1% of Basic Sum Insured per day.",
  "source": "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf",
  "page": 7,
  "section": "WHAT WE COVER",
  "chunk_id": "policy_p7_chunk_03"
}
```

## Abstention

The system does not invent missing evidence.

```text
True  -> evidence confirms condition
False -> evidence explicitly indicates failure
None  -> evidence is missing
```

For example, missing hospital registration or medical-necessity evidence can result in:

```text
NEEDS_REVIEW
```

## Example Decision

```json
{
  "case_id": "CUS-002",
  "decision": "ADMISSIBLE_WITH_LIMITS",
  "confidence": 0.85,
  "key_findings": [
    "Claim occurs after the general 30-day waiting period.",
    "Hospitalization meets the 24-hour minimum duration requirement."
  ],
  "missing_evidence": [],
  "validation": {
    "status": "VALID",
    "unsupported_claims": []
  }
}
```

## Technology Stack

- Python
- FastAPI
- Pydantic
- LangGraph
- Sentence Transformers
- FAISS
- BM25
- FlagEmbedding
- Google Gemini
- Streamlit
- JSON / FAISS indexes

## API

### Health Check

```http
GET /health
```

### Analyze Claim

```http
POST /analyze
```

Example request:

```json
{
  "case_id": "CUS-001",
  "policy_start_date": "2026-01-01",
  "claim_date": "2026-03-15",
  "is_inpatient": true,
  "treatment_duration_hours": 72,
  "diagnosis": "Appendicitis",
  "treatment": "Appendectomy"
}
```

## Running the Project

Create and activate the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Configure `.env`:

```env
GEMINI_API_KEY=your_api_key
LLM_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RERANKER_MODEL=BAAI/bge-reranker-base
```

Build policy indexes:

```powershell
python -m app.ingestion.indexer
```

Start the API:

```powershell
uvicorn app.api.main:app --reload
```

Start Streamlit in another terminal:

```powershell
streamlit run frontend/app.py
```

## Evaluation

Evaluation files:

```text
eval/
├── expected_outcomes.json
├── custom_expected_outcomes.json
├── run_eval.py
├── case_adapter.py
├── retrieval_eval.py
├── citation_eval.py
└── results.json
```

Run tests:

```powershell
python -m pytest -q
```

Run the complete evaluation:

```powershell
python -m eval.run_eval
```

Run retrieval evaluation:

```powershell
python -m eval.retrieval_eval
```

Run citation evaluation:

```powershell
python -m eval.citation_eval
```

The evaluation covers public cases, custom cases, decision behavior, retrieval quality, citation validity, and abstention behavior.

## Custom Test Cases

```text
CUS-001 -> ADMISSIBLE
CUS-002 -> ADMISSIBLE_WITH_LIMITS
CUS-003 -> NOT_ADMISSIBLE
CUS-004 -> NEEDS_REVIEW
CUS-005 -> NOT_ADMISSIBLE
```

The custom cases cover straightforward admissibility, policy-limit deductions, pre-existing disease, insufficient evidence, and experimental treatment.

## Failure and Abstention Handling

The system explicitly handles:
- missing hospital evidence
- missing medical necessity
- missing expense timing
- policy exclusions
- waiting-period failures
- unsupported claim information
- citation validation failures

When evidence is insufficient, the engine can return `NEEDS_REVIEW` instead of fabricating a conclusion.

## Project Structure

```text
claim-engine/
├── app/
│   ├── ingestion/
│   ├── retrieval/
│   ├── agents/
│   ├── orchestrator/
│   ├── schemas/
│   ├── api/
│   └── config.py
├── frontend/
├── data/
│   ├── policy/
│   ├── public_cases/
│   └── custom_cases/
├── eval/
├── tests/
├── requirements.txt
├── .env
└── README.md
```

## Design Principles

1. **Policy-first reasoning** — the supplied policy is treated as authoritative.
2. **Hybrid retrieval** — dense and lexical retrieval are combined.
3. **Structured decisions** — decisions are machine-readable.
4. **Evidence-aware reasoning** — missing information is explicitly represented.
5. **Traceability** — findings include policy source metadata.
6. **Abstention over fabrication** — uncertain cases can be sent to review.
7. **Separation of responsibilities** — retrieval, coverage, decision, and validation are separate stages.
