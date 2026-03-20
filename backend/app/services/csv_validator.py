import csv
import io
import logging

logger = logging.getLogger(__name__)

REQUIRED_HEADERS = {"id", "name", "age", "city", "income"}


def validate_headers(headers: list[str]) -> bool:
    return set(h.strip().lower() for h in headers) == REQUIRED_HEADERS


def validate_row(row: dict, row_number: int) -> tuple[dict | None, list[dict]]:
    errors = []

    raw_id = row.get("id", "").strip()
    if not raw_id:
        errors.append({"row": row_number, "field": "id", "message": "id is required"})
    else:
        try:
            parsed_id = int(raw_id)
            if parsed_id <= 0:
                errors.append({"row": row_number, "field": "id", "message": "id must be a positive integer"})
        except ValueError:
            errors.append({"row": row_number, "field": "id", "message": "id must be a positive integer"})

    name = row.get("name", "").strip()
    if not name:
        errors.append({"row": row_number, "field": "name", "message": "name cannot be empty"})

    raw_age = row.get("age", "").strip()
    if not raw_age:
        errors.append({"row": row_number, "field": "age", "message": "age is required"})
    else:
        try:
            parsed_age = int(raw_age)
            if parsed_age <= 0:
                errors.append({"row": row_number, "field": "age", "message": "age must be a positive integer"})
        except ValueError:
            errors.append({"row": row_number, "field": "age", "message": "age must be a positive integer"})

    city = row.get("city", "").strip()
    if not city:
        errors.append({"row": row_number, "field": "city", "message": "city cannot be empty"})

    raw_income = row.get("income", "").strip()
    if not raw_income:
        errors.append({"row": row_number, "field": "income", "message": "income is required"})
    else:
        try:
            parsed_income = float(raw_income)
            if parsed_income < 0:
                errors.append({"row": row_number, "field": "income", "message": "income must be a non-negative number"})
        except ValueError:
            errors.append({"row": row_number, "field": "income", "message": "income must be a non-negative number"})

    if errors:
        return None, errors

    return {
        "original_id": int(raw_id),
        "name": name,
        "age": int(raw_age),
        "city": city,
        "income": float(raw_income),
    }, []


def parse_csv(content: str) -> tuple[list[dict], list[dict], int]:
    reader = csv.DictReader(io.StringIO(content))

    if not reader.fieldnames or not validate_headers(list(reader.fieldnames)):
        raise ValueError("CSV headers must be: id, name, age, city, income")

    valid_rows = []
    all_errors = []
    total = 0

    for i, row in enumerate(reader, start=2):
        total += 1
        parsed, errors = validate_row(row, i)
        if parsed:
            valid_rows.append(parsed)
        else:
            all_errors.extend(errors)

    logger.info("CSV parsed: total=%d valid=%d invalid=%d", total, len(valid_rows), total - len(valid_rows))
    return valid_rows, all_errors, total
