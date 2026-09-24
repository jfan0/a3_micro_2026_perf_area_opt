# improve_perf_area: baseline_area_v15
Parent branch: baseline_area_v14
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.428116; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.428717 | 1.428116 | -0.042% |
| total cell area (um2) | 5,136,254 | 4,999,074 | -2.671% |
| SRAM macro area (um2) | 1,167,490 | 1,167,490 | +0.000% |
| fmax (MHz) | 48.17 | 43.48 | -9.736% |
| embench speed/MHz | 2.193479 | 2.192332 | -0.052% |
| embench speed score | 105.660 | 95.323 | -9.784% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 20.571389 | 19.068051 | -7.308% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.278163 | 0.285676 | +2.701% |

Verdict: **REGRESSED -7.308% vs parent**

## Hard gates

- FAIL perf_area_eff: 19.068051 speed/mm2 < best so far (v14) 20.571389 speed/mm2 -- Embench speed per area regressed (child fmax 43.48 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **FAILED** (recorded as status=gates_failed)
