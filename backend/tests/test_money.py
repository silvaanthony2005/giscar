from decimal import Decimal

import pytest

from app.domain.shared.money import ZERO, Money, parse_money


def test_from_amount_centavos():
    assert Money.from_amount("10.50").cents == 1050
    assert Money.from_amount(0.1).cents == 10


def test_plus_minus():
    a = Money.from_amount("50")
    b = Money.from_amount("25")
    assert a.minus(b).cents == 2500
    assert a.plus(b).cents == 7500


def test_minus_negativo_lanza():
    with pytest.raises(ValueError):
        Money.from_amount("10").minus(Money.from_amount("20"))


def test_percent_50():
    assert Money.from_amount("100").percent(50).cents == 5000
    assert Money.from_amount("99.99").percent(50).cents == 5000  # ROUND_HALF_UP


def test_amount_decimal():
    assert Money.from_amount("10.5").amount == Decimal("10.50")


def test_parse_money_invalido():
    assert not parse_money("no-numero").is_ok()
    assert parse_money("10.00").is_ok()


def test_zero():
    assert ZERO.cents == 0
