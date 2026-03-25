#!/usr/bin/env python3
"""EpiClaw Survival Analysis -- R-backed Kaplan-Meier and Cox workflow."""
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

from reporting import generate_report_footer, generate_report_header, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "survival-analysis"
DEMO_ROWS = [
    {"time": 2, "event": 1, "group": "unvaccinated", "age": 62},
    {"time": 3, "event": 0, "group": "vaccinated", "age": 45},
    {"time": 4, "event": 1, "group": "unvaccinated", "age": 58},
    {"time": 5, "event": 0, "group": "vaccinated", "age": 39},
    {"time": 7, "event": 1, "group": "unvaccinated", "age": 54},
    {"time": 8, "event": 0, "group": "vaccinated", "age": 48},
]

R_SCRIPT = r'''
args <- commandArgs(trailingOnly=TRUE)
input_csv <- args[1]
time_col <- args[2]
event_col <- args[3]
group_col <- if (args[4] == "__NONE__") NULL else args[4]
covariates <- if (args[5] == "__NONE__") character(0) else strsplit(args[5], ",")[[1]]
km_csv <- args[6]
cox_csv <- args[7]
logrank_csv <- args[8]

suppressPackageStartupMessages(library(survival))
df <- read.csv(input_csv, check.names=FALSE)
if (!is.null(group_col)) {
  km_formula <- as.formula(paste0("Surv(", time_col, ", ", event_col, ") ~ ", group_col))
} else {
  km_formula <- as.formula(paste0("Surv(", time_col, ", ", event_col, ") ~ 1"))
}
fit <- survfit(km_formula, data=df)
km_tab <- data.frame(time=fit$time, surv=fit$surv, n.risk=fit$n.risk, n.event=fit$n.event)
write.csv(km_tab, km_csv, row.names=FALSE)

if (!is.null(group_col)) {
  lr <- survdiff(km_formula, data=df)
  p <- 1 - pchisq(lr$chisq, length(lr$n) - 1)
  write.csv(data.frame(chisq=lr$chisq, p_value=p), logrank_csv, row.names=FALSE)
} else {
  write.csv(data.frame(chisq=NA, p_value=NA), logrank_csv, row.names=FALSE)
}

if (length(covariates) > 0) {
  cox_formula <- as.formula(paste0("Surv(", time_col, ", ", event_col, ") ~ ", paste(covariates, collapse=" + ")))
  cox_fit <- coxph(cox_formula, data=df)
  cox_sum <- summary(cox_fit)
  cox_tab <- as.data.frame(cox_sum$coefficients)
  cox_tab$term <- rownames(cox_tab)
  cox_tab$ci_low <- cox_sum$conf.int[,3]
  cox_tab$ci_high <- cox_sum$conf.int[,4]
  write.csv(cox_tab, cox_csv, row.names=FALSE)
} else {
  write.csv(data.frame(), cox_csv, row.names=FALSE)
}
'''


