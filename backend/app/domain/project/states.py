"""Estados y máquina de transiciones del agregado Project.

Un solo lugar define el flujo Ventas -> Desarrollo -> Despacho.
"""

from __future__ import annotations

from enum import StrEnum

from app.domain.shared.state_machine import StateMachine, Transition


class EstadoVentas(StrEnum):
    BORRADOR = "borrador"
    LEVANTAMIENTO = "levantamiento"
    COBRADO_50 = "cobrado_50"
    COBRADO_100 = "cobrado_100"
    ENVIADO_DESARROLLO = "enviado_desarrollo"
    CERRADO = "cerrado"


class EstadoDesarrollo(StrEnum):
    PENDIENTE = "pendiente"
    EN_PLANIFICACION = "en_planificacion"
    EN_DESARROLLO = "en_desarrollo"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"
    ENVIADO_DESPACHO = "enviado_despacho"


class EstadoDespacho(StrEnum):
    PENDIENTE = "pendiente"
    PENDIENTE_ENTREGA = "pendiente_entrega"
    ENTREGADO = "entregado"
    NEGADO = "negado"


VENTAS_SM = StateMachine(
    initial=EstadoVentas.LEVANTAMIENTO.value,
    transitions=(
        Transition(EstadoVentas.LEVANTAMIENTO.value, EstadoVentas.COBRADO_50.value, "cobrar_50"),
        Transition(EstadoVentas.LEVANTAMIENTO.value, EstadoVentas.COBRADO_100.value, "cobrar_100"),
        Transition(EstadoVentas.COBRADO_50.value, EstadoVentas.COBRADO_100.value, "cobrar_100"),
        Transition(EstadoVentas.COBRADO_50.value, EstadoVentas.ENVIADO_DESARROLLO.value, "pasar_desarrollo"),
        Transition(EstadoVentas.COBRADO_100.value, EstadoVentas.ENVIADO_DESARROLLO.value, "pasar_desarrollo"),
        # Venta cerrada: Despacho liquidó el saldo restante del proyecto.
        Transition(EstadoVentas.ENVIADO_DESARROLLO.value, EstadoVentas.CERRADO.value, "liquidar"),
    ),
)

DESARROLLO_SM = StateMachine(
    initial=EstadoDesarrollo.PENDIENTE.value,
    transitions=(
        Transition(EstadoDesarrollo.PENDIENTE.value, EstadoDesarrollo.EN_PLANIFICACION.value, "crear_plan"),
        Transition(EstadoDesarrollo.PENDIENTE.value, EstadoDesarrollo.CANCELADO.value, "cancelar"),
        Transition(EstadoDesarrollo.EN_PLANIFICACION.value, EstadoDesarrollo.EN_DESARROLLO.value, "iniciar"),
        Transition(EstadoDesarrollo.EN_DESARROLLO.value, EstadoDesarrollo.COMPLETADO.value, "completar"),
        Transition(EstadoDesarrollo.EN_PLANIFICACION.value, EstadoDesarrollo.CANCELADO.value, "cancelar"),
        Transition(EstadoDesarrollo.EN_DESARROLLO.value, EstadoDesarrollo.CANCELADO.value, "cancelar"),
        Transition(EstadoDesarrollo.COMPLETADO.value, EstadoDesarrollo.ENVIADO_DESPACHO.value, "pasar_despacho"),
    ),
)

DESPACHO_SM = StateMachine(
    initial=EstadoDespacho.PENDIENTE.value,
    transitions=(
        Transition(EstadoDespacho.PENDIENTE.value, EstadoDespacho.PENDIENTE_ENTREGA.value, "recibir"),
        Transition(EstadoDespacho.PENDIENTE_ENTREGA.value, EstadoDespacho.ENTREGADO.value, "entregar"),
        Transition(EstadoDespacho.PENDIENTE_ENTREGA.value, EstadoDespacho.NEGADO.value, "negar"),
        Transition(EstadoDespacho.NEGADO.value, EstadoDespacho.PENDIENTE_ENTREGA.value, "resolver"),
        Transition(EstadoDespacho.NEGADO.value, EstadoDespacho.ENTREGADO.value, "entregar"),
    ),
)
