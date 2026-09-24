# improve_perf_area: baseline_area_v4_1
Parent branch: baseline_area_v3
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.446032; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.446213 | 1.446032 | -0.013% |
| total cell area (um2) | 6,547,595 | 6,409,226 | -2.113% |
| SRAM macro area (um2) | 1,515,490 | 1,515,490 | +0.000% |
| fmax (MHz) | 47.88 | 47.44 | -0.919% |
| embench speed/MHz | 2.224019 | 2.223746 | -0.012% |
| embench speed score | 106.486 | 105.495 | -0.931% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 16.263380 | 16.459788 | +1.208% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.220877 | 0.225617 | +2.146% |

Verdict: **IMPROVED +1.208% vs parent**

## Hard gates

- PASS perf_area_eff: 16.459788 speed/mm2 >= parent 16.263380 speed/mm2 (child fmax 47.44 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
