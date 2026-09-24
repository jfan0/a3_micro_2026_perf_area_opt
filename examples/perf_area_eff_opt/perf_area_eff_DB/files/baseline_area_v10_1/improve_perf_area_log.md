# improve_perf_area: baseline_area_v10_1
Parent branch: baseline_area_v9
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.432191; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.432266 | 1.432191 | -0.005% |
| total cell area (um2) | 5,475,768 | 5,495,497 | +0.360% |
| SRAM macro area (um2) | 1,188,250 | 1,188,250 | +0.000% |
| fmax (MHz) | 48.17 | 39.4 | -18.206% |
| embench speed/MHz | 2.197645 | 2.197531 | -0.005% |
| embench speed score | 105.861 | 86.583 | -18.211% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 19.332549 | 15.755212 | -18.504% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.261564 | 0.260612 | -0.364% |

Verdict: **REGRESSED -18.504% vs parent**

## Hard gates

- FAIL perf_area_eff: 15.755212 speed/mm2 < parent 19.332549 speed/mm2 -- Embench speed per area regressed (child fmax 39.4 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **FAILED** (recorded as status=gates_failed)
