import pytest

from app.services.csv_validator import parse_csv, validate_row


class TestValidateRow:
    def test_valid_row(self):
        row = {"id": "1", "name": "Alice", "age": "25", "city": "NYC", "income": "5000"}
        parsed, errors = validate_row(row, 2)
        assert parsed is not None
        assert errors == []
        assert parsed["original_id"] == 1
        assert parsed["name"] == "Alice"
        assert parsed["age"] == 25
        assert parsed["income"] == 5000.0

    def test_missing_id(self):
        row = {"id": "", "name": "Alice", "age": "25", "city": "NYC", "income": "5000"}
        parsed, errors = validate_row(row, 2)
        assert parsed is None
        assert len(errors) == 1
        assert errors[0]["field"] == "id"

    def test_negative_id(self):
        row = {"id": "-1", "name": "Alice", "age": "25", "city": "NYC", "income": "5000"}
        parsed, errors = validate_row(row, 2)
        assert parsed is None
        assert errors[0]["field"] == "id"

    def test_empty_name(self):
        row = {"id": "1", "name": "", "age": "25", "city": "NYC", "income": "5000"}
        parsed, errors = validate_row(row, 3)
        assert parsed is None
        assert errors[0]["field"] == "name"
        assert errors[0]["row"] == 3

    def test_negative_age(self):
        row = {"id": "1", "name": "Alice", "age": "-5", "city": "NYC", "income": "5000"}
        parsed, errors = validate_row(row, 2)
        assert parsed is None
        assert errors[0]["field"] == "age"

    def test_non_numeric_age(self):
        row = {"id": "1", "name": "Alice", "age": "abc", "city": "NYC", "income": "5000"}
        parsed, errors = validate_row(row, 2)
        assert parsed is None
        assert errors[0]["field"] == "age"

    def test_empty_city(self):
        row = {"id": "1", "name": "Alice", "age": "25", "city": "", "income": "5000"}
        parsed, errors = validate_row(row, 2)
        assert parsed is None
        assert errors[0]["field"] == "city"

    def test_negative_income(self):
        row = {"id": "1", "name": "Alice", "age": "25", "city": "NYC", "income": "-100"}
        parsed, errors = validate_row(row, 2)
        assert parsed is None
        assert errors[0]["field"] == "income"

    def test_zero_income_is_valid(self):
        row = {"id": "1", "name": "Alice", "age": "25", "city": "NYC", "income": "0"}
        parsed, errors = validate_row(row, 2)
        assert parsed is not None
        assert parsed["income"] == 0.0

    def test_multiple_errors_in_one_row(self):
        row = {"id": "", "name": "", "age": "abc", "city": "", "income": "-1"}
        parsed, errors = validate_row(row, 2)
        assert parsed is None
        assert len(errors) == 5


class TestParseCsv:
    def test_valid_csv(self):
        content = "id,name,age,city,income\n1,Alice,25,NYC,5000\n2,Bob,35,LA,8000"
        valid, errors, total = parse_csv(content)
        assert total == 2
        assert len(valid) == 2
        assert len(errors) == 0

    def test_csv_with_invalid_rows(self):
        content = "id,name,age,city,income\n1,Alice,25,NYC,5000\n2,,35,LA,8000"
        valid, errors, total = parse_csv(content)
        assert total == 2
        assert len(valid) == 1
        assert len(errors) == 1

    def test_wrong_headers(self):
        content = "wrong,headers,here\n1,2,3"
        with pytest.raises(ValueError, match="CSV headers"):
            parse_csv(content)

    def test_empty_csv_body(self):
        content = "id,name,age,city,income\n"
        valid, errors, total = parse_csv(content)
        assert total == 0
        assert len(valid) == 0

    def test_all_rows_invalid(self):
        content = "id,name,age,city,income\n,,,,"
        valid, errors, total = parse_csv(content)
        assert total == 1
        assert len(valid) == 0
        assert len(errors) > 0
