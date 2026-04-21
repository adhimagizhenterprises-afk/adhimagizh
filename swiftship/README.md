# SwiftShip — Courier & Logistics Platform

A production-grade, microservices-based courier and logistics platform built with **FastAPI** (backend) and **React** (frontend). Inspired by ShipRocket, DTDC, ST Courier, and Professional Courier.

---

## Architecture Overview

```
swiftship/
├── services/
│   ├── customer-booking-service/   # Port 8001 — Bookings, AWB, pricing
│   ├── customer-tracking-service/  # Port 8002 — Real-time tracking, ETA
│   ├── operations-service/         # Port 8003 — Manifests, dispatch, hub ops
│   ├── agent-service/              # Port 8004 — Pickup/delivery, POD
│   ├── notification-service/       # Port 8005 — SMS, email, push
│   ├── payment-service/            # Port 8006 — COD, prepaid, invoices
│   └── user-auth-service/          # Port 8007 — JWT auth, roles
├── frontend/
│   ├── customer-portal/            # React SPA — customer booking & tracking
│   ├── ops-dashboard/              # React SPA — operations team
│   └── agent-app/                  # React Native — delivery agents
├── shared/
│   ├── events/                     # Kafka event schemas
│   ├── schemas/                    # Shared Pydantic schemas
│   └── utils/                      # AWB generator, validators
└── infrastructure/
    ├── docker/                     # Docker Compose files
    ├── k8s/                        # Kubernetes manifests
    └── nginx/                      # API Gateway / reverse proxy config
```

---

## Quick Start (Docker Compose)

```bash
git clone https://github.com/your-org/swiftship.git
cd swiftship
cp .env.example .env
docker-compose up --build
```

Services will be available at:
- Customer Portal: http://localhost:3000
- Ops Dashboard:   http://localhost:3001
- API Gateway:     http://localhost:8000
- API Docs:        http://localhost:8001/docs

---

## Technology Stack

| Layer            | Technology                                      |
|------------------|-------------------------------------------------|
| Backend          | FastAPI, Python 3.11, SQLAlchemy 2.0, Alembic   |
| Message Broker   | Apache Kafka (or RabbitMQ)                      |
| Databases        | PostgreSQL (per service), Redis, Elasticsearch  |
| Object Storage   | MinIO / AWS S3 (POD images, shipping labels)    |
| Frontend         | React 18, TypeScript, Redux Toolkit, Tailwind   |
| Mobile           | React Native (agent app)                        |
| Auth             | JWT + OAuth2, RBAC (customer/agent/ops/admin)   |
| Container        | Docker + Kubernetes + Istio                     |
| CI/CD            | GitHub Actions                                  |
| Observability    | Prometheus, Grafana, Loki, Jaeger (tracing)     |

---

## Service Responsibilities

### customer-booking-service
- Create shipment bookings (single/bulk)
- Calculate shipping charges (zone-based, weight-based, volumetric)
- Generate AWB (Air Waybill) numbers
- Schedule pickup requests
- Manage sender/receiver addresses

### customer-tracking-service
- Real-time shipment status via AWB/order ID
- Scan event history (pickup → in-transit → out-for-delivery → delivered)
- ETA prediction
- WebSocket support for live updates
- Elasticsearch-backed search

### operations-service
- Hub-to-hub manifest creation
- Route dispatch and optimization
- Sorting bay assignments
- Exception handling (undelivered, returned, held)
- Reports and MIS

### agent-service
- Delivery agent assignment
- Pickup and delivery workflows
- Proof of Delivery (POD) — photo + signature
- GPS location updates
- Agent performance tracking

### notification-service
- Booking confirmation (SMS + email)
- Out-for-delivery alerts
- Delivery confirmation
- Exception notifications
- Kafka consumer — subscribes to all shipment events

### payment-service
- COD (Cash on Delivery) management
- Prepaid payment via Razorpay
- Invoice generation (PDF)
- COD remittance to merchants
- Wallet and credit management

### user-auth-service
- User registration/login (Customer, Agent, Ops, Admin)
- JWT token issuance and refresh
- OAuth2 (Google/Apple for customers)
- Role-based access control (RBAC)
- API key management for enterprise clients

---

## Kafka Event Topics

| Topic                    | Published by        | Consumed by                          |
|--------------------------|---------------------|--------------------------------------|
| `booking.created`        | booking-service     | notification, payment, ops           |
| `pickup.scheduled`       | booking-service     | agent-service, notification          |
| `shipment.picked_up`     | agent-service       | tracking, notification               |
| `shipment.in_transit`    | operations-service  | tracking, notification               |
| `shipment.out_for_del`   | operations-service  | tracking, notification, agent        |
| `shipment.delivered`     | agent-service       | tracking, notification, payment      |
| `shipment.exception`     | agent/ops-service   | tracking, notification, ops          |
| `payment.confirmed`      | payment-service     | booking, notification                |
| `pod.captured`           | agent-service       | tracking, payment                    |

---

## Running Individual Services

```bash
cd services/customer-booking-service
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```
