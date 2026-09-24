# Parent design: measured performance, area and timing

## Headline

- mean embench IPC : 1.428116
- total cell area  : 4,999,156 um2 (Yosys, includes the CACTI SRAM macros)
- SRAM macro area  : 1,167,490 um2
- standard cells   : 3,831,666 um2
- fmax             : 48.17 MHz (tt_025C_1v80, OpenSTA)
- ipc_area_eff     : 0.285671 IPC/mm2

## Per-benchmark IPC

Sorted by IPC. The objective is built from the cycle counts, not this
column, so every benchmark counts equally regardless of its length.

| benchmark | IPC | ROI cycles | ROI instret |
|---|---|---|---|
| nettle-sha256 | 1.941558 | 2,375,029 | 4,611,257 |
| matmult-int | 1.939789 | 1,390,221 | 2,696,735 |
| nettle-aes | 1.936812 | 2,402,590 | 4,653,364 |
| md5sum | 1.865705 | 1,411,214 | 2,632,909 |
| edn | 1.835538 | 1,722,554 | 3,161,813 |
| depthconv | 1.784163 | 1,824,430 | 3,255,081 |
| picojpeg | 1.701336 | 1,669,397 | 2,840,206 |
| slre | 1.577570 | 1,735,276 | 2,737,520 |
| aha-mont64 | 1.553940 | 1,372,950 | 2,133,482 |
| crc32 | 1.535226 | 2,496,056 | 3,832,011 |
| wikisort | 1.456327 | 947,864 | 1,380,400 |
| tarfind | 1.381199 | 753,977 | 1,041,392 |
| huffbench | 1.107065 | 1,941,563 | 2,149,437 |
| sglib-combined | 1.074629 | 2,395,576 | 2,574,355 |
| qrduino | 1.056692 | 2,688,641 | 2,841,066 |
| ud | 1.000684 | 2,791,650 | 2,793,559 |
| statemate | 0.968157 | 1,678,524 | 1,625,074 |
| xgboost | 0.759571 | 2,312,552 | 1,756,547 |
| nsichneu | 0.658239 | 3,415,817 | 2,248,423 |
