"""Repositorios de Desarrollo y adjuntos."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.attachment.model import Attachment
from app.domain.development.model import (
    Cancellation,
    DevPlan,
    Phase,
    ProgressUpdate,
    ProjectMember,
)
from app.infrastructure.db.mappers_desarrollo import (
    apply_cancellation,
    apply_phase,
    apply_plan,
    attachment_to_domain,
    cancellation_to_domain,
    member_to_domain,
    phase_to_domain,
    plan_to_domain,
    progress_to_domain,
)
from app.infrastructure.db.models_desarrollo import (
    AttachmentRow,
    CancellationRow,
    DevPlanRow,
    PhaseRow,
    ProgressUpdateRow,
    ProjectMemberRow,
)


class PlanRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_project(self, project_id: str) -> DevPlan | None:
        stmt = select(DevPlanRow).where(DevPlanRow.project_id == project_id)
        row = self._db.execute(stmt).scalar_one_or_none()
        return plan_to_domain(row) if row else None

    def add(self, plan: DevPlan) -> DevPlan:
        row = DevPlanRow(id=plan.id, project_id=plan.project_id)
        apply_plan(plan, row)
        self._db.add(row)
        self._db.flush()
        return plan


class PhaseRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_plan(self, plan_id: str) -> list[Phase]:
        stmt = (
            select(PhaseRow)
            .where(PhaseRow.plan_id == plan_id)
            .order_by(PhaseRow.orden)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [phase_to_domain(r) for r in rows]

    def get(self, phase_id: str) -> Phase | None:
        row = self._db.get(PhaseRow, phase_id)
        return phase_to_domain(row) if row else None

    def add(self, phase: Phase) -> Phase:
        row = PhaseRow(id=phase.id, plan_id=phase.plan_id)
        apply_phase(phase, row)
        self._db.add(row)
        self._db.flush()
        return phase

    def update(self, phase: Phase) -> Phase:
        row = self._db.get(PhaseRow, phase.id)
        if row is None:
            raise KeyError(phase.id)
        apply_phase(phase, row)
        self._db.flush()
        return phase


class MemberRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_project(self, project_id: str) -> list[ProjectMember]:
        stmt = select(ProjectMemberRow).where(ProjectMemberRow.project_id == project_id)
        rows = self._db.execute(stmt).scalars().all()
        return [member_to_domain(r) for r in rows]

    def add(self, member: ProjectMember) -> ProjectMember:
        row = ProjectMemberRow(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            rol_proyecto=member.rol_proyecto,
            fecha_asignacion=member.fecha_asignacion,
        )
        self._db.add(row)
        self._db.flush()
        return member


class ProgressRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_project(self, project_id: str) -> list[ProgressUpdate]:
        stmt = (
            select(ProgressUpdateRow)
            .where(ProgressUpdateRow.project_id == project_id)
            .order_by(ProgressUpdateRow.fecha)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [progress_to_domain(r) for r in rows]

    def add(self, progress: ProgressUpdate) -> ProgressUpdate:
        row = ProgressUpdateRow(id=progress.id)
        row.project_id = progress.project_id
        row.phase_id = progress.phase_id
        row.user_id = progress.user_id
        row.porcentaje = progress.porcentaje
        row.notas = progress.notas
        row.fecha = progress.fecha
        self._db.add(row)
        self._db.flush()
        return progress


class CancellationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_project(self, project_id: str) -> Cancellation | None:
        stmt = select(CancellationRow).where(CancellationRow.project_id == project_id)
        row = self._db.execute(stmt).scalar_one_or_none()
        return cancellation_to_domain(row) if row else None

    def add(self, cancellation: Cancellation) -> Cancellation:
        row = CancellationRow(id=cancellation.id, project_id=cancellation.project_id)
        apply_cancellation(cancellation, row)
        self._db.add(row)
        self._db.flush()
        return cancellation


class AttachmentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_entity(self, entidad_tipo: str, entidad_id: str) -> list[Attachment]:
        stmt = (
            select(AttachmentRow)
            .where(
                AttachmentRow.entidad_tipo == entidad_tipo,
                AttachmentRow.entidad_id == entidad_id,
            )
            .order_by(AttachmentRow.fecha)
        )
        rows = self._db.execute(stmt).scalars().all()
        return [attachment_to_domain(r) for r in rows]

    def get(self, attachment_id: str) -> Attachment | None:
        row = self._db.get(AttachmentRow, attachment_id)
        return attachment_to_domain(row) if row else None

    def add(self, att: Attachment) -> Attachment:
        row = AttachmentRow(
            id=att.id,
            entidad_tipo=att.entidad_tipo,
            entidad_id=att.entidad_id,
            nombre=att.nombre,
            ruta=att.ruta,
            mime=att.mime,
            tamano=att.tamano,
            subido_por=att.subido_por,
            fecha=att.fecha,
        )
        self._db.add(row)
        self._db.flush()
        return att
