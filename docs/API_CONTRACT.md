# DQBH API Contract

Base URL:

/api/v1

---

# AUTH

POST /auth/login

POST /auth/refresh

GET /auth/me

---

# MACHINES

GET /machines

GET /machines/{id}

---

# SERVICE REQUESTS

POST /service-requests

GET /service-requests

GET /service-requests/{id}

POST /service-requests/{id}/classify

POST /service-requests/{id}/plan

GET /service-requests/{id}/candidates

POST /service-requests/{id}/reserve

POST /service-requests/{id}/approve

POST /service-requests/{id}/dispatch

POST /service-requests/{id}/check-in

POST /service-requests/{id}/work-log

POST /service-requests/{id}/checklist

POST /service-requests/{id}/complete

POST /service-requests/{id}/verify

POST /service-requests/{id}/reassign

---

# EXCEPTIONS

GET /exceptions

POST /exceptions/{id}/resolve

---

# INVENTORY

GET /inventory/availability

POST /inventory/transfers

---

# DASHBOARDS

GET /dashboard/manager

GET /dashboard/customer

GET /dashboard/technician

GET /dashboard/inventory

---

# AI

POST /ai/copilot