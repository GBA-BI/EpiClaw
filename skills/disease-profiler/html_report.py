"""Reusable HTML report builder for EpiClaw skills.

Generates self-contained HTML reports with embedded CSS — no external
dependencies (no Jinja2). Reports open cleanly in browsers and mobile devices.
"""

from __future__ import annotations

import html
import math
from datetime import datetime, timezone
from pathlib import Path

from reporting import DISCLAIMER

# ---------------------------------------------------------------------------
# Embedded CSS — EpiClaw teal/blue public health branding
# ---------------------------------------------------------------------------

_CSS = """\
:root {
  /* Brand palette — public health teal */
  --ec-teal-900: #004d40;
  --ec-teal-700: #00695c;
  --ec-teal-500: #00897b;
  --ec-teal-100: #e0f2f1;
  --ec-teal-50:  #e0f7fa;

  /* Severity */
  --ec-red-700:   #c62828;
  --ec-red-100:   #ffebee;
  --ec-red-50:    #fff5f5;
  --ec-amber-700: #f57f17;
  --ec-amber-100: #fff8e1;
  --ec-grey-700:  #616161;
  --ec-grey-500:  #9e9e9e;
  --ec-grey-300:  #e0e0e0;
  --ec-grey-100:  #f5f5f5;
  --ec-grey-50:   #fafafa;

  /* Surfaces */
  --ec-bg:        #fafafa;
  --ec-surface:   #ffffff;
  --ec-text:      #212121;
  --ec-text-secondary: #616161;
  --ec-border:    #e0e0e0;

  /* Spacing */
  --ec-space-xs: 4px;
  --ec-space-sm: 8px;
  --ec-space-md: 16px;
  --ec-space-lg: 24px;
  --ec-space-xl: 32px;
  --ec-space-2xl: 48px;

  /* Radii */
  --ec-radius-sm: 6px;
  --ec-radius-md: 10px;
  --ec-radius-lg: 16px;

  /* Shadows */
  --ec-shadow-sm: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
  --ec-shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06);
}
*, *::before, *::after { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: var(--ec-text);
  background: var(--ec-bg);
  margin: 0;
  padding: var(--ec-space-md);
  max-width: 960px;
  margin-left: auto;
  margin-right: auto;
}
h1 { color: var(--ec-teal-700); border-bottom: 3px solid var(--ec-teal-700); padding-bottom: 8px; }
h2 { color: #424242; margin-top: var(--ec-space-xl); }
h3 { color: var(--ec-grey-700); margin-top: var(--ec-space-lg); }

/* Branded header */
.report-header {
  background: linear-gradient(135deg, #004d40 0%, #00695c 50%, #00796b 100%);
  color: white;
  padding: var(--ec-space-lg) var(--ec-space-xl);
  border-radius: var(--ec-radius-lg);
  margin: 0 0 var(--ec-space-xl) 0;
}
.report-header h1 {
  margin: 0; font-size: 1.8em; font-weight: 700; border: none; padding: 0;
  color: white; letter-spacing: -0.02em;
}
.report-header .subtitle {
  margin: var(--ec-space-xs) 0 0 0; font-size: 0.95em; opacity: 0.9; font-weight: 400;
}

/* Metadata block */
.metadata { background: var(--ec-teal-100); border-radius: var(--ec-radius-sm); padding: 12px 16px; margin-bottom: var(--ec-space-lg); }
.metadata p { margin: 4px 0; font-size: 0.95em; }
.metadata strong { color: var(--ec-teal-900); }

/* Tables */
table { width: 100%; border-collapse: collapse; margin: var(--ec-space-md) 0; font-size: 0.9em; }
th { background: var(--ec-teal-100); color: var(--ec-teal-900); text-align: left; padding: 10px 12px; border-bottom: 2px solid #80cbc4; }
td { padding: 8px 12px; border-bottom: 1px solid var(--ec-border); }
tr:nth-child(even) { background: var(--ec-grey-100); }
tr:hover { background: var(--ec-teal-100); }

/* Table wrapper for mobile scroll */
.table-wrap {
  overflow-x: auto; -webkit-overflow-scrolling: touch;
  margin: var(--ec-space-md) 0; border-radius: var(--ec-radius-md); border: 1px solid var(--ec-border);
}
.table-wrap table { margin: 0; border: none; }

/* Severity-banded table rows */
tr.row-critical { background: var(--ec-red-50); }
tr.row-critical:hover { background: var(--ec-red-100); }
tr.row-warning { background: #fffde7; }
tr.row-warning:hover { background: var(--ec-amber-100); }
tr.row-normal { background: var(--ec-teal-50); }
tr.row-normal:hover { background: var(--ec-teal-100); }

/* Badges */
.badge { display: inline-flex; align-items: center; gap: 4px; padding: 3px 12px;
         border-radius: 20px; font-size: 0.78em; font-weight: 700;
         text-transform: uppercase; letter-spacing: 0.05em; white-space: nowrap; }
.badge-critical { background: #ffcdd2; color: #b71c1c; }
.badge-warning { background: #fff9c4; color: #e65100; }
.badge-normal { background: #b2dfdb; color: #004d40; }
.badge-info { background: #e0e0e0; color: #424242; }

/* Alert boxes */
.alert-box { border-left: 4px solid; border-radius: var(--ec-radius-sm); padding: 12px 16px; margin: 12px 0; }
.alert-box-critical { border-color: var(--ec-red-700); background: var(--ec-red-100); }
.alert-box-warning { border-color: var(--ec-amber-700); background: var(--ec-amber-100); }
.alert-box-info { border-color: var(--ec-grey-700); background: var(--ec-grey-100); }
.alert-box h4 { margin: 0 0 8px 0; }
.alert-box-critical h4 { color: var(--ec-red-700); }
.alert-box-warning h4 { color: var(--ec-amber-700); }
.alert-box-info h4 { color: var(--ec-grey-700); }

/* Summary cards */
.summary-cards {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--ec-space-md); margin: var(--ec-space-md) 0 var(--ec-space-xl) 0;
}
.summary-card {
  background: var(--ec-surface); border-radius: var(--ec-radius-md);
  padding: var(--ec-space-lg) var(--ec-space-md); text-align: center;
  box-shadow: var(--ec-shadow-sm); border-top: 4px solid transparent;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.summary-card:hover { box-shadow: var(--ec-shadow-md); transform: translateY(-2px); }
.summary-card .count { font-size: 2.5em; font-weight: 800; display: block; line-height: 1.1; }
.summary-card .label {
  font-size: 0.8em; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--ec-text-secondary); margin-top: var(--ec-space-xs); display: block;
}
.summary-card.critical { border-top-color: var(--ec-red-700); }
.summary-card.critical .count { color: var(--ec-red-700); }
.summary-card.warning { border-top-color: var(--ec-amber-700); }
.summary-card.warning .count { color: var(--ec-amber-700); }
.summary-card.normal { border-top-color: var(--ec-teal-700); }
.summary-card.normal .count { color: var(--ec-teal-700); }

/* Disclaimer */
.disclaimer { background: #fff3e0; border: 1px solid #ffcc80; border-radius: var(--ec-radius-sm);
              padding: var(--ec-space-xs) var(--ec-space-md); margin: 0 0 var(--ec-space-sm) 0; font-size: 0.8em; color: #e65100; line-height: 1.4; }
.disclaimer-bottom { margin: var(--ec-space-xl) 0 0 0; }

/* Collapsible details */
details { border: 1px solid var(--ec-border); border-radius: var(--ec-radius-md); margin: var(--ec-space-md) 0; overflow: hidden; }
details summary {
  cursor: pointer; padding: var(--ec-space-md); font-weight: 600; color: var(--ec-text);
  background: var(--ec-grey-50); border-radius: var(--ec-radius-md);
  list-style: none; display: flex; align-items: center; justify-content: space-between;
}
details summary::-webkit-details-marker { display: none; }
details summary::after {
  content: "\\25B6"; font-size: 0.7em; color: var(--ec-grey-500); transition: transform 0.2s ease;
}
details[open] summary::after { transform: rotate(90deg); }
details[open] summary { border-bottom: 1px solid var(--ec-border); border-radius: var(--ec-radius-md) var(--ec-radius-md) 0 0; }
details > :not(summary) { padding: 0 var(--ec-space-md); }

/* Branded footer */
.report-footer {
  margin-top: var(--ec-space-2xl); padding-top: var(--ec-space-lg);
  border-top: 2px solid var(--ec-teal-100); text-align: center;
  color: var(--ec-text-secondary); font-size: 0.85em;
}
.report-footer .footer-brand { font-weight: 700; color: var(--ec-teal-700); }

/* Responsive */
@media (max-width: 600px) {
  body { padding: var(--ec-space-sm); }
  table { font-size: 0.8em; }
  th, td { padding: 6px 8px; }
  .summary-cards { grid-template-columns: repeat(2, 1fr); }
  .summary-card { padding: var(--ec-space-md); }
  .summary-card .count { font-size: 1.8em; }
  .report-header { padding: var(--ec-space-md); }
  .report-header h1 { font-size: 1.4em; }
}

/* Print */
@media print {
  body { background: white; max-width: 100%; padding: 0; }
  .report-header { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .summary-card { break-inside: avoid; box-shadow: none; border: 1px solid #ccc; }
  details { break-inside: avoid; }
  .disclaimer { break-inside: avoid; }
  tr { break-inside: avoid; }
}
"""

