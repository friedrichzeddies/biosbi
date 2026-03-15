from pathlib import Path
from typing import Any

import markdown
import yaml
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

BASE = Path(__file__).resolve().parent
CONTENT_DIR = BASE / "content"
LAYOUT_FILE = BASE / "layout.yaml"
templates = Jinja2Templates(directory=str(BASE / "templates"))

app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


def load_blocks() -> list[dict[str, Any]]:
    raw_layout = yaml.safe_load(LAYOUT_FILE.read_text(encoding="utf-8")) or []
    if not isinstance(raw_layout, list):
        return []

    blocks: list[dict[str, Any]] = []
    for item in raw_layout:
        if not isinstance(item, dict):
            continue

        block_type = item.get("type")
        if block_type == "markdown":
            file_name = str(item.get("file", "")).strip()
            md_file = CONTENT_DIR / file_name
            if file_name and md_file.exists():
                raw_text = md_file.read_text(encoding="utf-8")
                html = markdown.markdown(raw_text, extensions=["extra", "tables", "fenced_code"])
            else:
                html = f"<p>Missing markdown file: <code>{file_name or 'undefined'}</code></p>"

            blocks.append({"type": "markdown", "file": file_name, "html": html})

        elif block_type == "interactive":
            blocks.append({"type": "interactive", "name": str(item.get("name", "interactive"))})

    return blocks


@app.get("/")
def read_page(request: Request):
    return templates.TemplateResponse("page.html", {"request": request, "blocks": load_blocks()})


@app.post("/api/forward-sim")
async def forward_sim_stub(payload: dict[str, Any] | None = None):
    return {
        "status": "placeholder",
        "message": "forward_sim endpoint wired. Execution not implemented yet.",
        "received": payload or {},
    }