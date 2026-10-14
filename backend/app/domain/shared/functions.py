"""Funciones de orden superior reutilizables en todo el dominio.

Puras: reciben funciones, devuelven funciones o valores. Sin efectos secundarios.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from functools import reduce
from typing import Any, TypeVar

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")


def pipe(*fns: Callable[..., Any]) -> Callable[..., Any]:
    """Compone funciones de izquierda a derecha: pipe(f, g, h)(x) == h(g(f(x)))."""

    def composed(x: Any) -> Any:
        return reduce(lambda acc, f: f(acc), fns, x)

    return composed


def compose(*fns: Callable[..., Any]) -> Callable[..., Any]:
    """Compone de derecha a izquierda: compose(f, g, h)(x) == f(g(h(x)))."""

    def composed(x: Any) -> Any:
        return reduce(lambda acc, f: f(acc), reversed(fns), x)

    return composed


def curried_map(f: Callable[[A], B]) -> Callable[[Iterable[A]], list[B]]:
    """`curried_map(f)(xs)` — map parcialmente aplicado."""
    return lambda xs: [f(x) for x in xs]


def curried_filter(p: Callable[[A], bool]) -> Callable[[Iterable[A]], list[A]]:
    return lambda xs: [x for x in xs if p(x)]


def curried_reduce(f: Callable[[B, A], B], initial: B) -> Callable[[Iterable[A]], B]:
    return lambda xs: reduce(f, xs, initial)


def sum_by(f: Callable[[A], int | float]) -> Callable[[Iterable[A]], int | float]:
    """Agrega un campo numérico: sum_by(attrgetter('monto'))(pagos)."""
    return lambda xs: sum(map(f, xs))


def count_where(p: Callable[[A], bool]) -> Callable[[Iterable[A]], int]:
    return lambda xs: sum(1 for x in xs if p(x))


def group_by(f: Callable[[A], Any]) -> Callable[[Iterable[A]], dict[Any, list[A]]]:
    """Agrupa elementos por una clave: group_by(lambda p: p.estado)(proyectos)."""

    def grouper(xs: Iterable[A]) -> dict[Any, list[A]]:
        def add(acc: dict[Any, list[A]], x: A) -> dict[Any, list[A]]:
            key = f(x)
            return {**acc, key: [*acc.get(key, []), x]}

        return reduce(add, xs, {})

    return grouper


def find_first(p: Callable[[A], bool]) -> Callable[[Sequence[A]], A | None]:
    return lambda xs: next((x for x in xs if p(x)), None)


def all_match(p: Callable[[A], bool]) -> Callable[[Iterable[A]], bool]:
    return lambda xs: all(p(x) for x in xs)


def any_match(p: Callable[[A], bool]) -> Callable[[Iterable[A]], bool]:
    return lambda xs: any(p(x) for x in xs)


def sort_by(f: Callable[[A], Any], reverse: bool = False) -> Callable[[Sequence[A]], list[A]]:
    """Ordena de forma estable sin mutar la original."""
    return lambda xs: sorted(xs, key=f, reverse=reverse)


def unique_by(f: Callable[[A], Any]) -> Callable[[Iterable[A]], list[A]]:
    """Elimina duplicados preservando el orden de aparición."""

    def go(xs: Iterable[A]) -> list[A]:
        def add(acc: tuple[set[Any], list[A]], x: A) -> tuple[set[Any], list[A]]:
            seen, out = acc
            k = f(x)
            if k in seen:
                return acc
            return (seen | {k}, [*out, x])

        return reduce(add, xs, (set(), []))[1]

    return go


def clamp(lo: int | float, hi: int | float) -> Callable[[int | float], int | float]:
    return lambda v: max(lo, min(hi, v))
