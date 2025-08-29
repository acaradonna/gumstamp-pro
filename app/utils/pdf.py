from pathlib import Path
from typing import Optional
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
import io


def _footer_overlay(page_width: float, page_height: float, text: str) -> bytes:
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    can.setFont("Helvetica", 9)
    can.setFillColor(Color(0, 0, 0, alpha=0.8))
    margin = 24
    can.drawRightString(page_width - margin, margin, text)
    can.save()
    packet.seek(0)
    return packet.read()


def _diagonal_overlay(page_width: float, page_height: float, text: str) -> bytes:
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    can.setFont("Helvetica", 36)
    can.setFillColor(Color(0.2, 0.2, 0.2, alpha=0.15))
    can.saveState()
    can.translate(page_width / 2, page_height / 2)
    can.rotate(45)
    can.drawCentredString(0, 0, text)
    can.restoreState()
    can.save()
    packet.seek(0)
    return packet.read()


def stamp_pdf(input_path: Path, output_path: Path, footer_text: Optional[str], diagonal_text: Optional[str]) -> None:
    reader = PdfReader(str(input_path))
    writer = PdfWriter()

    for page in reader.pages:
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)

        overlays = []
        if footer_text:
            overlays.append(_footer_overlay(page_width, page_height, footer_text))
        if diagonal_text:
            overlays.append(_diagonal_overlay(page_width, page_height, diagonal_text))

        if overlays:
            # Merge overlay(s) with page one by one
            base = page
            for o in overlays:
                overlay_reader = PdfReader(io.BytesIO(o))
                base.merge_page(overlay_reader.pages[0])
            writer.add_page(base)
        else:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
