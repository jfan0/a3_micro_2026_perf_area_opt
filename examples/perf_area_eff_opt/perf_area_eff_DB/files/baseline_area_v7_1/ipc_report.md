# Parent design: measured performance, area and timing

## Headline

- mean embench IPC : 1.444178
- total cell area  : 5,964,896 um2 (Yosys, includes the CACTI SRAM macros)
- SRAM macro area  : 1,588,098 um2
- standard cells   : 4,376,798 um2
- fmax             : 46.24 MHz (tt_025C_1v80, OpenSTA)
- ipc_area_eff     : 0.242113 IPC/mm2

## Per-benchmark IPC

Sorted by IPC. The objective is built from the cycle counts, not this
column, so every benchmark counts equally regardless of its length.

| benchmark | IPC | ROI cycles | ROI instret |
|---|---|---|---|
| matmult-int | 1.965053 | 1,372,347 | 2,696,735 |
| nettle-aes | 1.964131 | 2,369,172 | 4,653,364 |
| nettle-sha256 | 1.945905 | 2,369,723 | 4,611,257 |
| md5sum | 1.870725 | 1,407,427 | 2,632,909 |
| edn | 1.846950 | 1,711,910 | 3,161,813 |
| depthconv | 1.800272 | 1,808,105 | 3,255,081 |
| picojpeg | 1.713574 | 1,657,475 | 2,840,206 |
| slre | 1.597964 | 1,713,130 | 2,737,520 |
| aha-mont64 | 1.564458 | 1,363,720 | 2,133,482 |
| crc32 | 1.552964 | 2,467,546 | 3,832,011 |
| wikisort | 1.467374 | 940,728 | 1,380,400 |
| tarfind | 1.382128 | 753,470 | 1,041,392 |
| huffbench | 1.104597 | 1,945,901 | 2,149,437 |
| statemate | 1.094068 | 1,485,350 | 1,625,074 |
| sglib-combined | 1.076878 | 2,390,573 | 2,574,355 |
| qrduino | 1.056922 | 2,688,057 | 2,841,066 |
| ud | 1.000684 | 2,791,650 | 2,793,559 |
| xgboost | 0.776502 | 2,262,127 | 1,756,547 |
| nsichneu | 0.658229 | 3,415,869 | 2,248,423 |
