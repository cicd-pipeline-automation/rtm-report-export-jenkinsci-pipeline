#!/usr/bin/env python3
"""
RTM Report Generator – HTML & PDF (Production-Ready)
----------------------------------------------------
Reads normalized RTM JSON (from fetch_rtm_data.py) and produces:
  - HTML report (upload to Confluence)
  - PDF report  (email attachment)

Windows-safe (no emojis/box-drawing), UTF-8 aware, Unicode-capable PDF.
"""

import os
import sys
import json
import html
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from fpdf import FPDF
from tabulate import tabulate

# -----------------------------
# Paths & constants
# -----------------------------
DATA_FILE = Path("data/rtm_data.json")
REPORT_DIR = Path("report")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Timestamped outputs + stable "latest" links
ts = datetime.now().strftime("%Y%m%d-%H%M%S")
HTML_FILE = REPORT_DIR / f"rtm_report_{ts}.html"
PDF_FILE = REPORT_DIR / f"rtm_report_{ts}.pdf"
HTML_LATEST = REPORT_DIR / "rtm_report.html"
PDF_LATEST = REPORT_DIR / "rtm_report.pdf"
LOG_FILE = REPORT_DIR / "report_generation_log.txt"

# Optional project metadata via env
PROJECT_KEY = os.getenv("RTM_PROJECT", "")
TEST_EXEC = os.getenv("TEST_EXECUTION", "")
REPORT_TITLE = os.getenv("REPORT_TITLE", "RTM Test Execution Report")

# Unicode TTF font (recommended). Commit this to your repo.
FONT_PATH = Path("fonts/DejaVuSans.ttf")

# -----------------------------
# Logging
# -----------------------------
def log(msg: str, level: str = "INFO") -> None:
    ts_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{level}] {ts_now} | {msg}"
    # Console
    try:
        print(line)
    except UnicodeEncodeError:
        # In case the console is not UTF-8, replace non-encodable chars
        print(line.encode("cp1252", errors="replace").decode("cp1252"))
    # File
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# -----------------------------
# Input validation
# -----------------------------
if not DATA_FILE.exists():
    log(f"Missing input file: {DATA_FILE}", "ERROR")
    sys.exit(1)

try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
except json.JSONDecodeError as e:
    log(f"Invalid JSON in {DATA_FILE}: {e}", "ERROR")
    sys.exit(2)

issues: List[Dict[str, Any]] = data.get("issues", [])
if not issues:
    log("No issues in dataset; aborting.", "ERROR")
    sys.exit(3)

# -----------------------------
# Summaries
# -----------------------------
status_summary: Dict[str, int] = {}
for issue in issues:
    s = (issue.get("status") or "Unknown")
    status_summary[s] = status_summary.get(s, 0) + 1

log(f"Loaded {len(issues)} issues. Status breakdown: {status_summary}")

# -----------------------------
# HTML report
# -----------------------------
def generate_html() -> None:
    log("Generating HTML report...")
    rows = []
    for i in issues:
        rows.append([
            i.get("key", ""),
            i.get("summary", "") or "",
            i.get("type", "") or "",
            i.get("priority", "") or "",
            i.get("assignee", "") or "Unassigned",
            i.get("status", "") or "",
        ])

    html_table = tabulate(
        rows,
        headers=["Key", "Summary", "Type", "Priority", "Assignee", "Status"],
        tablefmt="html"
    )

    # Escape the dict preview to avoid HTML injection in the “Status Breakdown”
    status_preview = html.escape(json.dumps(status_summary, ensure_ascii=False))

    top_meta = []
    if PROJECT_KEY:
        top_meta.append(f"<b>Project:</b> {html.escape(PROJECT_KEY)}")
    if TEST_EXEC:
        top_meta.append(f"<b>Execution:</b> {html.escape(TEST_EXEC)}")
    top_meta.append(f"<b>Generated On:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    top_meta.append(f"<b>Total Issues:</b> {len(issues)}")
    meta_html = "<br>".join(top_meta)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(REPORT_TITLE)}</title>
