# Architecture

> Full architecture documentation will be added in Phase 5.

## High-Level Overview

```mermaid
graph LR
    SIM[Simulators x5] -->|Redis Streams| BE[Backend / FastAPI]
    BE -->|SQLAlchemy| PG[(PostgreSQL)]
    BE -->|SSE| FE[Frontend / React]
    BE -->|Metrics| PROM[Prometheus]
    PROM --> GF[Grafana]
```
