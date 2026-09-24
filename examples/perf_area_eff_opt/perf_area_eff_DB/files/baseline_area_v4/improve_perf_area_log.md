# improve_perf_area: baseline_area_v4
Parent branch: baseline_area_v3
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.380766; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.446213 | 1.380766 | -4.525% |
| total cell area (um2) | 6,547,595 | 6,189,488 | -5.469% |
| SRAM macro area (um2) | 1,515,490 | 1,160,531 | -23.422% |
| fmax (MHz) | 47.88 | 47.1 | -1.629% |
| embench speed/MHz | 2.224019 | 2.108380 | -5.200% |
| embench speed score | 106.486 | 99.305 | -6.744% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 16.263380 | 16.044090 | -1.348% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.220877 | 0.223082 | +0.999% |

Verdict: **REGRESSED -1.348% vs parent**

## Hard gates

- FAIL perf_area_eff: 16.044090 speed/mm2 < parent 16.263380 speed/mm2 -- Embench speed per area regressed (child fmax 47.1 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **FAILED** (recorded as status=gates_failed)
