# improve_perf_area: baseline_area_v6_2
Parent branch: baseline_area_v5_1
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.444178; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.444178 | 1.444178 | +0.000% |
| total cell area (um2) | 6,105,832 | 5,964,896 | -2.308% |
| SRAM macro area (um2) | 1,588,098 | 1,588,098 | +0.000% |
| fmax (MHz) | 47.26 | 46.24 | -2.158% |
| embench speed/MHz | 2.219955 | 2.219955 | +0.000% |
| embench speed score | 104.915 | 102.651 | -2.158% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 17.182764 | 17.209139 | +0.153% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.236524 | 0.242113 | +2.363% |

Verdict: **IMPROVED +0.153% vs parent**

## Hard gates

- PASS perf_area_eff: 17.209139 speed/mm2 >= parent 17.182764 speed/mm2 (child fmax 46.24 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