def _run_command(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "unknown error")


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _run_survival(args: argparse.Namespace, output_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    rscript = shutil.which("Rscript")
    if not rscript:
        raise RuntimeError("Rscript not found on PATH.")
    script_path = output_dir / "survival_runner.R"
    script_path.write_text(R_SCRIPT, encoding="utf-8")
    km_csv = output_dir / "survival_table.csv"
    cox_csv = output_dir / "cox_results.csv"
    logrank_csv = output_dir / "logrank_test.csv"
    covariates = ",".join(args.covariates) if args.covariates else "__NONE__"
    cmd = [rscript, str(script_path), str(Path(args.input)), args.time_col, args.event_col, args.group_col or "__NONE__", covariates, str(km_csv), str(cox_csv), str(logrank_csv)]
    _run_command(cmd)
    return _read_csv(km_csv), _read_csv(cox_csv), _read_csv(logrank_csv)


def generate_report(output_path: Path, km_rows: list[dict[str, str]], cox_rows: list[dict[str, str]], logrank_rows: list[dict[str, str]], args: argparse.Namespace) -> None:
    def _first_value(row: dict[str, str], *keys: str, default: str = "nan") -> str:
        for key in keys:
            if key in row and row[key] not in {"", None}:
                return row[key]
        return default

    header = generate_report_header(title="Survival Analysis Report", skill_name=SKILL_NAME, extra_metadata={"Version": VERSION})
    lines = [
        "## Kaplan-Meier Summary",
        "",
        f"- Time column: `{args.time_col}`",
        f"- Event column: `{args.event_col}`",
        f"- Group column: `{args.group_col or 'none'}`",
        "",
        "## Survival Tail",
        "",
        "| Time | Survival | At risk | Events |",
        "|---|---|---|---|",
    ]
    for row in km_rows[:10]:
        lines.append(f"| {row['time']} | {float(row['surv']):.4f} | {row['n.risk']} | {row['n.event']} |")
    if logrank_rows:
        lines.extend([
            "",
            "## Log-rank Test",
            "",
            f"- Chi-squared: {logrank_rows[0].get('chisq', 'NA')}",
            f"- p-value: {logrank_rows[0].get('p_value', 'NA')}",
        ])
    if cox_rows:
        lines.extend([
            "",
            "## Cox Model",
            "",
            "| Term | Hazard ratio | 95% CI | p-value |",
            "|---|---|---|---|",
        ])
        for row in cox_rows:
            hazard_ratio = float(_first_value(row, "exp.coef.", "exp.coef", "exp_coef"))
            ci_low = float(_first_value(row, "ci_low", "lower .95", "lower.95"))
            ci_high = float(_first_value(row, "ci_high", "upper .95", "upper.95"))
            p_value = float(_first_value(row, "Pr...z..", "Pr(>|z|)", "p", "p.value"))
            lines.append(
                f"| {row['term']} | {hazard_ratio:.4f} | {ci_low:.4f} to {ci_high:.4f} | {p_value:.4g} |"
            )
    footer = generate_report_footer()
    output_path.write_text("\n".join([header] + lines + [footer]), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EpiClaw Survival Analysis -- Kaplan-Meier and Cox regression via R.")
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", required=True)
    parser.add_argument("--demo", action="store_true", help="Run built-in demo cohort")
    parser.add_argument("--time-col", default="time")
    parser.add_argument("--event-col", default="event")
    parser.add_argument("--group-col", default="group")
    parser.add_argument("--covariates", nargs="*", default=["age"])
    return parser


def _write_demo_input(path: Path) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["time", "event", "group", "age"])
        writer.writeheader()
        writer.writerows(DEMO_ROWS)
    return path


def _run_demo_survival(args: argparse.Namespace, output_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], int]:
    """Run demo survival analysis.

    Prefers Rscript when available for real Cox/logrank results.
    Falls back to manual KM computation with approximate logrank when R is absent.
    """
    demo_csv = _write_demo_input(output_dir / "demo_survival.csv")
    args.input = str(demo_csv)

    # Try real R execution first
    rscript = shutil.which("Rscript")
    if rscript:
        try:
            km_rows, cox_rows, logrank_rows = _run_survival(args, output_dir)
            return km_rows, cox_rows, logrank_rows, len(DEMO_ROWS)
        except Exception as e:
            print(f"[warn] R execution failed ({e}); using Python fallback for demo.")

    # Python fallback: manual KM + simple logrank approximation
    cohort = sorted(DEMO_ROWS, key=lambda row: row[args.time_col])
    at_risk = len(cohort)
    survival = 1.0
    km_rows: list[dict[str, str]] = []
    for row in cohort:
        events = int(row[args.event_col])
        if events:
            survival *= (at_risk - events) / at_risk
        km_rows.append({
            "time": str(row[args.time_col]),
            "surv": f"{survival:.6f}",
            "n.risk": str(at_risk),
            "n.event": str(events),
        })
        at_risk -= 1

    # Simple Mantel-Cox logrank: O-E per group
    group_col = args.group_col or "group"
    groups = list({r[group_col] for r in DEMO_ROWS})
    if len(groups) == 2:
        events_total = sum(int(r[args.event_col]) for r in DEMO_ROWS)
        # Observed per group
        obs = {g: sum(int(r[args.event_col]) for r in DEMO_ROWS if r[group_col] == g) for g in groups}
        # Under null, expected proportional to group size
        n_total = len(DEMO_ROWS)
        exp = {g: sum(1 for r in DEMO_ROWS if r[group_col] == g) / n_total * events_total for g in groups}
        chi2 = sum((obs[g] - exp[g]) ** 2 / exp[g] for g in groups if exp[g] > 0)
        try:
            from scipy.stats import chi2 as chi2_dist
            p_lr = float(1.0 - chi2_dist.cdf(chi2, df=1))
        except ImportError:
            # Simple approximation: p from chi2 with 1 df
            import math
            p_lr = math.exp(-chi2 / 2) if chi2 > 0 else 1.0
        logrank_rows = [{"chisq": f"{chi2:.4f}", "p_value": f"{p_lr:.4f}"}]
    else:
        logrank_rows = [{"chisq": "NA", "p_value": "NA"}]

    # Cox: cannot compute without R; return empty with note
    cox_rows: list[dict[str, str]] = []
    print("[info] Demo Cox model requires R (Rscript not found); Cox table omitted.")
    return km_rows, cox_rows, logrank_rows, len(DEMO_ROWS)


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.demo or not args.input:
        km_rows, cox_rows, logrank_rows, n_subjects = _run_demo_survival(args, output_dir)
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"[error] Input path not found: {input_path}")
        km_rows, cox_rows, logrank_rows = _run_survival(args, output_dir)
        n_subjects = sum(1 for _ in csv.DictReader(Path(args.input).open("r", encoding="utf-8", newline="")))
    report_path = output_dir / "report.md"
    generate_report(report_path, km_rows, cox_rows, logrank_rows, args)
    summary = {"n_subjects": n_subjects, "n_timepoints": len(km_rows), "n_cox_terms": len(cox_rows), "group_col": args.group_col}
    data = {"kaplan_meier": km_rows, "cox_model": cox_rows, "logrank_test": logrank_rows}
    write_result_json(output_dir=output_dir, skill=SKILL_NAME, version=VERSION, summary=summary, data=data)
    print(f"[info] Report written to {report_path}")
    print(f"[info] Result JSON written to {output_dir / 'result.json'}")


if __name__ == "__main__":
    main()
