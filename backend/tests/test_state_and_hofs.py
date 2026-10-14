from app.domain.shared.functions import (
    all_match,
    any_match,
    count_where,
    group_by,
    pipe,
    sort_by,
    sum_by,
    unique_by,
)
from app.domain.shared.state_machine import StateMachine, Transition

# --- máquina de estados de ejemplo (ventas -> desarrollo -> despacho) ---
FLOW = StateMachine(
    initial="levantamiento",
    transitions=(
        Transition("levantamiento", "cobrado_50", "cobrar_50"),
        Transition("levantamiento", "cobrado_100", "cobrar_100"),
        Transition("cobrado_50", "enviado_desarrollo", "pasar"),
        Transition("cobrado_100", "enviado_desarrollo", "pasar"),
        Transition("enviado_desarrollo", "en_desarrollo", "iniciar"),
        Transition("en_desarrollo", "completado", "completar"),
        Transition("completado", "entregado", "entregar"),
    ),
)


def test_transicion_valida():
    assert FLOW.next("levantamiento", "cobrado_50").unwrap() == "cobrado_50"


def test_transicion_invalida():
    r = FLOW.next("levantamiento", "entregado")
    assert not r.is_ok()
    assert r.error.code == "state.invalid_transition"


def test_no_permite_retroceder():
    assert not FLOW.can_transition("completado", "levantamiento")


def test_allowed_targets():
    assert FLOW.allowed_targets("levantamiento") == ("cobrado_50", "cobrado_100")


# --- HOFs ---


def test_sum_by():
    pagos = [{"monto": 100}, {"monto": 50}, {"monto": 25}]
    assert sum_by(lambda p: p["monto"])(pagos) == 175


def test_count_where():
    proys = [{"estado": "x"}, {"estado": "y"}, {"estado": "x"}]
    assert count_where(lambda p: p["estado"] == "x")(proys) == 2


def test_group_by():
    proys = [{"dep": "v"}, {"dep": "d"}, {"dep": "v"}]
    grouped = group_by(lambda p: p["dep"])(proys)
    assert len(grouped["v"]) == 2
    assert len(grouped["d"]) == 1


def test_sort_by_no_muta():
    xs = [3, 1, 2]
    sorted_xs = sort_by(lambda x: x)(xs)
    assert sorted_xs == [1, 2, 3]
    assert xs == [3, 1, 2]  # original intacta


def test_unique_by():
    assert unique_by(lambda x: x["id"])([{"id": 1}, {"id": 1}, {"id": 2}]) == [
        {"id": 1},
        {"id": 2},
    ]


def test_all_any():
    assert all_match(lambda x: x > 0)([1, 2, 3])
    assert not all_match(lambda x: x > 0)([1, -1])
    assert any_match(lambda x: x < 0)([1, -1])


def test_pipe():
    f = pipe(lambda x: x + 1, lambda x: x * 2)
    assert f(3) == 8
