#!/usr/bin/env python3
"""EpiClaw Vaccine-Effectiveness -- estimate VE via screening, test-negative, or cohort methods."""
from __future__ import annotations
import argparse, csv, math, sys
import sys
from pathlib import Path

from reporting import generate_report_header, generate_report_footer, write_result_json


VERSION = "0.1.0"
SKILL_NAME = "vaccine-effectiveness"

# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------

def ve_screening(
    cases_vax: int,
    pop_vax: int,
    cases_unvax: int,
    pop_unvax: int,

):
    risk_v = cases_vax / pop_vax
    risk_u = cases_unvax / pop_unvax
    rr = risk_v / risk_u
    ve = 1.0 - rr
    se = math.sqrt((1 / cases_vax) - (1 / pop_vax) + (1 / cases_unvax) - (1 / pop_unvax))
    lower = 1.0 - math.exp(math.log(rr) + 1.959964 * se)
    upper = 1.0 - math.exp(math.log(rr) - 1.959964 * se)
    return ve, lower, upper
def ve_test_negative(
    cases_vax: int,
    cases_unvax: int,
    controls_vax: int,
    controls_unvax: int,

):
    odds_ratio = (cases_vax * controls_unvax) / (cases_unvax * controls_vax)
    ve = 1.0 - odds_ratio
    se = math.sqrt(1 / cases_vax + 1 / cases_unvax + 1 / controls_vax + 1 / controls_unvax)
    lower_or = math.exp(math.log(odds_ratio) - 1.959964 * se)
    upper_or = math.exp(math.log(odds_ratio) + 1.959964 * se)
    return ve, 1.0 - upper_or, 1.0 - lower_or
# ---------------------------------------------------------------------------
# CSV input loaders
# ---------------------------------------------------------------------------

def load_screening_csv(path: str) -> tuple[int, int, int, int]:
    """Load screening/cohort data from CSV.

    Expected columns: group (vaccinated/unvaccinated), cases, population
    """
    rows: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            g = row["group"].strip().lower()
            rows[g] = {"cases": int(row["cases"]), "population": int(row["population"])}
    vax = rows.get("vaccinated", rows.get("vax", {}))
    unvax = rows.get("unvaccinated", rows.get("unvax", {}))
    if not vax or not unvax:
        raise ValueError("CSV must have rows with group='vaccinated' and group='unvaccinated'")
    return vax["cases"], vax["population"], unvax["cases"], unvax["population"]


def load_tnd_csv(path: str) -> tuple[int, int, int, int]:
    """Load test-negative design data from CSV.

    Expected columns: group (vaccinated/unvaccinated), cases, controls
    """
    rows: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            g = row["group"].strip().lower()
            rows[g] = {"cases": int(row["cases"]), "controls": int(row["controls"])}
    vax = rows.get("vaccinated", rows.get("vax", {}))
    unvax = rows.get("unvaccinated", rows.get("unvax", {}))
    if not vax or not unvax:
        raise ValueError("CSV must have rows with group='vaccinated' and group='unvaccinated'")
    return vax["cases"], unvax["cases"], vax["controls"], unvax["controls"]


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

def run_demo_screening() -> dict:
    print("[info] Running screening-method demo")
    cases_vax, pop_vax = 150, 6000
    cases_unvax, pop_unvax = 200, 4000
    ve, ve_lower, ve_upper = ve_screening(cases_vax, pop_vax, cases_unvax, pop_unvax)
    ar_v = cases_vax / pop_vax
    ar_u = cases_unvax / pop_unvax
    return {
        "method": "screening",
        "ve": ve,
        "ve_lower": ve_lower,
        "ve_upper": ve_upper,
        "ar_vaccinated": ar_v,
        "ar_unvaccinated": ar_u,
        "table": {
            "cases_vaccinated": cases_vax,
            "population_vaccinated": pop_vax,
            "cases_unvaccinated": cases_unvax,
            "population_unvaccinated": pop_unvax,
        },
    }


