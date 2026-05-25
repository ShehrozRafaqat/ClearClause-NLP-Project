"""Render REPORT.md as a print-ready PDF.

Uses python-markdown to convert REPORT.md → styled HTML, then weasyprint to
convert HTML → PDF with proper CSS3 support. Output lands at ``REPORT.pdf``
in the repo root.

Run with the project venv:

    /home/shehroz/Documents/genai-course/.venv/bin/python scripts/build_report_pdf.py
"""

from __future__ import annotations

from pathlib import Path

import markdown
from weasyprint import HTML, CSS


HEADER_CSS = """
@page {
  size: A4;
  margin: 22mm 20mm 22mm 20mm;
}

* { box-sizing: border-box; }

html, body {
  font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif;
  font-size: 11pt;
  color: #0f1d18;
  background: #ffffff;
  line-height: 1.55;
  margin: 0;
  padding: 0;
}

main { max-width: 100%; }

h1, h2, h3, h4, h5 {
  font-family: "Liberation Serif", "DejaVu Serif", "Iowan Old Style", serif;
  color: #142a20;
  line-height: 1.25;
  margin-top: 1.4em;
  margin-bottom: 0.45em;
}

h1 {
  font-size: 26pt;
  color: #1f3a2d;
  border-bottom: 3px solid #2f5a40;
  padding-bottom: 0.25em;
  margin-top: 0.4em;
}

h2 {
  font-size: 17pt;
  color: #1f3a2d;
  border-bottom: 1px solid #e3e6dd;
  padding-bottom: 0.2em;
  margin-top: 1.7em;
}

h3 {
  font-size: 13pt;
  color: #2f5a40;
}

h4 { font-size: 11.5pt; color: #2f5a40; }

p { margin: 0.45em 0 0.55em 0; text-align: justify; }

a {
  color: #1f3a2d;
  text-decoration: underline;
}

ul, ol { margin: 0.4em 0 0.6em 1.3em; padding: 0; }
ul li, ol li { margin-bottom: 0.18em; }

code {
  font-family: "Liberation Mono", "DejaVu Sans Mono", monospace;
  font-size: 9.5pt;
  background: #f7f7f1;
  border: 1px solid #e3e6dd;
  border-radius: 3px;
  padding: 1px 4px;
  color: #1f3a2d;
}

pre {
  background: #f7f7f1;
  border: 1px solid #e3e6dd;
  border-left: 4px solid #2f5a40;
  border-radius: 4px;
  padding: 10px 14px;
  font-size: 9.5pt;
  line-height: 1.45;
  overflow-x: hidden;
  white-space: pre-wrap;
  word-break: break-word;
}

pre code { background: none; border: none; padding: 0; }

blockquote {
  margin: 0.7em 0;
  padding: 0.6em 1em;
  border-left: 4px solid #b88c3b;
  background: #fbfbf6;
  color: #243029;
  font-style: italic;
}

blockquote p { margin: 0.2em 0; }

table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.7em 0 0.9em 0;
  font-size: 10pt;
}

th, td {
  border: 1px solid #e3e6dd;
  padding: 6px 9px;
  text-align: left;
  vertical-align: top;
}

th {
  background: #1f3a2d;
  color: #f6f5ec;
  font-weight: 700;
  font-size: 9.5pt;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

tr:nth-child(even) td { background: #fbfbf6; }

hr {
  border: none;
  height: 1px;
  background: #e3e6dd;
  margin: 1.5em 0;
}

strong { color: #142a20; }

em { color: #243029; }

/* cover banner — first heading + meta table get special treatment */
h1:first-child {
  background: linear-gradient(135deg, #142a20 0%, #2f5a40 100%);
  color: #f6f5ec;
  border-bottom: 4px solid #b88c3b;
  padding: 18px 22px;
  margin: -4px -6px 16px -6px;
  font-size: 22pt;
  line-height: 1.2;
  page-break-after: avoid;
}

h1:first-child + p strong { color: #2f5a40; }

/* meta table styling */
table:first-of-type th {
  background: #2f5a40;
  font-size: 8.5pt;
}

/* avoid orphan headings */
h1, h2, h3 { page-break-after: avoid; }
table, pre, blockquote { page-break-inside: avoid; }
"""


def render_html(md_text: str, title: str) -> str:
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{HEADER_CSS}</style>
</head>
<body><main>{body}</main></body>
</html>"""


def main() -> None:
    repo = Path(__file__).resolve().parent.parent
    md_path = repo / "REPORT.md"
    pdf_path = repo / "REPORT.pdf"

    md_text = md_path.read_text(encoding="utf-8")
    html = render_html(md_text, "ClearClause — Project Report")

    HTML(string=html, base_url=str(repo)).write_pdf(str(pdf_path))

    size_kb = pdf_path.stat().st_size // 1024
    print(f"Saved: {pdf_path}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
