"""Tipos de dominio compartidos: Result, errores y valores inmutables.

Todo aquí es puro (stdlib únicamente). El dominio devuelve `Result` en lugar de
lanzar excepciones para errores de negocio esperados.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True

    def unwrap(self) -> T:
        return self.value

    def map(self, f: Callable[[T], U]) -> Result[U, E]:
        return Ok(f(self.value))


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E

    def is_ok(self) -> bool:
        return False

    def unwrap(self) -> T:
        raise UnwrapError(self.error)

    def map(self, f: Callable[[T], U]) -> Result[U, E]:
        return Err(self.error)


Result = Union[Ok[T], Err[E]]


class UnwrapError(Exception):
    """Solo para errores de programación (unwrap en un Err). No usar en negocio."""


# --- Manejo funcional de Result -------------------------------------------


def map_result(r: Result[T, E], f: Callable[[T], U]) -> Result[U, E]:
    """Aplica `f` al valor si es Ok, si no propaga el Err."""
    return r.map(f) if r.is_ok() else r  # type: ignore[arg-type]


def and_then(r: Result[T, E], f: Callable[[T], Result[U, E]]) -> Result[U, E]:
    """Encadena una función que también devuelve Result (monadic bind)."""
    return f(r.unwrap()) if r.is_ok() else r  # type: ignore[arg-type]


def unwrap_or(r: Result[T, E], default: T) -> T:
    return r.unwrap() if r.is_ok() else default


def collect(results: list[Result[T, E]]) -> Result[tuple[T, ...], E]:
    """Agrupa muchos Result: Ok con todos los valores, o el primer Err."""
    values: list[T] = []
    for r in results:
        if not r.is_ok():
            return r  # type: ignore[return-value]
        values.append(r.unwrap())  # type: ignore[arg-type]
    return Ok(tuple(values))


def partition(results: list[Result[T, E]]) -> tuple[list[T], list[E]]:
    """Separa Oks y Errs sin cortocircuitar. Útil para validaciones en lote."""
    oks = [r.unwrap() for r in results if r.is_ok()]
    errs = [r.error for r in results if not r.is_ok()]  # type: ignore[union-attr]
    return oks, errs


# --- Errores de negocio -----------------------------------------------------


@dataclass(frozen=True, slots=True)
class DomainError:
    code: str
    message: str


def error(code: str, message: str) -> Err[DomainError]:
    return Err(DomainError(code=code, message=message))
