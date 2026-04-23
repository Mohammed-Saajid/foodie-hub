from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exception_handlers import setup_exception_handlers
from app.core.exceptions import BaseAppException


class _RequestModel(BaseModel):
    count: int


class _InternalModel(BaseModel):
    count: int


def _build_app() -> FastAPI:
    app = FastAPI()
    setup_exception_handlers(app)

    @app.post("/request-validation")
    async def request_validation(payload: _RequestModel):
        return {"count": payload.count}

    @app.get("/sqlalchemy")
    async def sqlalchemy_failure():
        raise SQLAlchemyError("db unavailable")

    @app.get("/runtime")
    async def runtime_failure():
        raise RuntimeError("runtime exploded")

    @app.get("/domain-details")
    async def domain_with_valid_details():
        raise BaseAppException(
            status_code=409,
            code="CONFLICT",
            message="domain conflict",
            details={"loc": ["field"], "msg": "invalid", "type": "conflict"},
        )

    @app.get("/domain-malformed")
    async def domain_with_malformed_details():
        raise BaseAppException(
            status_code=400,
            code="BAD_REQUEST",
            message="domain malformed",
            details={"loc": None, "msg": "invalid", "type": "error"},
        )

    @app.get("/http-with-headers")
    async def http_with_headers():
        raise StarletteHTTPException(status_code=418, detail="teapot", headers={"X-Test": "1"})

    @app.get("/http-no-headers")
    async def http_no_headers():
        raise StarletteHTTPException(status_code=404, detail="missing")

    @app.get("/unhandled")
    async def unhandled_exception():
        raise ValueError("unexpected")

    @app.get("/pydantic-validation")
    async def pydantic_validation():
        _InternalModel.model_validate({"count": "not-an-int"})
        return {"ok": True}

    return app


def _build_client() -> TestClient:
    return TestClient(_build_app(), raise_server_exceptions=False)


def test_sqlalchemy_exception_handler():
    client = _build_client()
    response = client.get("/sqlalchemy")

    assert response.status_code == 500
    body = response.json()
    assert body["message"] == "Database error occurred."


def test_runtime_exception_handler():
    client = _build_client()
    response = client.get("/runtime")

    assert response.status_code == 500
    body = response.json()
    assert body["message"] == "A runtime error occurred."
    assert body["details"][0]["type"] == "runtime_error"


def test_app_exception_handler_with_valid_details():
    client = _build_client()
    response = client.get("/domain-details")

    assert response.status_code == 409
    body = response.json()
    assert body["message"] == "domain conflict"
    assert body["details"][0]["loc"] == ["field"]
    assert body["details"][0]["msg"] == "invalid"


def test_app_exception_handler_with_malformed_details():
    client = _build_client()
    response = client.get("/domain-malformed")

    assert response.status_code == 400
    body = response.json()
    assert body["message"] == "domain malformed"
    assert body["details"] == []


def test_request_validation_exception_handler():
    client = _build_client()
    response = client.post("/request-validation", json={"count": "bad"})

    assert response.status_code == 422
    body = response.json()
    assert body["message"] == "The request payload is invalid."
    assert body["details"][0]["loc"] == ["body", "count"]


def test_http_exception_handler_with_and_without_headers():
    client = _build_client()

    with_headers = client.get("/http-with-headers")
    assert with_headers.status_code == 418
    assert with_headers.json()["message"] == "teapot"
    assert with_headers.headers["x-test"] == "1"

    no_headers = client.get("/http-no-headers")
    assert no_headers.status_code == 404
    assert no_headers.json()["message"] == "missing"


def test_global_exception_handler():
    client = _build_client()
    response = client.get("/unhandled")

    assert response.status_code == 500
    body = response.json()
    assert body["message"] == "An unexpected server error occurred."


def test_pydantic_validation_exception_handler():
    client = _build_client()
    response = client.get("/pydantic-validation")

    assert response.status_code == 422
    body = response.json()
    assert body["message"] == "An internal validation error occurred."
    assert body["details"][0]["loc"] == ["count"]
