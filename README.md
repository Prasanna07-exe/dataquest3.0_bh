# DQBH

DataQuest 3.0 — Next-Generation Activity Management Platform for Industrial Equipment Services.

## Core Workflow

REQUEST
→ UNDERSTAND
→ VALIDATE
→ PREDICT
→ MATCH
→ RESERVE
→ APPROVE
→ DISPATCH
→ EXECUTE
→ DETECT
→ REASSIGN
→ VERIFY
→ CLOSE
→ LEARN

## Architecture

Frontend:
React + Vite + Tailwind

Backend:
FastAPI + Python

Database:
PostgreSQL

Cache:
Redis

AI:
Structured LLM services

Storage:
Supabase Storage

Realtime:
WebSockets

## P0 Scope

- Authentication and RBAC
- Multi-site and machine management
- Reactive service requests
- AI classification
- SLA engine
- Technician matching
- Inventory and reservations
- Manager approval
- Dispatch
- Technician execution
- Exception engine
- Dynamic reassignment
- Completion verification
- Machine service history
- Four dashboards
- Audit logging

## Development Principle

AI provides recommendations.

Deterministic backend services authorize and execute operational changes.

AI must never directly mutate operational state.