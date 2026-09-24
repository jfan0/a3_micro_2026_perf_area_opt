# Parent design: measured performance, area and timing

## Headline

- mean embench IPC : 1.449806
- total cell area  : 6,738,322 um2 (Yosys, includes the CACTI SRAM macros)
- SRAM macro area  : 1,641,487 um2
- standard cells   : 5,096,835 um2
- fmax             : 46.6 MHz (tt_025C_1v80, OpenSTA)
- ipc_area_eff     : 0.215158 IPC/mm2

## Per-benchmark IPC

Sorted by IPC. The objective is built from the cycle counts, not this
column, so every benchmark counts equally regardless of its length.

| benchmark | IPC | ROI cycles | ROI instret |
|---|---|---|---|
| matmult-int | 1.965053 | 1,372,347 | 2,696,735 |
| nettle-aes | 1.964151 | 2,369,148 | 4,653,364 |
| nettle-sha256 | 1.946390 | 2,369,133 | 4,611,257 |
| md5sum | 1.871893 | 1,406,549 | 2,632,909 |
| edn | 1.846563 | 1,712,269 | 3,161,813 |
| depthconv | 1.800272 | 1,808,105 | 3,255,081 |
| picojpeg | 1.714952 | 1,656,143 | 2,840,206 |
| aha-mont64 | 1.625702 | 1,312,345 | 2,133,482 |
| slre | 1.595472 | 1,715,806 | 2,737,520 |
| crc32 | 1.552965 | 2,467,545 | 3,832,011 |
| wikisort | 1.473780 | 936,639 | 1,380,400 |
| tarfind | 1.382629 | 753,197 | 1,041,392 |
| huffbench | 1.113773 | 1,929,870 | 2,149,437 |
| statemate | 1.094085 | 1,485,327 | 1,625,074 |
| sglib-combined | 1.087232 | 2,367,807 | 2,574,355 |
| qrduino | 1.071962 | 2,650,341 | 2,841,066 |
| ud | 1.003869 | 2,782,792 | 2,793,559 |
| xgboost | 0.777344 | 2,259,679 | 1,756,547 |
| nsichneu | 0.658228 | 3,415,871 | 2,248,423 |
