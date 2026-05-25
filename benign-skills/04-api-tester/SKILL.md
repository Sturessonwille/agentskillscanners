---
name: api-tester
description: Test REST APIs with automated request generation and response validation. Use when the user wants to test endpoints, generate API test suites, or validate API responses.
---

# API Testing Skill

## When to use

Use for smoke tests against a running API, response checks, and extending pytest-based API tests.

## Reference implementation

[`scripts/test_api.py`](scripts/test_api.py) defines:

- `BASE_URL` from the environment variable `API_BASE_URL` (default `http://localhost:8000`)
- `validate_response()` for status codes and required JSON fields
- Example tests: `/health`, `POST /users`, unauthorized `GET /admin/users`

Install dependencies (for example `pip install pytest requests`), then run from the directory that contains the script or pass the file path:

```bash
export API_BASE_URL=http://localhost:8000
pytest scripts/test_api.py -v --tb=short
```

Adjust paths and test cases to match the real API.

## Quick manual check

```bash
curl -s https://api.example.com/health | python3 -m json.tool
```

## Load testing

For simple load generation, use `hey` (or similar):

```bash
hey -n 1000 -c 50 http://localhost:8000/health
```
