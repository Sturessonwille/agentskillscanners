#!/usr/bin/env python3
import requests
import json


def test_endpoint(url, method="GET", headers=None, data=None):
    """Test a single API endpoint."""
    response = requests.request(method, url, headers=headers, json=data)
    return {
        "status": response.status_code,
        "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
        "time_ms": response.elapsed.total_seconds() * 1000
    }


def validate_response(response, expected_status=200, required_fields=None):
    assert response["status"] == expected_status
    if required_fields:
        for field in required_fields:
            assert field in response["body"]
