# Hospital Infection Control & Quality Management Platform

An enterprise-grade healthcare quality auditing, distraction-free daily rounds tracking, and anonymous safety reporting suite built using a modern **Next.js frontend** and **FastAPI backend**.

---

## 🏥 Architecture Overview

```
infection_ctrl_web/
├── frontend/                  # Next.js (App Router, Tailwind CSS, TypeScript)
├── backend/                   # FastAPI Web Server (SQLAlchemy, Alembic, Celery)
├── nginx.conf                 # Local Gateway Reverse Proxy Config
├── docker-compose.yml         # Local Development Orchestration
└── docker-compose.prod.yml    # Production Docker Orchestration Setup
```

---

## 🚀 Quick Start: Local Development

The entire platform is containerized using Docker. To spin up the backend API, Next.js web application, database, Redis cache, and storage server locally, run:

```bash
docker compose up --build
```

### Deployed Local Services:
* **Next.js Web App**: [http://localhost:3000](http://localhost:3000)
* **FastAPI Backend (Swagger API Docs)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **MinIO Object Storage Console**: [http://localhost:9001](http://localhost:9001) (User: `minioadmin` / Pass: `minioadminpassword`)

### Initial Login Credentials:
* **Email**: `admin@hospital.com`
* **Password**: `adminpassword123`

---

## 💎 Core Features

1. **Compliance Audits & Dynamic Scoring**: Automated compliance score calculations, dynamic risk classification triggers, and automatic CAPA generation for failed items.
2. **Corrective & Preventive Actions (CAPA) Kanban**: Drag-and-drop actions tracker with options to edit details, resolve tickets, and download formatted PDF action logs.
3. **Interactive Daily Rounds Module**:
   * Distraction-free walk tracker with structural floor/department progress ribbons.
   * Fuzzy-search observations library containing **500+ pre-seeded clinical items**.
   * Nested room & bed selector grids to reduce manual typings on tablets.
   * Simulated Speech-to-Text NLP logger & photo attachment evidence.
4. **Public Anonymous Safety Reporting (Quick Report)**: Let staff capture non-conformances with geolocation GPS pinpoints and photo evidence uploads directly from the login screen.
5. **Self-Registration with OTP Verification**: Registers users to the inactive queue. Authenticates email addresses via a 2-step Redis-backed verification code.
6. **Slate Dark/Light Mode Theme**: Global persist-to-storage darkslate aesthetic toggler.

---

## 🌐 Public Cloud Web Deployment

To deploy this repository live for tablet and mobile phone evaluation:

### 1. Database & Cache Infrastructure (Free Cloud Tiers)
* **Database**: Create a PostgreSQL database on [Supabase](https://supabase.com). Apply migrations locally:
  ```bash
  DATABASE_URL="postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres" alembic upgrade head
  ```
* **Redis Cache**: Create a Serverless Redis instance on [Upstash](https://upstash.com).
* **Storage**: Create a bucket on [Cloudflare R2](https://www.cloudflare.com/developer-platform/r2/) or AWS S3.

### 2. Frontend Host (Vercel)
1. Add a project in [Vercel](https://vercel.com) pointing to the `/frontend` subfolder.
2. Configure Environment Variable:
   * `NEXT_PUBLIC_API_URL` = `https://your-backend-app.onrender.com/api/v1`

### 3. Backend Host (Render or Railway)
1. Deploy a Web Service pointing to the `/backend` subfolder.
2. Configure Environment Variables:
   * `DATABASE_URL` = `postgresql+psycopg2://postgres:[password]@db.[supabase-ref].supabase.co:5432/postgres`
   * `REDIS_URL` = `redis://default:[password]@[upstash-endpoint].upstash.io:6379`
   * `JWT_SECRET` = `[your-custom-jwt-secret]`
   * `MINIO_ENDPOINT` = `[your-r2-or-s3-endpoint-domain]`
   * `MINIO_ACCESS_KEY` & `MINIO_SECRET_KEY` = `[your-s3-credentials]`
   * `MINIO_BUCKET_NAME` = `infection-control-media`
   * `MINIO_SECURE` = `True`
   * `BACKEND_CORS_ORIGINS` = `https://your-frontend-app.vercel.app`
