from dataclasses import dataclass
from datetime import date


@dataclass
class Tarefa:
    id: int
    titulo: str
    prazo: date
    tags: list[str]
    concluida: bool
