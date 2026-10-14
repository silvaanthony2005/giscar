from app.domain.shared.types import Err, Ok, and_then, collect, map_result, partition, unwrap_or


def test_ok_map_applies():
    assert map_result(Ok(2), lambda x: x * 3) == Ok(6)


def test_err_map_propagates():
    assert map_result(Err("e"), lambda x: x * 3) == Err("e")


def test_and_then_chains():
    def half(x):
        return Ok(x // 2) if x % 2 == 0 else Err("impar")

    assert and_then(Ok(4), half) == Ok(2)
    assert and_then(Ok(3), half) == Err("impar")


def test_unwrap_or():
    assert unwrap_or(Ok(1), 9) == 1
    assert unwrap_or(Err("e"), 9) == 9


def test_collect_short_circuits_on_first_err():
    assert collect([Ok(1), Ok(2)]) == Ok((1, 2))
    assert collect([Ok(1), Err("a"), Err("b")]) == Err("a")


def test_partition_splits():
    oks, errs = partition([Ok(1), Err("a"), Ok(2), Err("b")])
    assert oks == [1, 2]
    assert errs == ["a", "b"]
