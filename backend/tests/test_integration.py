import io
import time


def _upload_csv(client, csv_content: str, filename: str = "test.csv"):
    """Helper to upload a CSV and return the response."""
    file = io.BytesIO(csv_content.encode("utf-8"))
    return client.post("/upload", files={"file": (filename, file, "text/csv")})


def _wait_for_completion(client, upload_id: str, timeout: int = 10):
    """Poll until upload is completed or failed."""
    for _ in range(timeout * 2):
        resp = client.get(f"/upload/{upload_id}/status")
        status = resp.json()["status"]
        if status in ("completed", "failed"):
            return resp.json()
        time.sleep(0.5)
    return resp.json()


class TestUploadFlow:
    def test_full_upload_flow(self, client):
        csv = "id,name,age,city,income\n1,Alice,25,NYC,8000\n2,Bob,35,LA,5000\n3,Carol,55,SF,2000\n"
        response = _upload_csv(client, csv)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "processing"
        assert data["total_rows"] == 3
        assert data["valid_rows"] == 3
        assert data["invalid_rows"] == 0
        upload_id = data["upload_id"]

        status = _wait_for_completion(client, upload_id)
        assert status["status"] == "completed"
        assert status["processed_at"] is not None

        users_resp = client.get("/users")
        assert users_resp.status_code == 200
        assert users_resp.json()["total"] == 3

        campaigns_resp = client.get(f"/campaigns?upload_id={upload_id}")
        assert campaigns_resp.status_code == 200
        campaigns_data = campaigns_resp.json()
        assert len(campaigns_data["data"]) == 4

        campaign_names = {c["name"] for c in campaigns_data["data"]}
        assert campaign_names == {"Starter", "Growth", "Premium", "High Value Youth"}

    def test_upload_with_invalid_rows(self, client):
        csv = "id,name,age,city,income\n1,Alice,25,NYC,8000\n2,,abc,LA,-100\n"
        response = _upload_csv(client, csv)
        assert response.status_code == 201
        data = response.json()
        assert data["valid_rows"] == 1
        assert data["invalid_rows"] == 1
        assert len(data["errors"]) > 0

    def test_upload_all_rows_invalid(self, client):
        csv = "id,name,age,city,income\n-1,,0,,-50\nabc,,xyz,,-1\n"
        response = _upload_csv(client, csv)
        assert response.status_code == 201
        data = response.json()
        assert data["valid_rows"] == 0
        assert data["invalid_rows"] == 2
        assert data["total_rows"] == 2


class TestUploadValidation:
    def test_wrong_headers(self, client):
        response = _upload_csv(client, "wrong,headers\n1,2\n")
        assert response.status_code == 422
        body = response.json()
        assert "error" in body
        assert "message" in body
        assert "details" in body

    def test_empty_file(self, client):
        file = io.BytesIO(b"")
        response = client.post("/upload", files={"file": ("test.csv", file, "text/csv")})
        assert response.status_code == 422
        assert response.json()["error"] == "empty_file"

    def test_not_csv(self, client):
        file = io.BytesIO(b"not a csv")
        response = client.post("/upload", files={"file": ("test.txt", file, "text/plain")})
        assert response.status_code == 400
        assert response.json()["error"] == "invalid_file"

    def test_whitespace_only_file(self, client):
        file = io.BytesIO(b"   \n  \n  ")
        response = client.post("/upload", files={"file": ("test.csv", file, "text/csv")})
        assert response.status_code == 422

    def test_headers_only_no_data(self, client):
        response = _upload_csv(client, "id,name,age,city,income\n")
        assert response.status_code == 201
        data = response.json()
        assert data["total_rows"] == 0
        assert data["valid_rows"] == 0


class TestNotFound:
    def test_nonexistent_upload(self, client):
        response = client.get("/upload/nonexistent/status")
        assert response.status_code == 404
        assert response.json()["error"] == "not_found"

    def test_nonexistent_campaign(self, client):
        response = client.get("/campaigns/99999")
        assert response.status_code == 404
        assert response.json()["error"] == "not_found"

    def test_nonexistent_upload_stream(self, client):
        response = client.get("/upload/nonexistent/stream")
        assert response.status_code == 404


