"""Repositorios de Despacho e Incidencias."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.dispatch.model import Denial, Dispatch
from app.domain.incidence.model import Incidence, IncidentReport
from app.infrastructure.db.mappers_despacho import (
    apply_dispatch,
    apply_incidence,
    denial_to_domain,
    dispatch_to_domain,
    incident_to_domain,
    report_to_domain,
)
from app.infrastructure.db.models_despacho import (
    DenialRow,
    DispatchRow,
    IncidentReportRow,
    IncidentRow,
)


class DispatchRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_project(self, project_id: str) -> Dispatch | None:
        stmt = select(DispatchRow).where(DispatchRow.project_id == project_id)
        row = self._db.execute(stmt).scalar_one_or_none()
        return dispatch_to_domain(row) if row else None

    def add(self, d: Dispatch) -> Dispatch:
        row = DispatchRow(id=d.id, project_id=d.project_id)
        apply_dispatch(d, row)
        self._db.add(row)
        self._db.flush()
        return d

    def update(self, d: Dispatch) -> Dispatch:
        row = self._db.get(DispatchRow, d.id)
        if row is None:
            raise KeyError(d.id)
        apply_dispatch(d, row)
        self._db.flush()
        return d


class DenialRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_project(self, project_id: str) -> Denial | None:
        stmt = select(DenialRow).where(DenialRow.project_id == project_id)
        row = self._db.execute(stmt).scalar_one_or_none()
        return denial_to_domain(row) if row else None

    def add(self, d: Denial) -> Denial:
        row = DenialRow(
            id=d.id, project_id=d.project_id, motivo=d.motivo, detalle=d.detalle,
            registrado_por=d.registrado_por, fecha=d.fecha,
        )
        self._db.add(row)
        self._db.flush()
        return d


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, iid: str) -> Incidence | None:
        row = self._db.get(IncidentRow, iid)
        return incident_to_domain(row) if row else None

    def get_by_codigo(self, codigo: str) -> Incidence | None:
        stmt = select(IncidentRow).where(IncidentRow.codigo == codigo)
        row = self._db.execute(stmt).scalar_one_or_none()
        return incident_to_domain(row) if row else None

    def list_all(self) -> list[Incidence]:
        rows = self._db.execute(select(IncidentRow)).scalars().all()
        return [incident_to_domain(r) for r in rows]

    def next_orden(self) -> int:
        stmt = select(func.coalesce(func.max(IncidentRow.orden_llegada), 0))
        return int(self._db.execute(stmt).scalar_one()) + 1

    def codigo_exists(self, codigo: str) -> bool:
        return self.get_by_codigo(codigo) is not None

    def add(self, i: Incidence) -> Incidence:
        row = IncidentRow(id=i.id, codigo=i.codigo)
        apply_incidence(i, row)
        row.orden_llegada = i.orden_llegada
        row.reportado_por = i.reportado_por
        row.created_at = i.created_at
        self._db.add(row)
        self._db.flush()
        return i

    def update(self, i: Incidence) -> Incidence:
        row = self._db.get(IncidentRow, i.id)
        if row is None:
            raise KeyError(i.id)
        apply_incidence(i, row)
        self._db.flush()
        return i


class IncidentReportRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_incident(self, incident_id: str) -> list[IncidentReport]:
        stmt = (
            select(IncidentReportRow)
            .where(IncidentReportRow.incident_id == incident_id)
            .order_by(IncidentReportRow.fecha)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [report_to_domain(r) for r in rows]

    def add(self, rep: IncidentReport) -> IncidentReport:
        row = IncidentReportRow(
            id=rep.id, incident_id=rep.incident_id, diagnostico=rep.diagnostico,
            solucion=rep.solucion, tiempo_resolucion_horas=rep.tiempo_resolucion_horas,
            resuelto_por=rep.resuelto_por, fecha=rep.fecha,
        )
        self._db.add(row)
        self._db.flush()
        return rep
