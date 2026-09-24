# improve_perf_area: baseline_area_v7
Parent branch: baseline_area_v6_2
Build config: MediumBoomV3Config
BoomTile (parent): BoomTile
BoomTile (child):  BoomTile
Synthesis success: True; STA success: True
embench: 19/19 with IPC, mean IPC 1.37892; riscv-tests: 237/239 passed

## Objective

| metric | parent | child | delta |
|---|---|---|---|
| mean embench IPC | 1.444178 | 1.378920 | -4.519% |
| total cell area (um2) | 5,964,896 | 5,612,474 | -5.908% |
| SRAM macro area (um2) | 1,588,098 | 1,233,138 | -22.351% |
| fmax (MHz) | 46.24 | 38.77 | -16.155% |
| embench speed/MHz | 2.219955 | 2.104870 | -5.184% |
| embench speed score | 102.651 | 81.606 | -20.501% |
| embench_speed_score_area_eff (speed/mm2) -- gates | 17.209139 | 14.540079 | -15.510% |
| ipc_area_eff (IPC/mm2) -- recorded | 0.242113 | 0.245688 | +1.477% |

Verdict: **REGRESSED -15.510% vs parent**

## Hard gates

- FAIL perf_area_eff: 14.540079 speed/mm2 < parent 17.209139 speed/mm2 -- Embench speed per area regressed (child fmax 38.77 MHz)
- PASS riscv-tests: no regressions against the seed's 239 tests

Gates: **FAILED** (recorded as status=gates_failed)
