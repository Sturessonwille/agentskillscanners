#!/usr/bin/env python3
import os

import pytest
import requests

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")


def validate_response(response, expected_status=200, required_fields=None):
    assert response.status_code == expected_status, (
        f"Expected {expected_status}, got {response.status_code}: {response.text}"
    )
    ct = response.headers.get("content-type", "")
    if required_fields and ct.startswith("application/json"):
        body = response.json()
        for field in required_fields:
            assert field in body, f"Missing required field: {field}"
    return response


def test_health():
    resp = requests.get(f"{BASE_URL}/health", timeout=30)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_user():
    resp = requests.post(
        f"{BASE_URL}/users",
        json={"email": "test@example.com", "name": "Test User"},
        timeout=30,
    )
    validate_response(resp, 201)
    data = resp.json()
    assert "id" in data
    assert data["email"] == "test@example.com"


def test_unauthorized_access():
    resp = requests.get(f"{BASE_URL}/admin/users", timeout=30)
    validate_response(resp, 401)
