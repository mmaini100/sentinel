# Sentinel: AI-Powered Observability & Incident Response Platform

Sentinel is a distributed, full-stack observability and incident response platform designed to simulate, detect, and resolve microservice outages in real-time. It uses an event-driven architecture to monitor system telemetry and leverages a rule-based AI engine to generate Root Cause Analyses (RCA) and resolution runbooks on the fly.

## 🚀 Features

- **Real-Time Telemetry & Anomaly Detection**: Monitors distributed events and utilizes Z-score baselining to instantly detect positive latency spikes and error bursts.
- **Dynamic Service Topology**: An interactive, real-time map of all monitored microservices (React Flow). Services and dependency graphs dynamically update to highlight degraded nodes and "blast radius" when faults occur.
- **AI-Powered Root Cause Analysis (RCA)**: When an incident is triggered, the AI worker consumes the event telemetry and generates a correlated root cause hypothesis, confidence score, and actionable remediation steps.
- **Live Fault Injection Engine**: A built-in simulator allows users to inject specific faults (e.g., `cpu_spike`, `memory_leak`, `network_delay`) into target microservices via the UI, instantly triggering the end-to-end detection pipeline.
- **Premium Analytics Dashboard**: Real-time metrics on incident frequency, AI resolution rates, and system health visualized via smooth gradient area charts.

## 🛠️ Technology Stack

**Frontend**
- **Framework**: React 18, Vite, TypeScript
- **Styling**: Tailwind CSS (Custom Dark Theme, Glassmorphism)
- **Data Fetching**: React Query (@tanstack/react-query)
- **Visualizations**: Recharts, React Flow (Topology Mapping)
- **Icons**: Lucide React

**Backend & Infrastructure**
- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL (SQLAlchemy ORM, Alembic Migrations)
- **Message Broker / Cache**: Redis (for high-throughput fault bus and event streaming)
- **Containerization**: Docker & Docker Compose (multi-container orchestration)

## 🏗️ Architecture Flow

1. **Simulators**: Python background workers continuously generate healthy telemetry data (HTTP requests, CPU metrics) and publish them to a Redis stream.
2. **Fault Injection**: Users inject faults via the UI, modifying the simulator's behavior to produce degraded telemetry (e.g., latency spikes).
3. **Detection Engine**: The backend ingests the Redis stream. A Z-Score detector maintains Exponentially Weighted Moving Averages (EWMA) of service metrics, instantly flagging anomalies and generating `Incidents` in PostgreSQL.
4. **AI Worker**: An asynchronous worker polls for new, stable incidents, analyzes the event correlation, and attaches a generated RCA report to the incident.
5. **Client UI**: The React frontend polls the backend via REST, actively updating the topology graphs, timeline views, and dashboards.

## 🚦 Getting Started

### Prerequisites
- Docker and Docker Compose

### Running Locally
1. Clone the repository:
   ```bash
   git clone https://github.com/mmaini100/sentinel.git
   cd sentinel
   ```
2. Set up your environment variables:
   ```bash
   cp .env.example .env
   ```
3. Boot up the entire stack using Docker:
   ```bash
   docker compose up --build
   ```
4. Access the web interface:
   - **Frontend**: http://localhost:5174
   - **Backend API Docs**: http://localhost:8000/docs
