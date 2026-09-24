# improve_perf_area: baseline_area_v3
Parent branch: baseline_area_v2
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.446213; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.449806 | 1.446213 | -0.248% |
| total cell area (um2) | 6,738,322 | 6,547,595 | -2.830% |
| SRAM macro area (um2) | 1,641,487 | 1,515,490 | -7.676% |
| fmax (MHz) | 46.6 | 47.88 | +2.747% |
| embench speed/MHz | 2.229238 | 2.224019 | -0.234% |
| embench speed score | 103.882 | 106.486 | +2.506% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 15.416671 | 16.263380 | +5.492% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.215158 | 0.220877 | +2.658% |

Verdict: **IMPROVED +5.492% vs parent**

## Hard gates

- PASS perf_area_eff: 16.263380 speed/mm2 >= parent 15.416671 speed/mm2 (child fmax 47.88 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
