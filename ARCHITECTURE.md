# Architecture and Data Model

## System architecture

```mermaid
flowchart LR
    U[Admin / Reviewer / Viewer] --> UI[React + TypeScript UI]
    UI -->|JWT REST API| API[FastAPI]
    API --> AUTH[Authentication and RBAC]
    API --> INGEST[CSV / Excel ingestion]
    API --> RULES[Normalization and deterministic rules]
    API --> REVIEW[Exception review and revalidation]
    API --> AI[AI explanation adapter]
    API --> EXPORT[CSV exports]
    AUTH --> DB[(MongoDB)]
    INGEST --> DB
    RULES --> DB
    REVIEW --> HASH[SHA-256 canonical record hashing]
    HASH --> DB
    AI --> DB
    EXPORT --> DB
```

The backend is the authorization boundary. Hiding a control in React is never
treated as a security control. Every mutating endpoint verifies the JWT role,
and reviewer operations additionally verify dataset assignment and ownership of
the claimed exception.

## Verification sequence

```mermaid
sequenceDiagram
    participant A as Admin
    participant API as FastAPI
    participant DB as MongoDB
    participant R as Reviewer
    A->>API: Upload CSV/XLS/XLSX
    API->>DB: Store raw and normalized records
    A->>API: Normalize and validate
    API->>DB: Persist deterministic exceptions
    R->>API: Claim assigned exception
    API->>DB: Atomic open → under_review transition
    R->>API: Correct or reject with reason
    API->>API: Normalize and rerun rules
    API->>DB: Save correction, hashes, statuses and audit events
    API-->>R: Revalidation result
```

## Logical data model

```mermaid
erDiagram
    USER }o--o{ DATASET : assigned_to
    DATASET ||--o{ LOAN : contains
    DATASET ||--o{ EXCEPTION : produces
    LOAN ||--o{ EXCEPTION : has
    LOAN ||--o{ CORRECTION : records
    DATASET ||--o{ AUDIT_EVENT : logs
    LOAN ||--o{ AUDIT_EVENT : traces
    VALIDATION_RULE ||--o{ EXCEPTION : identifies

    USER {
      string email UK
      string role
      boolean enabled
    }
    DATASET {
      uuid id PK
      string name
      datetime created_at
      string[] assigned_reviewers
      boolean normalized
      boolean validated
    }
    LOAN {
      uuid id PK
      uuid dataset_id FK
      int source_row
      object raw
      object normalized
      string record_hash
      string status
      boolean verified
    }
    EXCEPTION {
      uuid id PK
      uuid loan_id FK
      string rule
      string field
      string severity
      string status
      string under_review_by
    }
    CORRECTION {
      datetime at
      string reviewer
      string reason
      object[] changes
      string previous_hash
      string new_hash
    }
    AUDIT_EVENT {
      uuid id PK
      string event
      string actor
      string role
      datetime created_at
      object detail
    }
    VALIDATION_RULE {
      string key PK
      number value
      boolean enabled
    }
```

Corrections are embedded in their loan record so the previous and new hashes
remain adjacent to the field-level change. Audit events remain separate,
append-only operational evidence.

## Trust boundaries

- AI output is advisory text only and cannot mutate or verify a record.
- Deterministic rules determine whether an exception still fails.
- Only an assigned reviewer who atomically claimed an exception may decide it.
- A record is marked `Verified` only when no `open` or `under_review`
  exceptions remain.
- SHA-256 hashes detect changes to canonical normalized record content; they are
  not presented as blockchain or digital signatures.