<style>
  body {{
    font-family: Arial, sans-serif;
    margin: 18px;
    color: #333;
  }}
  h1 {{
    color: #174c7e;
    border-bottom: 2px solid #174c7e;
    padding-bottom: 8px;
    margin-bottom: 16px;
  }}
  .summary {{
    background: #f7f9fc;
    border: 1px solid #e3eaf3;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 18px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  th, td {{
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background: #174c7e;
    color: #fff;
  }}
  tr:nth-child(even) {{ background: #fafafa; }}
  code {{
    background: #f1f1f1;
    padding: 2px 4px;
    border-radius: 4px;
  }}
</style>
</head>
<body>
  <h1>{html.escape(REPORT_TITLE)}</h1>
  <div class="summary">
    {meta_html}<br>
    <b>Status Breakdown:</b> <code>{status_preview}</code>
  </div>
  {html_table}
</body>
</html>
"""
    HTML_FILE.write_text(html_doc, encoding="utf-8")
    # Maintain stable "latest" copy
    HTML_LATEST.write_text(html_doc, encoding="utf-8")
    log(f"HTML written → {HTML_FILE.name} (and {HTML_LATEST.name})")

# -----------------------------
# PDF report
# -----------------------------
class RTMReportPDF(FPDF):
    def __init__(self, use_unicode_font: bool = False):
        super().__init__()
        self.use_unicode_font = use_unicode_font
        if self.use_unicode_font:
            # Register TTF for full Unicode support
            self.add_font("DejaVu", "", str(FONT_PATH), uni=True)
            self.add_font("DejaVu", "B", str(FONT_PATH), uni=True)
        self.set_auto_page_break(auto=True, margin=15)

    def safe_set_font(self, style: str = "", size: int = 10):
        if self.use_unicode_font:
            self.set_font("DejaVu", style, size)
        else:
            # Core font fallback (Latin-1 only)
            self.set_font("Arial", style, size)

    def header(self):
        self.safe_set_font("B", 14)
        self.cell(0, 8, REPORT_TITLE, ln=True, align="C")
        self.ln(2)
        self.safe_set_font("", 9)
        meta = []
        if PROJECT_KEY:
            meta.append(f"Project: {PROJECT_KEY}")
        if TEST_EXEC:
            meta.append(f"Execution: {TEST_EXEC}")
        meta.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.cell(0, 6, " | ".join(meta), ln=True, align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.safe_set_font("I", 8)
        self.cell(0, 8, f"Page {self.page_no()}", 0, 0, "C")

def truncate_for_latin1(text: str) -> str:
    """If TTF not available, core fonts only support Latin-1: replace others."""
    if text is None:
        return ""
    try:
        text.encode("latin-1")
        return text
    except UnicodeEncodeError:
        return text.encode("latin-1", errors="replace").decode("latin-1")

def pdf_multicell_row(pdf: RTMReportPDF, col_widths: List[int], values: List[str], border: int = 1, line_height: float = 6.0):
    """
    Draw a table row with wrapped text (multi_cell) per column while keeping borders aligned.
    """
    # Calculate max number of lines among cells
    pdf.safe_set_font("", 9)
    x_start = pdf.get_x()
    y_start = pdf.get_y()

    # First pass: compute heights
    line_counts = []
    for i, v in enumerate(values):
        v = v if isinstance(v, str) else str(v or "")
        # Temporarily write to get number of lines
        x = pdf.get_x(); y = pdf.get_y()
        pdf.multi_cell(col_widths[i], line_height, v, 0)
        line_count = int((pdf.get_y() - y) // line_height) or 1
        line_counts.append(line_count)
        pdf.set_xy(x + col_widths[i], y)

    row_height = max(line_counts) * line_height

    # Second pass: draw the bordered cells
    pdf.set_xy(x_start, y_start)
    for i, v in enumerate(values):
        x = pdf.get_x(); y = pdf.get_y()
        # Cell border rectangle
        pdf.rect(x, y, col_widths[i], row_height)
        # Text
        pdf.multi_cell(col_widths[i], line_height, v, 0)
        pdf.set_xy(x + col_widths[i], y)
    pdf.ln(row_height)

def generate_pdf() -> None:
    log("Generating PDF report...")
    use_unicode = FONT_PATH.exists()
    if use_unicode:
        log(f"Using Unicode font: {FONT_PATH}")
    else:
        log("Unicode font not found, falling back to core fonts (non-ASCII will be replaced).", "WARN")

    pdf = RTMReportPDF(use_unicode_font=use_unicode)
    pdf.add_page()

    # Summary header
    pdf.safe_set_font("B", 10)
    pdf.cell(0, 6, f"Total Issues: {len(issues)}", ln=True)
    pdf.cell(0, 6, f"Status Breakdown: {json.dumps(status_summary, ensure_ascii=not use_unicode)}", ln=True)
    pdf.ln(3)

    # Table header
    headers = ["Key", "Summary", "Type", "Priority", "Assignee", "Status"]
    col_widths = [22, 90, 22, 22, 32, 22]  # total ~210mm for A4 landscape? We'll keep portrait; adjust widths to fit.
    # If width overflows the page, reduce slightly
    if sum(col_widths) > 190:
        scale = 190.0 / sum(col_widths)
        col_widths = [int(w * scale) for w in col_widths]

    pdf.safe_set_font("B", 10)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, 1, 0, "C")
    pdf.ln()

    # Table rows
    pdf.safe_set_font("", 9)
    for i in issues:
        row = [
            i.get("key", "") or "",
            i.get("summary", "") or "",
            i.get("type", "") or "",
            i.get("priority", "") or "",
            i.get("assignee", "") or "Unassigned",
            i.get("status", "") or "",
        ]
        if not use_unicode:
            row = [truncate_for_latin1(v) for v in row]
        pdf_multicell_row(pdf, col_widths, row, line_height=5.5)

    pdf.output(str(PDF_FILE))
    # Maintain stable "latest" copy
    try:
        PDF_LATEST.write_bytes(PDF_FILE.read_bytes())
    except Exception as e:
        log(f"Could not write stable latest PDF: {e}", "WARN")

    log(f"PDF written → {PDF_FILE.name} (and {PDF_LATEST.name})")

# -----------------------------
# Main
# -----------------------------
def main() -> int:
    log("Starting RTM report generation...")
    try:
        generate_html()
        generate_pdf()
        log("Report generation complete.")
        print("[OK] RTM HTML and PDF generated.")
        return 0
    except Exception as e:
        log(f"Report generation failed: {e}", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
