from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app import api

app = FastAPI(title="API de Tarefas")
app.include_router(api.router)

_MESSAGES = {
    "not_found": "Recurso não encontrado",
    "method_not_allowed": "Método não permitido",
    "internal_error": "Erro interno",
}


def _error(status: int, code: str, field: str | None, headers=None) -> JSONResponse:
    if code == "validation_error":
        message = (
            f"Campo inválido: {field}" if field else "Corpo da requisição inválido"
        )
    elif code == "not_found" and field == "id":
        message = "Tarefa não encontrada"
    else:
        message = _MESSAGES[code]
    return JSONResponse(
        {"error": {"code": code, "field": field, "message": message}},
        status_code=status,
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
def _validation(request: Request, exc: RequestValidationError) -> JSONResponse:
    loc = exc.errors()[0]["loc"][1:]
    return _error(422, "validation_error", ".".join(str(p) for p in loc) or None)


@app.exception_handler(HTTPException)
def _http(request: Request, exc: HTTPException) -> JSONResponse:
    if exc.status_code == 405:
        return _error(405, "method_not_allowed", None, exc.headers)
    if exc.status_code == 404:
        field = "id" if exc.detail == "task_not_found" else None
        return _error(404, "not_found", field, exc.headers)
    # ponytail: só 404/405 sobem do roteamento hoje; outros status viram 500.
    return _error(500, "internal_error", None)


@app.exception_handler(Exception)
def _internal(request: Request, exc: Exception) -> JSONResponse:
    return _error(500, "internal_error", None)
