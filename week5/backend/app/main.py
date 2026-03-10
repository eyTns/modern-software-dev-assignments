from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import apply_seed_if_needed, engine
from .models import Base
from .routers import action_items as action_items_router
from .routers import notes as notes_router
from .schemas import ErrorDetail, ErrorResponse

app = FastAPI(title="Modern Software Dev Starter (Week 5)")


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent error envelope"""
    error_code_map = {
        404: "NOT_FOUND",
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
    }
    code = error_code_map.get(exc.status_code, "ERROR")
    error_response = ErrorResponse(error=ErrorDetail(code=code, message=str(exc.detail)))
    return JSONResponse(status_code=exc.status_code, content=error_response.model_dump())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with consistent error envelope"""
    errors = exc.errors()
    # Format validation errors into a readable message
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(loc_part) for loc_part in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{loc}: {msg}")

    error_response = ErrorResponse(
        error=ErrorDetail(code="VALIDATION_ERROR", message="; ".join(error_messages))
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with consistent error envelope"""
    error_response = ErrorResponse(
        error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred")
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


# Ensure data dir exists
Path("data").mkdir(parents=True, exist_ok=True)

# Mount static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)
    apply_seed_if_needed()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("frontend/index.html")


# Routers
app.include_router(notes_router.router)
app.include_router(action_items_router.router)