class TestUsersFilters:
    def _seed(self, client):
        csv = "id,name,age,city,income\n1,Alice,25,NYC,8000\n2,Bob,35,LA,5000\n3,Carol,55,SF,2000\n"
        resp = _upload_csv(client, csv)
        _wait_for_completion(client, resp.json()["upload_id"])

    def test_filter_by_name(self, client):
        self._seed(client)
        resp = client.get("/users?name=Alice")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["data"][0]["name"] == "Alice"

    def test_filter_by_name_case_insensitive(self, client):
        self._seed(client)
        resp = client.get("/users?name=alice")
        assert resp.json()["total"] == 1

    def test_filter_by_min_age(self, client):
        self._seed(client)
        resp = client.get("/users?min_age=30")
        assert resp.json()["total"] == 2

    def test_filter_by_max_income(self, client):
        self._seed(client)
        resp = client.get("/users?max_income=6000")
        assert resp.json()["total"] == 2

    def test_filter_combined(self, client):
        self._seed(client)
        resp = client.get("/users?min_age=30&max_income=6000")
        assert resp.json()["total"] == 1
        assert resp.json()["data"][0]["name"] == "Bob"

    def test_filter_no_results(self, client):
        self._seed(client)
        resp = client.get("/users?name=NonExistent")
        assert resp.json()["total"] == 0
        assert resp.json()["data"] == []


class TestPagination:
    def _seed_many(self, client):
        rows = "id,name,age,city,income\n"
        for i in range(1, 26):
            rows += f"{i},User{i},{20 + i},City{i},{1000 * i}\n"
        resp = _upload_csv(client, rows)
        _wait_for_completion(client, resp.json()["upload_id"])

    def test_users_default_pagination(self, client):
        self._seed_many(client)
        resp = client.get("/users")
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total"] == 25
        assert len(data["data"]) == 20

    def test_users_page_2(self, client):
        self._seed_many(client)
        resp = client.get("/users?page=2")
        data = resp.json()
        assert data["page"] == 2
        assert len(data["data"]) == 5

    def test_users_custom_page_size(self, client):
        self._seed_many(client)
        resp = client.get("/users?page_size=5")
        data = resp.json()
        assert len(data["data"]) == 5
        assert data["total"] == 25

    def test_campaigns_pagination(self, client):
        self._seed_many(client)
        resp = client.get("/campaigns?page_size=2")
        data = resp.json()
        assert len(data["data"]) <= 2

    def test_campaign_detail_users_paginated(self, client):
        self._seed_many(client)
        campaigns = client.get("/campaigns").json()["data"]
        if campaigns:
            cid = campaigns[0]["id"]
            resp = client.get(f"/campaigns/{cid}?page_size=5")
            assert resp.status_code == 200
            assert resp.json()["users"]["page_size"] == 5

    def test_invalid_page_number(self, client):
        resp = client.get("/users?page=0")
        assert resp.status_code == 422

    def test_page_size_exceeds_max(self, client):
        resp = client.get("/users?page_size=200")
        assert resp.status_code == 422


class TestRateLimit:
    def test_upload_within_limit(self, client):
        """5 uploads should succeed."""
        csv = "id,name,age,city,income\n1,Test,25,City,1000\n"
        for i in range(5):
            resp = _upload_csv(client, csv)
            assert resp.status_code == 201, f"Request {i+1} should succeed"

    def test_upload_exceeds_limit(self, client):
        """6th upload should be rate limited."""
        csv = "id,name,age,city,income\n1,Test,25,City,1000\n"
        for _ in range(5):
            _upload_csv(client, csv)

        resp = _upload_csv(client, csv)
        assert resp.status_code == 429
        assert resp.json()["error"] == "rate_limit_exceeded"

    def test_rate_limit_does_not_affect_other_endpoints(self, client):
        """GET endpoints should not be affected by upload rate limit."""
        csv = "id,name,age,city,income\n1,Test,25,City,1000\n"
        for _ in range(5):
            _upload_csv(client, csv)

        resp = client.get("/users")
        assert resp.status_code == 200

        resp = client.get("/campaigns")
        assert resp.status_code == 200


class TestErrorResponseConsistency:
    """All error responses must follow {error, message, details} format."""

    def test_404_upload(self, client):
        body = client.get("/upload/fake/status").json()
        assert set(body.keys()) >= {"error", "message"}

    def test_404_campaign(self, client):
        body = client.get("/campaigns/99999").json()
        assert set(body.keys()) >= {"error", "message"}

    def test_400_not_csv(self, client):
        file = io.BytesIO(b"data")
        body = client.post("/upload", files={"file": ("x.txt", file, "text/plain")}).json()
        assert set(body.keys()) >= {"error", "message", "details"}

    def test_422_bad_headers(self, client):
        body = _upload_csv(client, "bad,headers\n1,2\n").json()
        assert set(body.keys()) >= {"error", "message", "details"}

    def test_429_rate_limit(self, client):
        csv = "id,name,age,city,income\n1,T,25,C,1000\n"
        for _ in range(5):
            _upload_csv(client, csv)
        body = _upload_csv(client, csv).json()
        assert set(body.keys()) >= {"error", "message"}
        assert body["error"] == "rate_limit_exceeded"