# Badge CSS class mapping
_BADGE_CLASS = {
    "critical": "badge-critical",
    "warning": "badge-warning",
    "normal": "badge-normal",
    "info": "badge-info",
}


class HtmlReportBuilder:
    """Builds a self-contained HTML report with embedded CSS."""

    def __init__(self, title: str, skill: str, extra_css: str = "") -> None:
        self._title = html.escape(title)
        self._skill = html.escape(skill)
        self._extra_css = extra_css
        self._sections: list[str] = []
        self._custom_header = False
        self._custom_footer = False
        self._has_disclaimer = False

    def add_header_block(self, title: str, subtitle: str = "") -> "HtmlReportBuilder":
        """Add a branded gradient header."""
        sub = f'<p class="subtitle">{html.escape(subtitle)}</p>' if subtitle else ""
        self._sections.append(
            f'<div class="report-header">'
            f"<h1>{html.escape(title)}</h1>"
            f"{sub}"
            f"</div>"
        )
        self._custom_header = True
        return self

    def add_metadata(self, items: dict[str, str]) -> "HtmlReportBuilder":
        parts = []
        for key, val in items.items():
            parts.append(f"<p><strong>{html.escape(key)}:</strong> {html.escape(str(val))}</p>")
        self._sections.append(f'<div class="metadata">{"".join(parts)}</div>')
        return self

    def add_section(self, heading: str, level: int = 2) -> "HtmlReportBuilder":
        tag = f"h{min(max(level, 1), 6)}"
        self._sections.append(f"<{tag}>{html.escape(heading)}</{tag}>")
        return self

    def add_paragraph(self, text: str, css_class: str = "") -> "HtmlReportBuilder":
        cls = f' class="{html.escape(css_class)}"' if css_class else ""
        self._sections.append(f"<p{cls}>{html.escape(text)}</p>")
        return self

    def add_summary_cards(self, cards: list[tuple[str, int, str]]) -> "HtmlReportBuilder":
        """Add summary cards. Each card is (label, count, category)."""
        parts = []
        for label, count, category in cards:
            cat_class = html.escape(category)
            parts.append(
                f'<div class="summary-card {cat_class}">'
                f'<span class="count">{int(count)}</span>'
                f'<span class="label">{html.escape(label)}</span>'
                f"</div>"
            )
        self._sections.append(f'<div class="summary-cards">{"".join(parts)}</div>')
        return self

    def add_alert_box(self, severity: str, title: str, body: str) -> "HtmlReportBuilder":
        sev = severity if severity in ("critical", "warning", "info") else "info"
        self._sections.append(
            f'<div class="alert-box alert-box-{sev}">'
            f"<h4>{html.escape(title)}</h4>"
            f"<p>{html.escape(body)}</p>"
            f"</div>"
        )
        return self

    def add_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        badge_col: int | None = None,
    ) -> "HtmlReportBuilder":
        parts = ["<table><thead><tr>"]
        for h in headers:
            parts.append(f"<th>{html.escape(h)}</th>")
        parts.append("</tr></thead><tbody>")
        for row in rows:
            parts.append("<tr>")
            for i, cell in enumerate(row):
                if i == badge_col:
                    badge_cls = _BADGE_CLASS.get(cell, "badge-info")
                    parts.append(f'<td><span class="badge {badge_cls}">{html.escape(cell)}</span></td>')
                else:
                    parts.append(f"<td>{html.escape(str(cell))}</td>")
            parts.append("</tr>")
        parts.append("</tbody></table>")
        self._sections.append("".join(parts))
        return self

    def add_table_wrapped(
        self,
        headers: list[str],
        rows: list[list[str]],
        badge_col: int | None = None,
        row_classes: list[str] | None = None,
    ) -> "HtmlReportBuilder":
        """Add a table wrapped for mobile scrolling."""
        parts = ['<div class="table-wrap"><table><thead><tr>']
        for h in headers:
            parts.append(f"<th>{html.escape(h)}</th>")
        parts.append("</tr></thead><tbody>")
        for idx, row in enumerate(rows):
            cls = ""
            if row_classes and idx < len(row_classes):
                cls = f' class="{html.escape(row_classes[idx])}"'
            parts.append(f"<tr{cls}>")
            for i, cell in enumerate(row):
                if i == badge_col:
                    badge_cls = _BADGE_CLASS.get(cell, "badge-info")
                    parts.append(f'<td><span class="badge {badge_cls}">{html.escape(cell)}</span></td>')
                else:
                    parts.append(f"<td>{html.escape(str(cell))}</td>")
            parts.append("</tr>")
        parts.append("</tbody></table></div>")
        self._sections.append("".join(parts))
        return self

    def add_details(self, summary_text: str, content_html: str) -> "HtmlReportBuilder":
        """Add a collapsible <details>/<summary> section."""
        self._sections.append(
            f"<details><summary>{html.escape(summary_text)}</summary>"
            f"{content_html}"
            f"</details>"
        )
        return self

    def add_raw_html(self, raw: str) -> "HtmlReportBuilder":
        self._sections.append(raw)
        return self

    def add_disclaimer(self) -> "HtmlReportBuilder":
        self._sections.append(
            f'<div class="disclaimer"><strong>Disclaimer:</strong> {html.escape(DISCLAIMER)}</div>'
        )
        self._has_disclaimer = True
        return self

    def add_footer_block(self, skill: str, version: str = "") -> "HtmlReportBuilder":
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ver = f" v{html.escape(version)}" if version else ""
        self._sections.append(
            f'<div class="report-footer">'
            f'<p>Generated by <span class="footer-brand">EpiClaw</span> '
            f"\u00b7 {html.escape(skill)}{ver} \u00b7 {now}</p>"
            f'<p style="font-size:0.8em;margin-top:4px;">Data processed locally. '
            f"No data was transmitted to external servers without consent.</p></div>"
        )
        self._custom_footer = True
        return self

    def render(self) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        body = "\n".join(self._sections)
        disclaimer_bottom = ""
        if self._has_disclaimer:
            disclaimer_bottom = (
                f'<div class="disclaimer disclaimer-bottom">'
                f'<strong>Disclaimer:</strong> {html.escape(DISCLAIMER)}</div>'
            )
        title_block = "" if self._custom_header else f"<h1>{self._title}</h1>"
        footer = "" if self._custom_footer else (
            f'<p style="color:#757575;font-size:0.9em;margin-top:32px;">'
            f"Generated by EpiClaw &middot; {html.escape(self._skill)} &middot; {now}</p>"
        )
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._title}</title>
<style>
{_CSS}
{self._extra_css}
</style>
</head>
<body>
{title_block}
{body}
{disclaimer_bottom}
{footer}
</body>
</html>"""


def write_html_report(output_dir: str | Path, filename: str, content: str) -> Path:
    """Write an HTML string to *output_dir*/*filename* and return the path."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    path.write_text(content, encoding="utf-8")
    return path
