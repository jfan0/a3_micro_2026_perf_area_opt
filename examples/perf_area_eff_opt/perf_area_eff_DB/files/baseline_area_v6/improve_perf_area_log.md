# improve_perf_area: baseline_area_v6
Parent branch: baseline_area_v5_1
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.444178; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.444178 | 1.444178 | +0.000% |
| total cell area (um2) | 6,105,832 | 5,899,922 | -3.372% |
| SRAM macro area (um2) | 1,588,098 | 1,588,098 | +0.000% |
| fmax (MHz) | 47.26 | 44.82 | -5.163% |
| embench speed/MHz | 2.219955 | 2.219955 | +0.000% |
| embench speed score | 104.915 | 99.498 | -5.163% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 17.182764 | 16.864355 | -1.853% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.236524 | 0.244779 | +3.490% |

Verdict: **REGRESSED -1.853% vs parent**

## Hard gates

- FAIL perf_area_eff: 16.864355 speed/mm2 < parent 17.182764 speed/mm2 -- Embench speed per area regressed (child fmax 44.82 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **FAILED** (recorded as status=gates_failed)
