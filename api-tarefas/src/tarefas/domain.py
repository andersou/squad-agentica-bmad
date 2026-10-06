from dataclasses import dataclass
from datetime import date


@dataclass
class Tarefa:
    id: int
    titulo: str
    prazo: date
    tags: list[str]
    concluida: bool


def norm_tag(s: str) -> str:
    return s.strip().casefold()


def normalizar_tags(lista: list[str]) -> list[str]:
    tags, vistas = [], set()
    for tag in lista:
        tag = tag.strip()
        if not tag:
            raise ValueError("tag vazia")
        norm = norm_tag(tag)
        if norm not in vistas:
            vistas.add(norm)
            tags.append(tag)
    return tags
