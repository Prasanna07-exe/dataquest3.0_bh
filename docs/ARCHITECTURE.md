# DQBH Architecture

## Architecture Style

Modular monolith.

The system is divided into logical modules but deployed as a unified backend during the hackathon.

---

## High-Level Architecture

Frontend
    ↓
FastAPI API Layer
    ↓
Core Domain Services
    ↓
Intelligence Services
    ↓
Integration Services
    ↓
PostgreSQL / Redis / Object Storage

---

## Core Modules

- Auth & RBAC
- Customers & Sites
- Equipment
- Service Requests
- Scheduling
- Inventory
- Matching
- Approvals
- Execution
- Exceptions
- Verification
- Notifications
- Analytics
- Audit

---

## Intelligence Modules

- Request Classification
- Resource Planning
- Spare-Part Prediction
- SLA Risk
- Technician Matching
- Exception Intelligence
- Diagnostic/RAG
- Operations Copilot
- Predictive Maintenance
- Root Cause Analysis
- Document/OCR

---

## Critical Architecture Rule

AI/LLM services return structured recommendations.

AI does not directly modify authoritative application state.

The backend:

1. Validates AI output
2. Applies deterministic business rules
3. Checks authorization
4. Executes database transaction
5. Writes audit record
6. Emits notification/event