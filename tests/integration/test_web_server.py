import requests
import pytest


@pytest.mark.usefixtures("app")
def test_health_endpoint():
    resp = requests.get("http://localhost:8003/health", timeout=5)
    resp.raise_for_status()
    assert resp.text == "UP"


@pytest.mark.usefixtures("app")
def test_report_submit_success():
    form_data = {
        "date-time": "10/03/2010 23:45",
        "duration-minutes": "10",
        "drug-administered": "on",
        "details-text": "Test suite added",
        "hospitalization-required": "on",
    }
    resp = requests.post("http://localhost:8003/reports", form_data)
    resp.raise_for_status()
