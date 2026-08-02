# CINE-GATE Milestone 5 architecture

```mermaid
flowchart LR
    U[Production user] --> W[FastAPI web application]
    W --> RS[Rights Scout\nGemini advisory discovery]
    RS --> SC[Scope Controller\nDeterministic policy]
    SC --> EM[Evidence Mapper\nMatrix + readiness]
    EM --> RB[Release Brief Agent\nGemini advisory explanation]
    RB --> HC{Human Control Plane}
    HC -->|Approve eligible record| F[Finalized record]
    HC -->|Reject| F
    HC -->|Correct metadata| R[Linked revision]
    R --> SC
    SC -->|BLOCKED| HC
    W --> E[Evidence package\nJSON + CSV + report + checksums]

    subgraph Google Cloud account stage
      ADK[ADK multi-agent workflow\nParallel discovery + sequential synthesis]
      AE[Vertex AI Agent Engine\nSessions + Cloud Trace]
      CR[Cloud Run hosted app]
      ADK --> AE
      CR --> RS
    end

    subgraph IBM track development evidence
      B[IBM Bob]
      BI[.bobignore + AGENTS.md]
      BT[Bounded review tasks]
      BE[Truthful evidence notes]
      BI --> B --> BT --> BE
    end
```

The ADK workflow is advisory. The FastAPI deterministic policy is the source of the recorded outcome. Unrelated proprietary systems and confidential material are outside the repository and outside the Bob workspace.
