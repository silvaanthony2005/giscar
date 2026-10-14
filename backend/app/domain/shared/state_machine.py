"""Motor genérico de transiciones de estado. Puro y reutilizable por módulos.

Define un grafo de estados y transiciones; las aplica de forma inmutable y
devuelve `Result` en vez de lanzar excepciones.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Generic, TypeVar

from app.domain.shared.types import DomainError, Err, Ok, Result

S = TypeVar("S")  # tipo de estado (str normalmente)
T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Transition(Generic[S]):
    source: S
    target: S
    name: str


@dataclass(frozen=True, slots=True)
class StateMachine(Generic[S]):
    initial: S
    transitions: tuple[Transition[S], ...]

    def allowed_targets(self, state: S) -> tuple[S, ...]:
        return tuple(t.target for t in self.transitions if t.source == state)

    def can_transition(self, state: S, target: S) -> bool:
        return target in self.allowed_targets(state)

    def next(self, state: S, target: S) -> Result[S, DomainError]:
        if not self.can_transition(state, target):
            return Err(
                DomainError(
                    "state.invalid_transition",
                    f"Transición no permitida: {state} → {target}",
                )
            )
        return Ok(target)


def transition_field(
    sm: StateMachine[str],
    get_state: Callable[[T], str],
    set_state: Callable[[T, str], T],
) -> Callable[[T, str], Result[T, DomainError]]:
    """Devuelve una función pura que transiciona un objeto inmutable.

    `get_state`/`set_state` construyen el setter con `dataclasses.replace`.
    """

    def go(obj: T, target: str) -> Result[T, DomainError]:
        result = sm.next(get_state(obj), target)
        if not result.is_ok():
            return result  # type: ignore[return-value]
        return Ok(set_state(obj, result.unwrap()))

    return go


def with_replace(**changes: object) -> Callable[[object], object]:
    """Helper parcial: `with_replace(estado='x')(obj)` -> replace(obj, estado='x')."""

    def apply(obj: object) -> object:
        return replace(obj, **changes)  # type: ignore[arg-type]

    return apply
