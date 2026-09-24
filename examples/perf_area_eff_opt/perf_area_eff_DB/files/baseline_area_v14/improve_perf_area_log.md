# improve_perf_area: baseline_area_v14
Parent branch: baseline_area_v13
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.428717; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.432266 | 1.428717 | -0.248% |
| total cell area (um2) | 5,305,560 | 5,136,254 | -3.191% |
| SRAM macro area (um2) | 1,188,250 | 1,167,490 | -1.747% |
| fmax (MHz) | 48.17 | 48.17 | +0.000% |
| embench speed/MHz | 2.197645 | 2.193479 | -0.190% |
| embench speed score | 105.861 | 105.660 | -0.190% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 19.952759 | 20.571389 | +3.100% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.269956 | 0.278163 | +3.040% |

Verdict: **IMPROVED +3.100% vs parent**

## Hard gates

- PASS perf_area_eff: 20.571389 speed/mm2 > best so far (v13) 19.952759 speed/mm2 (child fmax 48.17 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
