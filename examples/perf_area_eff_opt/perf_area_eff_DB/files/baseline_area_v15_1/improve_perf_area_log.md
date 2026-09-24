# improve_perf_area: baseline_area_v15_1
Parent branch: baseline_area_v14
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.428717; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.428717 | 1.428717 | +0.000% |
| total cell area (um2) | 5,136,254 | 5,065,285 | -1.382% |
| SRAM macro area (um2) | 1,167,490 | 1,167,490 | +0.000% |
| fmax (MHz) | 48.17 | 39.81 | -17.355% |
| embench speed/MHz | 2.193479 | 2.193479 | +0.000% |
| embench speed score | 105.660 | 87.322 | -17.355% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 20.571389 | 17.239386 | -16.197% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.278163 | 0.282061 | +1.401% |

Verdict: **REGRESSED -16.197% vs parent**

## Hard gates

- FAIL perf_area_eff: 17.239386 speed/mm2 < best so far (v14) 20.571389 speed/mm2 -- Embench speed per area regressed (child fmax 39.81 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **FAILED** (recorded as status=gates_failed)
