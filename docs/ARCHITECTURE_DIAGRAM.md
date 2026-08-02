# Architecture diagram source

```mermaid
flowchart LR
    U[Production user] --> W[Accessible web interface]
    W --> API[FastAPI review API]
    API --> D[Rights-discovery agent]
    D -->|Local keywords or Gemini| API
    API --> P[Deterministic rights policy]
    P --> M[Rights matrix and readiness engine]
    M --> N[Explanation adapter]
    N --> R[(SQLite case and revision store)]
    R --> H[Named human review]
    H --> R
    R --> V[Corrected revision workflow]
    V --> API
    R --> E[Evidence JSON and checksums]
    R --> C[Rights-matrix CSV]
    R --> T[Printable release report]
    E --> Z[Release-package ZIP and manifest]
    C --> Z
    T --> Z

    G[Vertex AI Agent Engine scaffold] -. account-stage deployment .-> D
    B[IBM Bob] -. documented development contribution .-> W
```

## Boundary note

The diagram describes CINE-GATE only. It does not represent any unrelated proprietary architecture, enterprise control plane, confidential validation model, or unpublished mechanism.
