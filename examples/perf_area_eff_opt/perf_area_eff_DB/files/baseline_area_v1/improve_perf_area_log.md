# improve_perf_area: baseline_area_v1
Parent branch: baseline
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.449806; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.449806 | 1.449806 | +0.000% |
| total cell area (um2) | 8,435,057 | 7,371,858 | -12.605% |
| SRAM macro area (um2) | 1,641,487 | 1,641,487 | +0.000% |
| fmax (MHz) | 45.0 | 39.51 | -12.200% |
| embench speed/MHz | 2.229238 | 2.229238 | +0.000% |
| embench speed score | 100.316 | 88.077 | -12.200% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 11.892713 | 11.947760 | +0.463% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.171879 | 0.196668 | +14.422% |

Verdict: **IMPROVED +0.463% vs parent**

## Hard gates

- PASS perf_area_eff: 11.947760 speed/mm2 >= parent 11.892713 speed/mm2 (child fmax 39.51 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