def run_demo_test_negative() -> dict:
    print("[info] Running test-negative design demo")
    # 2x2: cases vaccinated=80, cases unvaccinated=120,
    #       controls vaccinated=200, controls unvaccinated=150
    cases_vax, cases_unvax = 80, 120
    controls_vax, controls_unvax = 200, 150
    ve, ve_lower, ve_upper = ve_test_negative(cases_vax, cases_unvax, controls_vax, controls_unvax)
    or_val = (cases_vax * controls_unvax) / (controls_vax * cases_unvax)
    return {
        "method": "test-negative",
        "ve": ve,
        "ve_lower": ve_lower,
        "ve_upper": ve_upper,
        "or": or_val,
        "table": {
            "cases_vaccinated": cases_vax,
            "cases_unvaccinated": cases_unvax,
            "controls_vaccinated": controls_vax,
            "controls_unvaccinated": controls_unvax,
        },
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report(res: dict, pathogen: str, vaccine: str) -> str:
    header = generate_report_header(
        title="Vaccine Effectiveness Analysis",
        skill_name=SKILL_NAME,
        extra_metadata={"Pathogen": pathogen, "Vaccine": vaccine, "Method": res["method"]},
    )
    ve_pct = res["ve"] * 100
    lo_pct = res["ve_lower"] * 100
    hi_pct = res["ve_upper"] * 100

    lines = [header]
    lines.append("## Results\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Vaccine Effectiveness | **{ve_pct:.1f}%** |")
    lines.append(f"| 95% CI | ({lo_pct:.1f}%, {hi_pct:.1f}%) |")
    lines.append(f"| Method | {res['method']} |")

    if res["method"] == "screening":
        t = res["table"]
        ar_v = res["ar_vaccinated"]
        ar_u = res["ar_unvaccinated"]
        lines.append("\n## Attack Rates\n")
        lines.append("| Group | Cases | Population | Attack Rate |")
        lines.append("|-------|-------|------------|-------------|")
        lines.append(f"| Vaccinated | {t['cases_vaccinated']} | {t['population_vaccinated']} | {ar_v:.4f} ({ar_v*100:.2f}%) |")
        lines.append(f"| Unvaccinated | {t['cases_unvaccinated']} | {t['population_unvaccinated']} | {ar_u:.4f} ({ar_u*100:.2f}%) |")

    elif res["method"] == "test-negative":
        t = res["table"]
        lines.append("\n## 2x2 Table (Test-Negative Design)\n")
        lines.append("|  | Vaccinated | Unvaccinated |")
        lines.append("|--|-----------|--------------|")
        lines.append(f"| Cases | {t['cases_vaccinated']} | {t['cases_unvaccinated']} |")
        lines.append(f"| Controls | {t['controls_vaccinated']} | {t['controls_unvaccinated']} |")
        lines.append(f"\n**Odds Ratio**: {res['or']:.3f}")

    lines.append("\n## Interpretation\n")
    if ve_pct >= 0:
        lines.append(
            f"The {vaccine} vaccine demonstrates **{ve_pct:.1f}% effectiveness** against {pathogen} "
            f"(95% CI: {lo_pct:.1f}%–{hi_pct:.1f}%). "
        )
        if lo_pct > 0:
            lines.append("The lower confidence bound exceeds 0%, suggesting statistically significant protection.")
        else:
            lines.append("The confidence interval crosses 0%, indicating the estimate is not statistically significant at the 5% level.")
    else:
        lines.append(f"VE is negative ({ve_pct:.1f}%), suggesting no protective effect or possible bias.")

    lines.append(generate_report_footer())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Vaccine effectiveness estimation")
    parser.add_argument("--method", choices=["screening", "test-negative", "cohort"], default="screening")
    parser.add_argument("--pathogen", default="Influenza")
    parser.add_argument("--vaccine", default="Seasonal Flu Vaccine")
    parser.add_argument("--output", default="output/vaccine-effectiveness")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    parser.add_argument("--input", dest="input_path", default=None,
                        help="CSV file with columns: group, cases, population (screening/cohort) "
                             "or group, cases, controls (test-negative)")
    # Direct CLI args (alternative to --input CSV)
    parser.add_argument("--cases-vax", type=int, default=None, help="Cases among vaccinated")
    parser.add_argument("--pop-vax", type=int, default=None, help="Total vaccinated population (screening/cohort)")
    parser.add_argument("--cases-unvax", type=int, default=None, help="Cases among unvaccinated")
    parser.add_argument("--pop-unvax", type=int, default=None, help="Total unvaccinated population (screening/cohort)")
    parser.add_argument("--controls-vax", type=int, default=None, help="Controls among vaccinated (TND)")
    parser.add_argument("--controls-unvax", type=int, default=None, help="Controls among unvaccinated (TND)")
    args = parser.parse_args(argv)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[info] EpiClaw {SKILL_NAME} v{VERSION}")
    print(f"[info] Method: {args.method}, Pathogen: {args.pathogen}, Vaccine: {args.vaccine}")

    use_demo = args.demo or (
        args.input_path is None
        and args.cases_vax is None
        and args.cases_unvax is None
    )

    if args.method in ("screening", "cohort"):
        if use_demo:
            res = run_demo_screening()
        elif args.input_path:
            print(f"[info] Loading screening data from: {args.input_path}")
            cv, pv, cu, pu = load_screening_csv(args.input_path)
            ve, ve_lower, ve_upper = ve_screening(cv, pv, cu, pu)
            res = {
                "method": args.method,
                "ve": ve, "ve_lower": ve_lower, "ve_upper": ve_upper,
                "ar_vaccinated": cv / pv, "ar_unvaccinated": cu / pu,
                "table": {"cases_vaccinated": cv, "population_vaccinated": pv,
                          "cases_unvaccinated": cu, "population_unvaccinated": pu},
            }
        elif args.cases_vax is not None and args.pop_vax is not None and args.cases_unvax is not None and args.pop_unvax is not None:
            ve, ve_lower, ve_upper = ve_screening(args.cases_vax, args.pop_vax, args.cases_unvax, args.pop_unvax)
            res = {
                "method": args.method,
                "ve": ve, "ve_lower": ve_lower, "ve_upper": ve_upper,
                "ar_vaccinated": args.cases_vax / args.pop_vax,
                "ar_unvaccinated": args.cases_unvax / args.pop_unvax,
                "table": {"cases_vaccinated": args.cases_vax, "population_vaccinated": args.pop_vax,
                          "cases_unvaccinated": args.cases_unvax, "population_unvaccinated": args.pop_unvax},
            }
        else:
            parser.error("Provide --input CSV or --cases-vax / --pop-vax / --cases-unvax / --pop-unvax")
    elif args.method == "test-negative":
        if use_demo:
            res = run_demo_test_negative()
        elif args.input_path:
            print(f"[info] Loading TND data from: {args.input_path}")
            cv, cu, ctv, ctu = load_tnd_csv(args.input_path)
            ve, ve_lower, ve_upper = ve_test_negative(cv, cu, ctv, ctu)
            or_val = (cv * ctu) / (cu * ctv)
            res = {
                "method": "test-negative",
                "ve": ve, "ve_lower": ve_lower, "ve_upper": ve_upper, "or": or_val,
                "table": {"cases_vaccinated": cv, "cases_unvaccinated": cu,
                          "controls_vaccinated": ctv, "controls_unvaccinated": ctu},
            }
        elif args.cases_vax is not None and args.cases_unvax is not None and args.controls_vax is not None and args.controls_unvax is not None:
            ve, ve_lower, ve_upper = ve_test_negative(args.cases_vax, args.cases_unvax, args.controls_vax, args.controls_unvax)
            or_val = (args.cases_vax * args.controls_unvax) / (args.cases_unvax * args.controls_vax)
            res = {
                "method": "test-negative",
                "ve": ve, "ve_lower": ve_lower, "ve_upper": ve_upper, "or": or_val,
                "table": {"cases_vaccinated": args.cases_vax, "cases_unvaccinated": args.cases_unvax,
                          "controls_vaccinated": args.controls_vax, "controls_unvaccinated": args.controls_unvax},
            }
        else:
            parser.error("Provide --input CSV or --cases-vax / --cases-unvax / --controls-vax / --controls-unvax")

    report_md = build_report(res, args.pathogen, args.vaccine)
    report_path = out_dir / "report.md"
    report_path.write_text(report_md)
    print(f"[info] Report written to {report_path}")

    summary = {
        "method": res["method"],
        "vaccine_effectiveness": round(res["ve"], 4),
        "ve_lower_95ci": round(res["ve_lower"], 4),
        "ve_upper_95ci": round(res["ve_upper"], 4),
        "pathogen": args.pathogen,
        "vaccine": args.vaccine,
    }
    data: dict = {"method_details": {k: v for k, v in res.items() if k not in ("ve", "ve_lower", "ve_upper", "method")}}
    if "table" in res:
        data["2x2_table"] = res["table"]

    result_path = write_result_json(out_dir, SKILL_NAME, VERSION, summary, data)
    print(f"[info] Result JSON written to {result_path}")
    print(f"[info] Done. VE={res['ve']*100:.1f}% (95% CI: {res['ve_lower']*100:.1f}%–{res['ve_upper']*100:.1f}%)")


if __name__ == "__main__":
    main()
