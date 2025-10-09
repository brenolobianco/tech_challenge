# 🚀 Tech Challenge – Marketing Audience Campaign Builder

## 🧠 Overview

Welcome to the **Marketing Audience Tech Challenge**!

Your goal is to build a **full-stack web application** using **Python (FastAPI or Django)** and **React** that allows users to upload a `.csv` file containing customer data.  
The system should process this data asynchronously and create **segmented marketing campaigns** in the database based on predefined business logic.

This challenge is designed to evaluate:
- Backend design and architecture
- Asynchronous task management (background jobs)
- Data modeling and persistence
- Frontend interaction and visualization
- Clean code and documentation

---

## ⚙️ Technical Scope

### 1. CSV Upload and Processing

- The user uploads a `.csv` file with customer data, containing fields:
  -     `id,name,age,city,income` 


- The backend:
- Parses and validates the CSV
- Stores users into a `users` table
- Triggers a **background job** that will segment these users into different marketing campaigns

---

### 2. Background Job – Campaign Generation

Once the CSV is uploaded, a **background worker** (e.g., Celery, RQ, Dramatiq, or equivalent) should:

1. Retrieve all users from the database  
2. Segment them into **three marketing campaigns** based on the following logic:

| Campaign | Criteria |
|-----------|-----------|
| **Starter** | `age < 30 and income < 3000` |
| **Growth** | `30 ≤ age ≤ 50 and 3000 ≤ income ≤ 10000` |
| **Premium** | `age > 50 or income > 10000` |

3. Persist these campaigns in the database:
 - Table `campaigns` → stores campaign metadata
 - Table `campaign_users` → maps users to their respective campaign

4. Ensure **idempotency** — if the job runs multiple times, it should not duplicate data.

---

### 3. API Endpoints

| Method | Route | Description |
|--------|--------|-------------|
| `POST /upload` | Upload CSV and trigger campaign generation job |
| `GET /campaigns` | List all campaigns and their statistics |
| `GET /campaigns/{id}` | Retrieve a campaign with its users |
| `GET /users` | (Optional) List all users |

#### Example response
```json
{
"campaigns": [
  {
    "id": 1,
    "name": "Starter",
    "users_count": 42,
    "average_income": 2850.40
  },
  {
    "id": 2,
    "name": "Growth",
    "users_count": 57,
    "average_income": 6250.32
  },
  {
    "id": 3,
    "name": "Premium",
    "users_count": 31,
    "average_income": 11320.88
  }
]
}
