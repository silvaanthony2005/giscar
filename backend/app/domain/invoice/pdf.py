"""Generación de PDF de factura con reportlab. Devuelve bytes (sin I/O de disco)."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.domain.invoice.model import Invoice

BRAND = colors.HexColor("#1d4ed8")
INK = colors.HexColor("#0f172a")
MUTED = colors.HexColor("#64748b")


def invoice_pdf(invoice: Invoice) -> bytes:
    """Genera el PDF de la factura y lo devuelve como bytes (función pura)."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Encabezado
    c.setFillColor(BRAND)
    c.rect(0, height - 28 * mm, width, 28 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20 * mm, height - 17 * mm, "GCISCAR")
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, height - 24 * mm, "Factura de cobro")

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 20 * mm, height - 15 * mm, f"No. {invoice.numero}")

    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawRightString(width - 20 * mm, height - 21 * mm, invoice.emitida_en.strftime("%d/%m/%Y %H:%M"))

    # Datos del cliente / proyecto
    y = height - 42 * mm
    s = invoice.snapshot
    rows = [
        ("Cliente", s.cliente_nombre),
        ("Proyecto", f"{s.project_codigo} — {s.project_titulo}"),
        ("Método de pago", invoice.metodo_pago),
        ("Porcentaje", f"{invoice.porcentaje}% del total"),
        ("Total del proyecto", f"{s.monto_total.amount}"),
    ]
    c.setFillColor(INK)
    for label, value in rows:
        c.setFont("Helvetica", 9)
        c.setFillColor(MUTED)
        c.drawString(20 * mm, y, label)
        c.setFont("Helvetica", 10)
        c.setFillColor(INK)
        c.drawString(55 * mm, y, str(value))
        y -= 6 * mm

    # Monto cobrado (destacado)
    y -= 6 * mm
    c.setFillColor(BRAND)
    c.roundRect(20 * mm, y - 6 * mm, width - 40 * mm, 14 * mm, 3, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(25 * mm, y, "Monto cobrado")
    c.drawRightString(width - 25 * mm, y, f"{invoice.monto.amount}")

    # Levantamiento (detalle del producto)
    y -= 22 * mm
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Detalles del levantamiento")
    y -= 7 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    for line in _wrap(s.project_descripcion, 95)[:24]:
        c.drawString(20 * mm, y, line)
        y -= 4.5 * mm

    # Pie
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, 15 * mm, "Documento de registro interno — GCISCAR")
    c.drawRightString(width - 20 * mm, 15 * mm, f"Emitida por: {invoice.emitida_por}")

    c.showPage()
    c.save()
    return buffer.getvalue()


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width:
            if current:
                lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines
