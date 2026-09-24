# improve_perf_area: baseline_area_v5_1
Parent branch: baseline_area_v4_1
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.444178; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.446032 | 1.444178 | -0.128% |
| total cell area (um2) | 6,409,226 | 6,105,832 | -4.734% |
| SRAM macro area (um2) | 1,515,490 | 1,588,098 | +4.791% |
| fmax (MHz) | 47.44 | 47.26 | -0.379% |
| embench speed/MHz | 2.223746 | 2.219955 | -0.170% |
| embench speed score | 105.495 | 104.915 | -0.549% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 16.459788 | 17.182764 | +4.392% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.225617 | 0.236524 | +4.834% |

Verdict: **IMPROVED +4.392% vs parent**

## Hard gates

- PASS perf_area_eff: 17.182764 speed/mm2 >= parent 16.459788 speed/mm2 (child fmax 47.26 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
