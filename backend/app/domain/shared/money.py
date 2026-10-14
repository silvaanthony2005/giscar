"""Valor monetario inmutable en centavos para evitar errores de punto flotante."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.domain.shared.types import DomainError, Err, Ok, Result


@dataclass(frozen=True, slots=True)
class Money:
    """Cantidad en centavos (entero). 10.50 DOP == Money(1050)."""

    cents: int

    def __post_init__(self) -> None:
        if self.cents < 0:
            raise ValueError("Money no puede ser negativo")

    @classmethod
    def from_amount(cls, amount: Decimal | int | float | str) -> Money:
        d = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return cls(cents=int(d * 100))

    @property
    def amount(self) -> Decimal:
        return (Decimal(self.cents) / Decimal(100)).quantize(Decimal("0.01"))

    def plus(self, other: Money) -> Money:
        return Money(self.cents + other.cents)

    def minus(self, other: Money) -> Money:
        if other.cents > self.cents:
            raise ValueError("Money negativo resultante")
        return Money(self.cents - other.cents)

    def percent(self, pct: int | float) -> Money:
        d = (Decimal(self.cents) * Decimal(str(pct)) / Decimal(100)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        return Money(int(d))

    def __str__(self) -> str:
        return f"{self.amount}"


ZERO = Money(0)


def parse_money(raw: str) -> Result[Money, DomainError]:
    try:
        return Ok(Money.from_amount(raw))
    except Exception:
        return Err(DomainError("money.invalido", "Monto inválido"))
