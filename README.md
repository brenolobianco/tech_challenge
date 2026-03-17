# Tech Challenge – Marketing Audience Campaign Builder

## Overview

Welcome to the **Marketing Audience Tech Challenge**!

Your goal is to build a **full-stack web application** using **Python (FastAPI or Django)** and **React** that allows users to upload a `.csv` file containing customer data.
The system should process this data asynchronously and create **segmented marketing campaigns** in the database based on predefined business logic.

This challenge is designed to evaluate:
- Backend design and architecture
- Asynchronous task management (background jobs)
- Data modeling and persistence
- Error handling and edge cases
- API design consistency
- Testing practices
- Frontend interaction and visualization
- Clean code and documentation

---

## Technical Scope

### 1. CSV Upload and Processing

The user uploads a `.csv` file with customer data, containing fields:

```
id,name,age,city,income
```

#### Row-level Validation

Each row must be validated individually. The following rules apply:

| Field    | Validation                              |
|----------|-----------------------------------------|
| `id`     | Required, must be a positive integer    |
| `name`   | Required, non-empty string              |
| `age`    | Required, positive integer              |
| `city`   | Required, non-empty string              |
| `income` | Required, non-negative number           |

- **Valid rows** are stored in the `users` table and processed normally.
- **Invalid rows** are skipped but reported in the upload response.
- The upload is **not** rejected entirely due to invalid rows — partial success is expected.

#### Upload Response

The `POST /upload` endpoint should return immediately with an `upload_id` and status `"processing"`:

```json
{
  "upload_id": "abc-123",
  "status": "processing",
  "total_rows": 100,
  "valid_rows": 95,
  "invalid_rows": 5,
  "errors": [
    { "row": 3, "field": "age", "message": "age must be a positive integer" },
    { "row": 17, "field": "income", "message": "income must be a non-negative number" },
    { "row": 42, "field": "name", "message": "name cannot be empty" }
  ]
}
```

**HTTP Status:** `201 Created`

---

### 2. Upload Tracking

A new `uploads` table tracks the lifecycle of each file upload:

| Column         | Description                                           |
|----------------|-------------------------------------------------------|
| `id`           | Unique upload identifier                              |
| `filename`     | Original filename                                     |
| `status`       | `pending` → `processing` → `completed` / `failed`    |
| `total_rows`   | Total rows in the CSV                                 |
| `valid_rows`   | Number of valid rows imported                         |
| `invalid_rows` | Number of invalid rows skipped                        |
| `created_at`   | Timestamp of upload                                   |
| `processed_at` | Timestamp when processing finished (nullable)         |

The upload status can be queried via `GET /upload/{upload_id}/status`.

---

### 3. Background Job – Campaign Generation

Once the CSV is uploaded, a **background worker** (e.g., Celery, RQ, Dramatiq, or equivalent) should:

1. Segment **only the users from that specific upload** into marketing campaigns (not all users in the database)
2. Apply the following segmentation rules:

| Campaign              | Criteria                                     |
|-----------------------|----------------------------------------------|
| **Starter**           | `age < 30 and income < 3000`                 |
| **Growth**            | `30 ≤ age ≤ 50 and 3000 ≤ income ≤ 10000`   |
| **Premium**           | `age > 50 or income > 10000`                 |
| **High Value Youth**  | `age < 30 and income > 5000`                 |

> **Note:** A user can belong to **more than one campaign**. For example, a 25-year-old with income 8000 qualifies for both **Premium** and **High Value Youth**. Make sure your data model supports this (many-to-many relationship).

3. Persist campaigns in the database:
   - Table `campaigns` → stores campaign metadata
   - Table `campaign_users` → maps users to their respective campaigns

4. Ensure **idempotency** — if the job runs multiple times for the same upload, it should not duplicate data.

5. Update the upload status to `completed` (or `failed` if an error occurs) and set `processed_at`.

---

### 4. API Endpoints

| Method | Route                        | Description                                    |
|--------|------------------------------|------------------------------------------------|
| `POST` | `/upload`                    | Upload CSV and trigger campaign generation      |
| `GET`  | `/upload/{upload_id}/status` | Get upload processing status                    |
| `GET`  | `/campaigns`                 | List all campaigns with statistics (paginated)  |
| `GET`  | `/campaigns/{id}`            | Retrieve a campaign with its users (paginated)  |
| `GET`  | `/users`                     | List all users (paginated, with filters)        |

#### Pagination

All list endpoints must return a **standardized paginated envelope**:

