# -*- coding: utf-8 -*-
from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from packager.models import ValidationResult, PackPlanItem


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _esc(s: Any) -> str:
    return html.escape("" if s is None else str(s))


def _group_results(results: List[ValidationResult]) -> Dict[str, List[ValidationResult]]:
    groups = {"ERROR": [], "WARNING": [], "INFO": []}
    for r in results:
        lvl = (r.level or "INFO").upper()
        if lvl not in groups:
            groups[lvl] = []
        groups[lvl].append(r)
    return groups


def build_report_html(
    tool_name: str,
    tool_version: str,
    profile: str,
    input_root: str,
    output_root: str,
    project: str,
    asset_name: str,
    version: str,
    validation_results: List[ValidationResult],
    plan: List[PackPlanItem],
    hashes_by_src: Optional[Dict[str, str]] = None,
    hash_algo: str = "sha1",
) -> str:
    hashes_by_src = hashes_by_src or {}

    # Category counts
    by_cat: Dict[str, int] = {}
    for p in plan:
        by_cat[p.category] = by_cat.get(p.category, 0) + 1

    groups = _group_results(validation_results)

    # Simple inline CSS (clean + readable)
    css = """
    body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 24px; }
    h1 { margin: 0 0 6px 0; }
    .sub { color: #444; margin: 0 0 18px 0; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 14px; margin: 12px 0; }
    .row { display: flex; gap: 18px; flex-wrap: wrap; }
    .kv { min-width: 260px; }
    .k { color: #666; font-size: 12px; }
    .v { font-weight: 600; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    th, td { border-bottom: 1px solid #eee; padding: 8px; text-align: left; vertical-align: top; font-size: 13px; }
    th { background: #fafafa; position: sticky; top: 0; }
    .pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }
    .err { background: #ffe9e9; color: #8a0000; }
    .warn { background: #fff4d6; color: #7a5200; }
    .info { background: #e9f3ff; color: #003a7a; }
    code { background: #f6f6f6; padding: 1px 4px; border-radius: 6px; }
    .small { font-size: 12px; color: #555; }
    """

    def pill(level: str) -> str:
        lvl = level.upper()
        if lvl == "ERROR":
            return '<span class="pill err">ERROR</span>'
        if lvl == "WARNING":
            return '<span class="pill warn">WARNING</span>'
        return '<span class="pill info">INFO</span>'

    # Build validation rows
    def render_results(level: str, items: List[ValidationResult]) -> str:
        if not items:
            return f"<p class='small'>No {level.lower()}s.</p>"
        rows = []
        for r in items:
            rel = f"<code>{_esc(r.relpath)}</code>" if r.relpath else ""
            rows.append(
                f"<tr>"
                f"<td>{pill(r.level)}</td>"
                f"<td><code>{_esc(r.code)}</code></td>"
                f"<td>{_esc(r.message)} {rel}</td>"
                f"</tr>"
            )
        return (
            "<table>"
            "<thead><tr><th>Level</th><th>Code</th><th>Message</th></tr></thead>"
            "<tbody>"
            + "".join(rows) +
            "</tbody></table>"
        )

    # Plan rows (src -> dst)
    plan_rows = []
    for p in plan:
        h = hashes_by_src.get(p.src)
        hash_cell = f"<code>{_esc(h)}</code>" if h else ""
        plan_rows.append(
            f"<tr>"
            f"<td><code>{_esc(p.category)}</code></td>"
            f"<td class='small'>{_esc(p.relpath)}</td>"
            f"<td class='small'>{_esc(p.dst)}</td>"
            f"<td class='small'>{hash_cell}</td>"
            f"</tr>"
        )

    cat_list = "".join(
        f"<li><code>{_esc(cat)}</code> - {count}</li>"
        for cat, count in sorted(by_cat.items(), key=lambda kv: (-kv[1], kv[0]))
    ) or "<li class='small'>No plan items.</li>"

    html_out = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{_esc(tool_name)} Report - {_esc(asset_name)} {_esc(version)}</title>
  <style>{css}</style>
</head>
<body>
  <h1>{_esc(tool_name)} - Delivery Report</h1>
  <p class="sub">Generated {_esc(_utc_now())} (UTC) - Tool version {_esc(tool_version)}</p>

  <div class="card">
    <div class="row">
      <div class="kv"><div class="k">Profile</div><div class="v">{_esc(profile)}</div></div>
      <div class="kv"><div class="k">Project</div><div class="v">{_esc(project)}</div></div>
      <div class="kv"><div class="k">Asset</div><div class="v">{_esc(asset_name)}</div></div>
      <div class="kv"><div class="k">Delivery Version</div><div class="v">{_esc(version)}</div></div>
    </div>
    <div class="row" style="margin-top:10px;">
      <div class="kv" style="min-width:420px;"><div class="k">Input Root</div><div class="v"><code>{_esc(input_root)}</code></div></div>
      <div class="kv" style="min-width:420px;"><div class="k">Output Root</div><div class="v"><code>{_esc(output_root)}</code></div></div>
    </div>
  </div>

  <div class="card">
    <h2>Validation Summary</h2>
    <p class="small">
      {len(groups.get("ERROR", []))} error(s),
      {len(groups.get("WARNING", []))} warning(s),
      {len(groups.get("INFO", []))} info
    </p>

    <h3>Errors</h3>
    {render_results("ERROR", groups.get("ERROR", []))}

    <h3>Warnings</h3>
    {render_results("WARNING", groups.get("WARNING", []))}

    <h3>Info</h3>
    {render_results("INFO", groups.get("INFO", []))}
  </div>

  <div class="card">
    <h2>Packaging Plan</h2>
    <p class="small">Total planned files: <b>{len(plan)}</b></p>
    <ul>{cat_list}</ul>

    <h3>Files</h3>
    <p class="small">Hash column shows source file {hash_algo} when available.</p>
    <table>
      <thead>
        <tr>
          <th>Category</th>
          <th>Source (relpath)</th>
          <th>Destination</th>
          <th>Hash</th>
        </tr>
      </thead>
      <tbody>
        {''.join(plan_rows) if plan_rows else '<tr><td colspan="4" class="small">No files planned.</td></tr>'}
      </tbody>
    </table>
  </div>

</body>
</html>
"""
    return html_out


def write_report_html(html_text: str, report_path: str) -> str:
    p = Path(report_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html_text, encoding="utf-8")
    return str(p)
