# improve_perf_area: baseline_area_v18
Parent branch: baseline_area_v17
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.428141; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.428141 | 1.428141 | +0.000% |
| total cell area (um2) | 4,993,670 | 4,995,020 | +0.027% |
| SRAM macro area (um2) | 1,167,490 | 1,167,490 | +0.000% |
| fmax (MHz) | 53.29 | 58.38 | +9.552% |
| embench speed/MHz | 2.192370 | 2.192370 | +0.000% |
| embench speed score | 116.831 | 127.991 | +9.552% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 23.395899 | 25.623634 | +9.522% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.285990 | 0.285913 | -0.027% |

Verdict: **IMPROVED +9.522% vs parent**

## Hard gates

- PASS perf_area_eff: 25.623634 speed/mm2 > best so far (v17) 23.395899 speed/mm2 (child fmax 58.38 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **PASSED** (recorded as status=ok)
