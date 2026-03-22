# AffiForge Architecture (March 22, 2026)

```mermaid
flowchart TD
    A[User Dashboard] --> B[Celery Scheduler]
    B --> C[Reddit Scanner + Pain Extractor]
    C --> D[Serper Low-Comp Validator]
    D --> E[Cluster Generator (NEW)]
    E --> F[LangChain Content Agent]
    F --> G[WordPress Auto-Publish]
    G --> H[Earnings Tracker + Revenue-Share Calculator (NEW)]
    H --> I[Ad/Program Optimizer Dashboard (NEW)]
    I --> A
```
