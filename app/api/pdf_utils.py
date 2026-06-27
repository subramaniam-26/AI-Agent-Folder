"""Small dependency-free PDF writer for farmer reports."""

from __future__ import annotations

import textwrap


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_report_lines(report: str, width: int = 86) -> list[str]:
    lines: list[str] = []
    for raw_line in report.replace("**", "").replace("_", "").splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(raw_line, width=width) or [""])
    return lines


def build_report_pdf(report: str, title: str = "Soil Nutrient Report") -> bytes:
    """Build a simple multi-page PDF from plain report text."""
    page_width = 612
    page_height = 792
    margin_x = 54
    start_y = 738
    line_height = 14
    max_lines_per_page = 48

    body_lines = _wrap_report_lines(report)
    pages = [
        body_lines[index : index + max_lines_per_page]
        for index in range(0, len(body_lines), max_lines_per_page)
    ] or [[]]

    objects: list[bytes] = []

    def add_object(payload: str | bytes) -> int:
        if isinstance(payload, str):
            payload = payload.encode("latin-1", errors="replace")
        objects.append(payload)
        return len(objects)

    font_obj = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_refs: list[int] = []

    for page_number, page_lines in enumerate(pages, start=1):
        text_commands = [
            "BT",
            "/F1 16 Tf",
            f"{margin_x} {start_y} Td",
            f"({_escape_pdf_text(title)}) Tj",
            "0 -24 Td",
            "/F1 10 Tf",
        ]
        for line in page_lines:
            text_commands.append(f"({_escape_pdf_text(line)}) Tj")
            text_commands.append(f"0 -{line_height} Td")
        text_commands.extend(
            [
                "/F1 8 Tf",
                f"{page_width - 110} {-line_height} Td",
                f"(Page {page_number}) Tj",
                "ET",
            ]
        )
        stream = "\n".join(text_commands).encode("latin-1", errors="replace")
        content_obj = add_object(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
        page_obj = add_object(
            "<< /Type /Page /Parent 0 0 R "
            f"/MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        page_refs.append(page_obj)

    kids = " ".join(f"{page_ref} 0 R" for page_ref in page_refs)
    pages_obj = add_object(f"<< /Type /Pages /Kids [{kids}] /Count {len(page_refs)} >>")

    for page_ref in page_refs:
        objects[page_ref - 1] = objects[page_ref - 1].replace(b"/Parent 0 0 R", f"/Parent {pages_obj} 0 R".encode("ascii"))

    catalog_obj = add_object(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, payload in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(payload)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root {catalog_obj} 0 R >>\n"
            "startxref\n"
            f"{xref_start}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)
