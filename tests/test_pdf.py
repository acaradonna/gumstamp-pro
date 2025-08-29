from pathlib import Path
from app.utils.pdf import stamp_pdf
from reportlab.pdfgen import canvas
import io


def _make_pdf(tmp_path: Path) -> Path:
    p = tmp_path / "in.pdf"
    packet = io.BytesIO()
    can = canvas.Canvas(packet)
    can.drawString(100, 750, "Hello PDF")
    can.save()
    packet.seek(0)
    p.write_bytes(packet.read())
    return p


def test_stamp_pdf(tmp_path: Path):
    inp = _make_pdf(tmp_path)
    out = tmp_path / "out.pdf"
    stamp_pdf(inp, out, footer_text="Purchased by test@example.com", diagonal_text="TEST")
    assert out.exists()
    assert out.stat().st_size > 0