```json
{
  "data": [],
  "page": 1,
  "page_size": 20,
  "total": 150
}
```

#### Filters

| Endpoint            | Supported Filters                                          |
|---------------------|------------------------------------------------------------|
| `GET /campaigns`    | `upload_id` (filter campaigns by originating upload)       |
| `GET /campaigns/{id}` | Paginated user list within the campaign                 |
| `GET /users`        | `name` (search/partial match), `min_age`, `max_age`, `min_income`, `max_income` |

#### Example: `GET /campaigns`

```json
{
  "data": [
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
    },
    {
      "id": 4,
      "name": "High Value Youth",
      "users_count": 8,
      "average_income": 7540.25
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 4
}
```

---

### 5. Error Handling and HTTP Semantics

Your API should use **correct HTTP status codes** consistently:

| Status Code | When to Use                                              |
|-------------|----------------------------------------------------------|
| `201`       | Successful upload (`POST /upload`)                       |
| `200`       | Successful retrieval                                     |
| `400`       | Invalid request (e.g., missing file, wrong content type) |
| `404`       | Resource not found (upload, campaign, or user)           |
| `422`       | Malformed CSV (e.g., wrong headers, unparseable file)    |

All error responses must follow a **consistent structure**:

```json
{
  "error": "not_found",
  "message": "Campaign with id 99 was not found",
  "details": null
}
```

**Duplicate uploads:** You should decide on a strategy for handling duplicate CSV uploads (e.g., reject, overwrite, or create new). Document your choice and reasoning in your project README.

---

### 6. Database Schema

Your application must have **four database tables**:

| Table            | Description                              |
|------------------|------------------------------------------|
| `uploads`        | Tracks each CSV upload and its status    |
| `users`          | Stores customer data from CSV            |
| `campaigns`      | Stores campaign metadata                 |
| `campaign_users` | Many-to-many mapping of users to campaigns |

The `users` table should reference which upload it came from (`upload_id` foreign key).

---

### 7. Testing Requirements

You must include automated tests covering at minimum:

- **CSV validation logic:** valid file, rows with invalid data, empty file, wrong/missing headers
- **Segmentation rules:** verify each campaign's criteria, including overlap cases (e.g., a user qualifying for both Premium and High Value Youth) and edge cases on boundaries
- **At least 1 integration test:** end-to-end upload flow (upload CSV → verify users created → verify campaigns generated)

> We value **quality over quantity** — well-structured, meaningful tests are preferred over high coverage with shallow assertions.

---

### 8. Logging

Implement **structured logging** for key operations:

- Upload received (filename, row count)
- Background job started / completed / failed
- Campaign generation results (count per campaign)

All log entries related to a specific upload should include the `upload_id` for traceability.

> Python's standard `logging` library is sufficient — no external logging frameworks are required.

---

### 9. Frontend Requirements

Build a React frontend that provides:

- **Upload interface:** file input to upload a CSV file
- **Upload progress/status:** after uploading, poll `GET /upload/{upload_id}/status` and display the current status (processing, completed, failed)
- **Validation errors:** display any row-level validation errors returned from the upload
- **Campaign list:** table or cards showing each campaign with `users_count` and `average_income`
- **Campaign detail:** click a campaign to see its users (with pagination)
- **User list:** paginated list of all users with search/filter support

---

### 10. Bonus (Not Required)

These are not mandatory but will be positively evaluated:

- **Docker Compose** setup for the full stack (backend + worker + database + frontend)
- **OpenAPI/Swagger** documentation auto-generated from your API
- **Rate limiting** on the upload endpoint
- **WebSocket or SSE** for real-time upload status updates (instead of polling)

---

## Evaluation Criteria

Your submission will be evaluated in the following order of importance:

1. **Functional solution** — the application works and meets the stated requirements
2. **Code organization, readability, and maintainability** — clean structure, clear naming, separation of concerns
3. **Error handling and edge cases** — graceful handling of invalid input, failures, and boundary conditions
4. **Test quality** — meaningful, well-structured tests that cover critical paths
5. **API design consistency** — proper use of HTTP methods, status codes, pagination, and response formats
6. **Documentation** — README explaining setup instructions, architectural decisions, and trade-offs

---

## Submission

- Push your code to a **public GitHub repository**
- Include a `README.md` in your project with:
  - Setup and run instructions
  - Architectural decisions and trade-offs
  - Your strategy for handling duplicate uploads (and why)
  - Any assumptions or known limitations
- Ensure the application can be started and tested by the reviewer
