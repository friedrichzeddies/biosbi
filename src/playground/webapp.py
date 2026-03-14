from __future__ import annotations

import html
import json
from ipaddress import ip_address
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import markdown
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


APP_TITLE = "biosbi local playground"

PLAYGROUND_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = PLAYGROUND_DIR / "templates"
STATIC_DIR = PLAYGROUND_DIR / "static"
CONTENT_PATH = PLAYGROUND_DIR / "content.md"
SIM_PARAMS_PATH = PLAYGROUND_DIR.parent / "forward_sim" / "simulation_parameters.json"


class MarkdownRequest(BaseModel):
    text: str = Field(default="")


class RelayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_url: HttpUrl
    payload: dict[str, Any]


class SimulationParametersUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    parameters: dict[str, Any]


def _is_loopback_host(hostname: str | None) -> bool:
    if hostname is None:
        return False
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ip_address(hostname).is_loopback
    except ValueError:
        return False


def _validate_local_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Only http:// or https:// local targets are allowed.")
    if not _is_loopback_host(parsed.hostname):
        raise HTTPException(status_code=400, detail="Relay target must be localhost or another loopback address.")


def _render_markdown(text: str) -> str:
    safe_input = html.escape(text, quote=False)
    return markdown.markdown(safe_input, extensions=["extra", "nl2br"])


def _read_simulation_parameters() -> dict[str, Any]:
    if not SIM_PARAMS_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Simulation parameters not found: {SIM_PARAMS_PATH}")

    try:
        data = json.loads(SIM_PARAMS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in simulation parameters file: {exc}") from exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="Simulation parameters file must contain a JSON object.")

    return data


def _write_simulation_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    SIM_PARAMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SIM_PARAMS_PATH.write_text(json.dumps(parameters, indent=4) + "\n", encoding="utf-8")
    return parameters


def create_app() -> FastAPI:
    app = FastAPI(title=APP_TITLE)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(TEMPLATES_DIR / "index.html")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/content")
    async def blog_content() -> dict[str, str]:
        if not CONTENT_PATH.exists():
            raise HTTPException(status_code=404, detail=f"Markdown content not found: {CONTENT_PATH}")
        markdown_text = CONTENT_PATH.read_text(encoding="utf-8")
        return {"html": _render_markdown(markdown_text)}

    @app.post("/api/render-markdown")
    async def render_markdown(request: MarkdownRequest) -> dict[str, str]:
        return {"html": _render_markdown(request.text)}

    @app.get("/api/simulation-parameters")
    async def get_simulation_parameters() -> dict[str, Any]:
        return {"parameters": _read_simulation_parameters()}

    @app.put("/api/simulation-parameters")
    async def put_simulation_parameters(request: SimulationParametersUpdate) -> dict[str, Any]:
        return {"parameters": _write_simulation_parameters(request.parameters)}

    @app.post("/api/relay")
    async def relay(request: RelayRequest) -> dict[str, Any]:
        _validate_local_url(str(request.target_url))

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(str(request.target_url), json=request.payload)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Local relay request failed: {exc}") from exc

        content_type = response.headers.get("content-type", "")
        body: Any
        if "application/json" in content_type:
            body = response.json()
        else:
            body = response.text

        return {
            "target_url": str(request.target_url),
            "status_code": response.status_code,
            "body": body,
        }

    return app