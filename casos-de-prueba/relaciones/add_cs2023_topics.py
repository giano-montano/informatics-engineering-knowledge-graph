"""Adds to the CP-15 sheet the topics of each CS2023 knowledge unit, copied from the document.

The graph has only the name of each unit; the CP-15 criterion asks for its topics, which are
in the CS2023 report (Kumar et al., 2024). This copies, for every row, the unit's topic list
(CS Core, KA Core and Non-core, up to its illustrative learning outcomes) from the text of the
PDF, so the judgment can be made on the sheet. It only reads the document: it judges nothing.

    pdftotext -layout "data/Kumar et al. - 2024 - Computer Science Curricula 2023.pdf" cs2023.txt
    uv run python casos-de-prueba/relaciones/add_cs2023_topics.py cs2023.txt \
        casos-de-prueba/relaciones/juicio-de-relaciones-semilla-20261116.xlsx
"""

import argparse
import re
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font

COLUMN = "tópicos de la unidad (CS2023)"
UNIT_COLUMN = "unidad"
END = re.compile(r"^\s*Illustrative learning outcomes", re.IGNORECASE)
NEXT_UNIT = re.compile(r"^[A-Z]+-[A-Za-z-]+: [A-Z]")
PAGE_NUMBER = re.compile(r"^\s*\d+\s*$")


def unit_topics(text: str, code: str) -> str:
    """The topic list of ``code`` (e.g. ``AL-Foundational``), as printed in the report."""
    lines = text.replace("\f", "\n").splitlines()
    heading = re.compile(rf"^{re.escape(code)}: (?!.*\.\.\.\.)")
    starts = [i for i, line in enumerate(lines) if heading.match(line)]
    if len(starts) != 1:
        raise SystemExit(f"{code}: expected one heading in the report, found {len(starts)}")
    kept = []
    for line in lines[starts[0] + 1:]:
        if END.match(line) or NEXT_UNIT.match(line):
            break
        if line.strip() and not PAGE_NUMBER.match(line):
            kept.append(line.rstrip())
    return "\n".join(kept)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report_text", type=Path, help="pdftotext -layout output of the CS2023 report")
    parser.add_argument("workbook", type=Path, help="the judgment workbook; its CP-15 sheet gets one more column")
    arguments = parser.parse_args()
    text = arguments.report_text.read_text(encoding="utf-8")
    book = load_workbook(arguments.workbook)
    page = book["CP-15"]
    header = [cell.value for cell in page[2]]
    if COLUMN in header:
        raise SystemExit(f"the CP-15 sheet already has the column {COLUMN!r}")
    unit = header.index(UNIT_COLUMN)
    target = len(header) + 1
    page.cell(row=2, column=target, value=COLUMN).font = Font(bold=True)
    topics = {}
    for row in page.iter_rows(min_row=3):
        code = row[unit].value.removeprefix("KU-")
        topics.setdefault(code, unit_topics(text, code))
        cell = page.cell(row=row[0].row, column=target, value=topics[code])
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    page.column_dimensions[page.cell(row=2, column=target).column_letter].width = 80
    book.save(arguments.workbook)
    print(f"{page.max_row - 2} rows, {len(topics)} units")


if __name__ == "__main__":
    main()
