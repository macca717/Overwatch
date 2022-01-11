import asyncio
import json
from typing import Any, Dict
from subprocess import Popen
import requests
import pytest
import pytest_check as check
from websockets.legacy import client
from app.datastructures import AppConfig
from app.helpers import TimeoutAfter

WS_ADDRESS = "ws://localhost:8888/"
HTTP_ADDRESS = "http://localhost:8888/"
JPEG_START_BYTES = b"\xff\xd8"
JPEG_END_BYTES = b"\xff\xd9"

pytestmark = pytest.mark.integration


def is_command_response(rx_data) -> bool:
    if "status" in rx_data or "error" in rx_data:
        return True
    return False


@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_status_update_correct():
    required_fields = (
        "timeStamp",
        "state",
        "silencedTill",
        "initialAlarm",
    )
    async with client.connect(WS_ADDRESS) as conn:
        with TimeoutAfter(2):
            resp = await conn.recv()
            data: Dict[str, Any] = json.loads(resp)
            for field in required_fields:
                check.is_in(field, data.keys())


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_correct_silence_command():
    async with client.connect(WS_ADDRESS) as conn:
        await conn.send(json.dumps({"command": "silence", "data": {"silenceFor": 1}}))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert rx_data == {"status": "OK"}
                break


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_correct_test_command():
    async with client.connect(WS_ADDRESS) as conn:
        await conn.send(json.dumps({"command": "test", "data": {"excluded": []}}))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert rx_data == {"status": "OK"}
                break


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_correct_config_update_command(test_config: AppConfig):
    async with client.connect(WS_ADDRESS) as conn:
        await conn.send(
            json.dumps(
                {
                    "command": "config_update",
                    "data": {"config": test_config.dict()},
                }
            )
        )
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert rx_data == {"status": "OK"}
                break


@pytest.mark.timeout(60)
@pytest.mark.asyncio
async def test_shutdown_command(app_with_handle):
    process: Popen = app_with_handle
    async with client.connect("ws://localhost:7777/") as conn:
        await conn.send(json.dumps({"command": "shutdown", "data": {"shutdownIn": 0}}))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert rx_data == {"status": "OK"}
                break
    process.wait(timeout=10)
    assert process.returncode == 0


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_silence_bad_field():
    async with client.connect(WS_ADDRESS) as conn:
        data = {"command": "silence", "data": {"wrong_field": 180}}
        await conn.send(json.dumps(data))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert "error" in rx_data
                break


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_silence_cmd_bad_data_type():
    async with client.connect(WS_ADDRESS) as conn:
        data = {"command": "silence", "data": {"excluded": []}}
        await conn.send(json.dumps(data))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert "error" in rx_data
                break


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_test_cmd_bad_field():
    async with client.connect(WS_ADDRESS) as conn:
        data = {"command": "test", "data": {"wrong_field": []}}
        await conn.send(json.dumps(data))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert "error" in rx_data
                break


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_test_cmd_bad_data_type():
    async with client.connect(WS_ADDRESS) as conn:
        data = {"command": "test", "data": {"silenced_for": 456}}
        await conn.send(json.dumps(data))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert "error" in rx_data
                break


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_config_cmd_bad_field():
    async with client.connect(WS_ADDRESS) as conn:
        data = {"command": "config_update", "data": {"wrong_field": []}}
        await conn.send(json.dumps(data))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert "error" in rx_data
                break


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_config_cmd_bad_data_type():
    async with client.connect(WS_ADDRESS) as conn:
        data = {"command": "config_update", "data": {"silenced_for": 456}}
        await conn.send(json.dumps(data))
        while True:
            resp = await conn.recv()
            rx_data = json.loads(resp)
            if is_command_response(rx_data):
                assert "error" in rx_data
                break


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_raw_video_endpoint():
    async with client.connect(WS_ADDRESS + "raw-video") as conn:
        jpeg_start_bytes = b"\xff\xd8"
        jpeg_end_bytes = b"\xff\xd9"
        resp = await conn.recv()
        check.equal(resp[:2], jpeg_start_bytes)
        check.equal(resp[-2:], jpeg_end_bytes)


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with client.connect(WS_ADDRESS + "metrics") as conn:
        resp = await conn.recv()
        required_fields = (
            "timeStamp",
            "sysCpuPercent",
            "sysMemPercent",
            "capCpuPercent",
            "capMemPercent",
            "socketConnections",
            "loopAvgS",
            "loopMaxS",
            "loopMinS",
        )
        recv_json: Dict[str, Any] = json.loads(resp)
        for field in required_fields:
            assert field in recv_json.keys()


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
def test_health_endpoint():
    resp = requests.get(HTTP_ADDRESS + "health")
    resp.raise_for_status()
    assert resp.text == "OK\n"


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
def test_snapshot_endpoint():
    resp = requests.get(HTTP_ADDRESS + "snapshot")
    resp.raise_for_status()
    data = resp.content
    check.equal(data[:2], JPEG_START_BYTES)
    check.equal(data[-2:], JPEG_END_BYTES)


@pytest.mark.timeout(45)
@pytest.mark.usefixtures("app")
def test_config_get_endpoint():
    resp = requests.get(HTTP_ADDRESS + "config")
    resp.raise_for_status()
    data = resp.content
    AppConfig.parse_raw(data)
