"""Agregado Project: el expediente central que transita por departamentos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.project.states import EstadoDesarrollo, EstadoDespacho, EstadoVentas
from app.domain.shared.money import Money


@dataclass(frozen=True, slots=True)
class Project:
    id: str
    codigo: str
    titulo: str
    descripcion_detallada: str
    customer_id: str
    monto_total: Money
    # snapshot de contacto para Despacho (no depende de joins)
    contacto_nombre: str
    contacto_telefono: str | None
    contacto_email: str | None
    contacto_direccion: str | None
    estado_ventas: str
    estado_desarrollo: str
    estado_despacho: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def new_state_fields(cls) -> dict[str, str]:
        return {
            "estado_ventas": EstadoVentas.LEVANTAMIENTO.value,
            "estado_desarrollo": EstadoDesarrollo.PENDIENTE.value,
            "estado_despacho": EstadoDespacho.PENDIENTE.value,
        }
