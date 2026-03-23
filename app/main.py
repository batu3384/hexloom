"""FastAPI application entrypoint for Hexloom."""

from __future__ import annotations

import os
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from rich.console import Console
from rich.panel import Panel
from tqdm import tqdm

from app.engine import TransformationEngine, TransformationResult
from app.schemas import (
    BulkSummaryResponse,
    BulkTransformItemResponse,
    BulkTransformRequest,
    BulkTransformResponse,
    TransformRequest,
    TransformResponse,
)


BASE_DIR = Path(__file__).resolve().parent.parent
console = Console()
engine = TransformationEngine()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="Hexloom",
    version="0.1.0",
    description="Operational workspace for multi-format text transformations.",
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.middleware("http")
async def rich_request_logger(request: Request, call_next):
    started_at = time.perf_counter()
    body = await request.body()
    body_preview = body.decode("utf-8", errors="replace").strip()
    if len(body_preview) > 500:
        body_preview = f"{body_preview[:500]}..."

    client_host = request.client.host if request.client else "bilinmiyor"
    console.print(
        Panel.fit(
            f"[bold cyan]{request.method}[/bold cyan] {request.url.path}\n"
            f"[dim]{client_host}[/dim]",
            title="İstek",
            border_style="cyan",
        )
    )
    if body_preview:
        console.print(Panel(body_preview, title="İstek Gövdesi", border_style="blue"))

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request = Request(request.scope, receive)

    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        console.print(
            Panel.fit(
                f"[bold red]500[/bold red] İç Sunucu Hatası\n[dim]{elapsed_ms:.2f} ms[/dim]",
                title="Yanıt",
                border_style="red",
            )
        )
        raise

    elapsed_ms = (time.perf_counter() - started_at) * 1000
    border_style = "green" if response.status_code < 400 else "red"
    console.print(
        Panel.fit(
            f"[bold]{response.status_code}[/bold]\n[dim]{elapsed_ms:.2f} ms[/dim]",
            title="Yanıt",
            border_style=border_style,
        )
    )
    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    public_url = os.getenv("HEXLOOM_PUBLIC_URL", "").strip()
    if not public_url:
        public_url = str(request.base_url).rstrip("/")

    og_image_path = str(request.url_for("static", path="og-card.svg"))
    if og_image_path.startswith("http://") or og_image_path.startswith("https://"):
        og_image_url = og_image_path
    else:
        og_image_url = f"{public_url}{og_image_path}"

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "methods": engine.available_methods(),
            "asset_version": app.version,
            "public_url": public_url,
            "og_image_url": og_image_url,
        },
    )


@app.get("/methods")
async def methods():
    return {"methods": engine.available_methods()}


@app.get("/health/transformations")
async def transformation_health():
    report = engine.run_self_check()
    status_code = status.HTTP_200_OK if report["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=report)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.svg", media_type="image/svg+xml")


@app.post("/encode", response_model=TransformResponse, response_model_exclude_none=True)
async def encode(payload: TransformRequest):
    result = engine.encode(payload.data, payload.method)
    return _single_transform_response(result)


@app.post("/decode", response_model=TransformResponse, response_model_exclude_none=True)
async def decode(payload: TransformRequest):
    result = engine.decode(payload.data, payload.method)
    return _single_transform_response(result)


@app.post("/bulk/encode", response_model=BulkTransformResponse, response_model_exclude_none=True)
async def bulk_encode(payload: BulkTransformRequest):
    return _bulk_transform_response(payload, "encode")


@app.post("/bulk/decode", response_model=BulkTransformResponse, response_model_exclude_none=True)
async def bulk_decode(payload: BulkTransformRequest):
    return _bulk_transform_response(payload, "decode")


def _single_transform_response(result: TransformationResult) -> TransformResponse | JSONResponse:
    response = TransformResponse(
        status=result.status,
        result=result.result,
        message=result.message,
        clipboard_ready=result.clipboard_ready,
    )
    if result.status == "error":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response.model_dump(),
        )
    return response


def _bulk_transform_response(
    payload: BulkTransformRequest, operation: str
) -> BulkTransformResponse | JSONResponse:
    if not engine.is_supported(payload.method):
        error = TransformResponse(
            status="error",
            result=None,
            message=f"Bilinmeyen dönüşüm yöntemi: {payload.method}",
            clipboard_ready=False,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error.model_dump(),
        )

    handler = engine.encode if operation == "encode" else engine.decode
    item_results: list[BulkTransformItemResponse] = []
    success_count = 0

    progress = tqdm(
        payload.items,
        total=len(payload.items),
        desc=f"bulk-{operation}:{payload.method}",
        unit="item",
        leave=False,
    )
    for index, item in enumerate(progress):
        result = handler(item, payload.method)
        if result.status == "success":
            success_count += 1
        item_results.append(
            BulkTransformItemResponse(
                index=index,
                input=item,
                status=result.status,
                result=result.result,
                message=result.message,
                clipboard_ready=result.clipboard_ready,
            )
        )

    error_count = len(item_results) - success_count
    if error_count == 0:
        overall_status = "success"
    elif success_count == 0:
        overall_status = "error"
    else:
        overall_status = "partial_success"

    combined_result = "\n".join(
        item.result for item in item_results if item.status == "success" and item.result is not None
    )
    response = BulkTransformResponse(
        status=overall_status,
        method=payload.method,
        operation=operation,
        clipboard_ready=bool(combined_result),
        combined_result=combined_result or None,
        summary=BulkSummaryResponse(
            total=len(item_results),
            success_count=success_count,
            error_count=error_count,
        ),
        results=item_results,
    )
    return response


def run() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
