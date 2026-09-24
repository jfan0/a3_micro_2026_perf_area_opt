"""Generate the performance-area efficiency table for the perf_area_eff_opt flow.

Reads {DB_DIR}/perf_area_eff.db and emits a per-branch row with:
  - total cell area (Yosys) and fmax (OpenSTA)
  - mean embench IPC
  - perf_area_eff = embench_speed_score / area, in speed/mm2
  - the embench speed score and its per-MHz figure
  - the efficiency change vs the branch's parent and vs the baseline branch
  - riscv-tests passed, and whether both hard gates passed

Only branches that recorded an efficiency are listed; pass --all to include
failed and incomplete runs. The DB is opened read-only.
"""

import argparse
import os
import sqlite3
from pathlib import Path

DB_DIR = os.environ.get(
    "PERF_AREA_EFF_DB_DIR", os.path.expanduser("~/perf_area_eff_DB"))
BASELINE_BRANCH_NAME = "baseline"

COLUMNS = ["id", "name", "parent_id", "status", "area", "sram_macro_area",
           "std_cell_area", "fmax_mhz", "mean_ipc",
           "embench_speed_score", "embench_speed_score_per_mhz",
           "embench_speed_score_area_eff", "riscv_tests_passed",
           "riscv_tests_total", "gates_passed"]


def fetch_branches(conn):
    """Return one dict per branch, in creation order."""
    return [dict(zip(COLUMNS, row)) for row in conn.execute(
        f"SELECT {', '.join(COLUMNS)} FROM branches ORDER BY id")]


def pct_change(value, reference):
    if value is None or not reference:
        return None
    return (value / reference - 1.0) * 100.0


def num(value, fmt):
    return "-" if value is None else format(value, fmt)


def format_table(rows):
    header = ["Branch", "Parent", "Status", "Fmax (MHz)", "Area (mm2)",
              "Speed", "Speed/MHz", "Eff (speed/mm2)", "Eff (speed/MHz/mm2)",
              "vs parent", "vs baseline", "riscv-tests", "Gates"]
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        riscv = ("-" if r["riscv_tests_total"] is None
                 else f"{r['riscv_tests_passed']}/{r['riscv_tests_total']}")
        gates = {1: "PASS", 0: "FAIL"}.get(r["gates_passed"], "-")
        # Both deltas are on Eff (speed/mm2), the objective -- not on the
        # per-MHz column beside it.
        vs_parent = "-" if r["vs_parent"] is None else f"{r['vs_parent']:+.3f}%"
        vs_base = "-" if r["vs_baseline"] is None else f"{r['vs_baseline']:+.3f}%"
        print(f"| {r['name']} | {r['parent'] or '-'} | {r['status'] or '-'} | "
              f"{num(r['fmax_mhz'], '.2f')} | {num(r['area_mm2'], '.4f')} | "
              f"{num(r['embench_speed_score'], '.3f')} | "
              f"{num(r['embench_speed_score_per_mhz'], '.4f')} | "
              f"{num(r['eff_mm2'], '.6f')} | "
              f"{num(r['eff_per_mhz_mm2'], '.6f')} | "
              f"{vs_parent} | {vs_base} | {riscv} | {gates} |")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.path.join(DB_DIR, "perf_area_eff.db"))
    ap.add_argument("--baseline", default=BASELINE_BRANCH_NAME,
                    help="branch to use as the efficiency reference")
    ap.add_argument("--all", action="store_true",
                    help="also list branches that recorded no efficiency")
    args = ap.parse_args()

    if not Path(args.db).is_file():
        raise SystemExit(f"DB not found: {args.db}")
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    branches = fetch_branches(conn)
    by_id = {b["id"]: b for b in branches}

    base = next((b for b in branches if b["name"] == args.baseline), None)
    if base is None:
        raise SystemExit(f"baseline branch {args.baseline!r} not found in DB")

    rows = []
    for b in branches:
        if b["embench_speed_score_area_eff"] is None and not args.all:
            continue
        parent = by_id.get(b["parent_id"])
        rows.append({
            **b,
            "parent": parent["name"] if parent else None,
            "area_mm2": None if b["area"] is None else b["area"] / 1e6,
            "eff_mm2": None if b["embench_speed_score_area_eff"] is None else b["embench_speed_score_area_eff"] * 1e6,
            # Frequency cancels out of this one, so it isolates the per-cycle
            # half of a change from the synthesis-dependent fmax.
            "eff_per_mhz_mm2": (
                None if b["embench_speed_score_per_mhz"] is None or not b["area"]
                else b["embench_speed_score_per_mhz"] / b["area"] * 1e6),
            "vs_parent": pct_change(
                b["embench_speed_score_area_eff"], parent["embench_speed_score_area_eff"] if parent else None),
            "vs_baseline": (None if b is base
                            else pct_change(b["embench_speed_score_area_eff"], base["embench_speed_score_area_eff"])),
        })

    base_eff = None if base["embench_speed_score_area_eff"] is None else base["embench_speed_score_area_eff"] * 1e6
    base_area = None if base["area"] is None else base["area"] / 1e6
    print(f"DB: {args.db}")
    print(f"Baseline: {args.baseline}  (area={num(base_area, '.4f')} mm2, "
          f"fmax={num(base['fmax_mhz'], '.2f')} MHz, "
          f"IPC={num(base['mean_ipc'], '.6f')}, "
          f"eff={num(base_eff, '.6f')} speed/mm2)")
    print()
    format_table(rows)


if __name__ == "__main__":
    main()
