# Parent design: measured performance, area and timing

## Headline

- mean embench IPC : 1.432266
- total cell area  : 5,636,879 um2 (Yosys, includes the CACTI SRAM macros)
- SRAM macro area  : 1,233,138 um2
- standard cells   : 4,403,741 um2
- fmax             : 45.39 MHz (tt_025C_1v80, OpenSTA)
- ipc_area_eff     : 0.254088 IPC/mm2

## Per-benchmark IPC

Sorted by IPC. The objective is built from the cycle counts, not this
column, so every benchmark counts equally regardless of its length.

| benchmark | IPC | ROI cycles | ROI instret |
|---|---|---|---|
| matmult-int | 1.954384 | 1,379,839 | 2,696,735 |
| nettle-sha256 | 1.941558 | 2,375,029 | 4,611,257 |
| nettle-aes | 1.939261 | 2,399,555 | 4,653,364 |
| md5sum | 1.866581 | 1,410,552 | 2,632,909 |
| edn | 1.840812 | 1,717,619 | 3,161,813 |
| depthconv | 1.800256 | 1,808,121 | 3,255,081 |
| picojpeg | 1.710628 | 1,660,329 | 2,840,206 |
| slre | 1.579251 | 1,733,429 | 2,737,520 |
| aha-mont64 | 1.564458 | 1,363,720 | 2,133,482 |
| crc32 | 1.552964 | 2,467,546 | 3,832,011 |
| wikisort | 1.454798 | 948,860 | 1,380,400 |
| tarfind | 1.382759 | 753,126 | 1,041,392 |
| huffbench | 1.105247 | 1,944,757 | 2,149,437 |
| sglib-combined | 1.074994 | 2,394,762 | 2,574,355 |
| qrduino | 1.057715 | 2,686,041 | 2,841,066 |
| ud | 1.000684 | 2,791,650 | 2,793,559 |
| statemate | 0.970080 | 1,675,196 | 1,625,074 |
| xgboost | 0.758391 | 2,316,149 | 1,756,547 |
| nsichneu | 0.658239 | 3,415,817 | 2,248,423 |
