# improve_perf_area: baseline_area_v10
Parent branch: baseline_area_v9
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.432266; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.432266 | 1.432266 | +0.000% |
| total cell area (um2) | 5,475,768 | 5,481,536 | +0.105% |
| SRAM macro area (um2) | 1,188,250 | 1,188,250 | +0.000% |
| fmax (MHz) | 48.17 | 38.45 | -20.179% |
| embench speed/MHz | 2.197645 | 2.197645 | +0.000% |
| embench speed score | 105.861 | 84.499 | -20.179% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 19.332549 | 15.415286 | -20.263% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.261564 | 0.261289 | -0.105% |

Verdict: **REGRESSED -20.263% vs parent**

## Hard gates

- FAIL perf_area_eff: 15.415286 speed/mm2 < parent 19.332549 speed/mm2 -- Embench speed per area regressed (child fmax 38.45 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **FAILED** (recorded as status=gates_failed)
