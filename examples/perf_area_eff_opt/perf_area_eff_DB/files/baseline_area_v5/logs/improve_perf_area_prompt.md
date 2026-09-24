Improve the performance-area efficiency of an implementation of the BOOM out-of-order processor core.

## Arguments

`MediumBoomV3Config` = `[config_name]`

**Target config:** if `MediumBoomV3Config` is provided and contains "Config", use it. Otherwise
`MediumBoomV3Config`. Your change must actually reach this config — a parameter
edited in a case-class default the config overrides changes nothing. Configs live
in `generators/chipyard/src/main/scala/config/`; this one's BOOM parameters come
from `chipyard`.

## Goal

Maximize **performance per area**:

    perf_area_eff = perf / total_cell_area

`perf` is the **Embench speed score**, so in full:

    perf_area_eff = embench_speed_score / total_cell_area

in units of speed/mm2. The speed score is Embench's own figure: per benchmark,
the reference platform's time over this design's time, geometric mean over all
19. Two properties of that definition shape everything below.

**Frequency is already inside it.** This design's time is `cycles / fmax`, so the
score is `fmax x geomean(reference_cycles / our_cycles)`. Losing 10% of fmax
costs 10% of the objective exactly as losing 10% of IPC would. There is no
separate frequency gate — a trade of frequency for area passes precisely when the
trade is worth it.

**The mean is geometric.** A 20% regression on one benchmark is not cancelled by
a 20% gain on another; the pair comes out behind.

**The parent design you are improving — branch `baseline_area_v4_1`:**

| metric | value |
|---|---|
| total cell area | 6,409,226 um2 |
| embench speed score | 105.495 |
| embench speed per MHz | 2.223746 |
| mean embench IPC | 1.446032 (reported, not the objective) |
| fmax | 47.44 MHz (tt_025C_1v80) |
| perf_area_eff (speed/mm2) | 16.459788 speed/mm2 |

### What earlier iterations already did

The lineage that produced the parent, plus the attempts rejected along the way.
The parent's code already contains every change in the lineage rows; what you
cannot see from the code is which of them worked and what was thrown away.

| branch | area mm2 | fmax MHz | IPC | speed/MHz | speed/mm2 | status | files this step touched |
|---|---|---|---|---|---|---|---|
| seed | 8.435 | 45.00 | 1.449806 | 2.229238 | 11.892713 | ok | -- |
| v1 | 7.372 | 39.51 | 1.449806 | 2.229238 | 11.947760 | ok | dcache.scala, mshrs.scala |
| v2 | 6.738 | 46.60 | 1.449806 | 2.229238 | 15.416671 | ok | issue-slot.scala |
| v3 | 6.548 | 47.88 | 1.446213 | 2.224019 | 16.263380 | ok | btb.scala, faubtb.scala |
| v4_1 | 6.409 | 47.44 | 1.446032 | 2.223746 | 16.459788 | ok | fdiv.scala |

Attempts from this lineage that were rejected or are alternatives (same starting point, different edit):

| branch | area mm2 | fmax MHz | IPC | speed/MHz | speed/mm2 | status | files this step touched |
|---|---|---|---|---|---|---|---|
| v4 | 6.189 | 47.10 | 1.380766 | 2.108380 | 16.044090 | gates_failed | -- |
| v5 | n/a | n/a | n/a | n/a | n/a | n/a | -- |

Use it to find structures already picked over (less left in them than their size
suggests), directions that failed and how, and large structures absent from every
row — usually where the unclaimed win is. Do not repeat a rejected edit unless
you can say concretely what you are doing differently.

### Two hard gates

Neither is negotiable. An edit that trips either is recorded as a failure
whatever else it achieved.

1. **`perf_area_eff` must not regress below the parent** — the design you are
   editing, whose numbers are in the table above. There is no credit for headroom
   an earlier iteration won. Frequency is a factor of the score, so this gate
   covers timing too.
2. **No new riscv-test failures**, measured against the **seed**, not the parent:
   correctness is a constraint, so a test an earlier iteration happened to fix is
   not your obligation. ISA-visible behavior, memory ordering, exception
   semantics and architectural register state must be preserved.
   (`rv64ui-p-ma_data` and `rv64ui-v-ma_data` already fail on the unmodified
   design — BOOM does not implement misaligned data accesses. Not your task.)

### Doing the arithmetic

The objective is a ratio, so estimate the *relative* change in each term:

    improves  <=>  (1 + dCycles') x (1 + dFmax/Fmax) / (1 + dArea/Area) > 1

where `dCycles'` rises when a benchmark takes fewer cycles.

- Remove 2.4% of area for a 1% cycle-count loss, fmax flat:
  `0.99 / 0.976 = 1.014`. **Win.**
- Add 1.2% of area for a 3% cycle-count gain: `1.03 / 1.012 = 1.018`. **Win** —
  this is a ratio, not an area budget; spend area when performance pays.
- Remove 7.1% of area at no cycle cost but 10% of fmax:
  `0.90 / 0.929 = 0.969`. **Loss.** A 5% frequency loss is exactly cancelled by a
  5% area saving; anything less is a net loss. Always price this term.

Take the absolute numbers those percentages correspond to from the parent's area
in the table above.

SRAM macros are the largest single blocks, so cache and predictor *geometry*
changes move both area and cycle counts a lot, while datapath tweaks mostly move
area a little.

## Approaches

The objective has exactly three factors:

    perf_area_eff  proportional to  (1 / cycles) x fmax / area

So there are three levers, and any change that moves one of them the right way
without giving back more on another is a win. Pick which lever you are pulling —
but estimate all three, because a change rarely moves only one.

### Fewer cycles

Better speculation and scheduling is the highest-leverage lever here, because a
better *algorithm* at the same area is free: a TAGE-style predictor reaching the
parent's accuracy in fewer bits, a differently-banked BTB, a cheaper RAS, a
prefetcher whose accuracy justifies its storage. Predictors live in
`generators/boom/src/main/scala/v3/ifu/` (`bpd*.scala`, `tage.scala`,
`btb.scala`, `bim.scala`, `loop.scala`, `ras.scala`). Mispredict cost is high on
a 10-stage out-of-order core, so accuracy changes show up clearly in the cycle
counts. Predictor tables are real SRAM, so check the area report before assuming
they are free.

Growing a structure also belongs here: more ROB entries, a deeper issue queue or
a larger cache buys cycles at an area cost. The objective is a ratio, not an area
budget, so this is legitimate whenever the cycles pay for the area.

### Less area

Same architecture, less logic. Narrow an over-wide mux, drop logic redundant
given an invariant, share a unit between paths that cannot be active in the same
cycle, strength-reduce arithmetic, encode a one-hot broadcast. These are usually
cycle-neutral, which makes them the cleanest wins, but also the smallest — target
them where the area report says the area actually is.

Then ask what each large structure's storage really costs. Flip-flops pay a cell
per bit plus the muxing to read and write them; memory macros are far denser but
constrain access (read latency, port count) and carry fixed overhead that small
memories cannot amortize. For each, ask what its access pattern actually requires
— how many simultaneous readers and writers, whether a read can wait a cycle,
whether a lookup must search every entry.

Then ask what the design carries at all: logic serving debug, tracing or
verification; optional features and generous defaults; values wider or more
redundant than their use requires; units dedicated and fully parallel for
operations the workloads rarely perform. The riscv-test gate decides what is
actually required.

Shrinking a structural parameter is the most predictable route and the easiest to
overdo. Parameters are in
`generators/boom/src/main/scala/v3/common/parameters.scala`: ROB entries,
issue-queue depths (`IQT_INT`, `IQT_MEM`, `IQT_FP`), physical register file
sizes, LDQ/STQ entries, fetch-buffer and FTQ depth, MSHR count, cache ways/sets.
Several are *superlinear* in area — a register file grows as entries x ports, an
issue queue's wakeup network as depth x issue width — so shrinking a wide
structure a little removes more than shrinking a narrow one a lot. Two hazards:
those same dimensions set the length of the wakeup and bypass paths, so a size
change moves frequency as well as area; and some parameters are coupled, with
BOOM asserting on the relationships at elaboration time, so an inconsistent set
fails the build rather than producing a design.

### Higher frequency

Frequency is a plain multiplier on the objective, so shortening the design's
worst path is worth exactly as much as removing the equivalent fraction of area —
and unlike area, it costs nothing in cycles when done right. This lever is only
available if you know where the worst path is, so start from the STA report:
find the endpoint family that owns the top paths, then read that structure's
Chisel for the logic between the startpoint register and the endpoint.

What usually helps: splitting a long combinational chain across a pipeline
register (costs a cycle of latency somewhere — price that against the frequency
gain), replacing a priority encoder or a wide OR-reduction over a queue with a
tree, narrowing a comparison that runs on more bits than it needs, or moving work
off the critical edge into a cycle where it is not urgent.

Remember that a path crossing into a structure is not necessarily that
structure's fault: the delay may be mostly in the logic feeding it.

---

## Tools

Two MCP tools, and they are the whole interface.

- **Do not use Ray or any other cluster mechanism** — no `import ray`, `ray` CLI,
  GCS/raylet gRPC, Ray/gRPC proxy env vars, or scheduling work on another node.
  Do not inspect or call the pipeline's actors or tasks.
- **Do not run synthesis, STA or CACTI yourself.** Only `perf_area_experiment`
  results count.
- **Stay on the build node:** the chipyard tree and `/tmp/improve_perf_area/`.
- **If a tool seems stuck, keep polling `synth_status`.** If it failed, say so in
  your final response. Do not work around it.

### `chipyard_bash`

Bash on the worker holding the BOOM checkout. Scala sources at
`/home/ray/chipyard/generators/boom/src/main/scala/v3/`; the parent design's
already-elaborated Verilog at `/home/ray/chipyard/preliminary-generated-src/`.

**Edit files in place with targeted commands (`sed -i`, `cat >>`), never by
writing a whole file back.** The pipeline detects your changes by diffing against
the baseline, so a rewritten file shows up as a change to everything in it.
Re-read each edited region with `sed -n` afterwards to confirm it landed.

### `perf_area_experiment`

Re-elaborates Chisel and synthesizes one sub-module, on your edited (child) or
the parent's unmodified RTL, reporting area and fmax per side. Minutes, against
roughly an hour of synthesis plus several hours of simulation for the full tile.

Start-then-poll, because a synchronous call would exceed the MCP HTTP timeout:

- **`rebuild_verilog()`** — re-runs `make verilog` with your edits. Call once
  after editing, before any `start_synth_child`. **This is also your compile
  check**: if it errors, your Chisel does not elaborate.
- **`list_modules()`** / **`list_modules_parent()`** — module names for the child
  and parent sides. The parent side needs no `rebuild_verilog` and is useful in
  Phase 1; diffing the two afterwards spots structural drift you introduced.
- **`start_synth_child(vlsi_top, timeout_seconds=5400)`** and
  **`start_synth_parent(...)`** — dispatch a sub-block synthesis + STA, returning
  a handle immediately. **Issue both in the same turn** so they run concurrently.
- **`synth_status(handle, max_wait_seconds=180)`** — poll, blocking up to
  `max_wait_seconds` (cap 240). Returns `status: running` with elapsed time, or
  the full summary. A handle polled to completion is dropped.

**Pick the smallest `vlsi_top` containing what you changed.** A register file
(~520,000 um2) takes about 1.5–2 min per side. **Never `BoomCore` or `BoomTile`**
— they exceed the timeout cap and return nothing at all.

**What an A/B does and does not tell you:**

- **The area delta is trustworthy**, and is the reason to run it: if the module
  shrank, the tile shrank by about that much.
- **The fmax is not usable as the tile's frequency.** The sub-block is
  synthesized alone with no input or output delay constraints, while the tile's
  worst paths *start outside* the module and end at a register inside it. Those
  paths get timed from the module's input port with zero external delay, so a
  sub-block's fmax is systematically optimistic about exactly the paths that
  matter. Use it only to compare the two sides against each other, as evidence
  about whether your edit lengthened a path *internal* to the module.
- **The tile's frequency evidence is the full-tile STA report**,
  `/tmp/improve_perf_area/sta_report.rpt`. If a structure you are touching appears in its worst paths,
  assume a frequency cost and price it; if it appears nowhere, assume 1.0.

### Chisel guidelines

1. `:=` for all connections. `<>` only when BOTH sides are `DecoupledIO`/`ValidIO`.
2. BOOM Bundles require implicit `Parameters`.
3. `when`/`.elsewhen`/`.otherwise` for hardware muxes; Scala `if` for
   elaboration-time gating.
4. `RegInit(value)` when a reset value is needed.
5. Preserve ALL original imports.
6. `:= DontCare` for unconnected Bundle fields.
7. A new module: `cat >` a new `.scala`, same package as related modules,
   extending `BoomModule` with `HasBoomCoreParameters`.

---

## Phase 1: Read the reports

Three reports, all on the chipyard node (paths and recipes at the end). Read all
three — each answers a different question.

1. **Area report** — *where is the area?* The denominator, and the only report
   that attributes it to structures. An edit to a module that is 0.3% of the
   design cannot move the objective however clever it is.
2. **IPC report** — *where is performance at stake?* The spread across embench
   is wide. A memory-bound benchmark barely notices a narrower issue queue; a
   branchy one is very sensitive to predictor accuracy.
3. **STA report** — *what would frequency cost?* Which structures own the worst
   paths. This is the only sound evidence for the frequency term.

Then read the generated Verilog and the Chisel for the structures you are
considering, and optionally `list_modules_parent()` to line up module names with
the area report for Phase 4.

## Phase 2: Plan

Pick **one** coherent change. One change whose effect can be attributed is worth
more than three whose effects are entangled — this loop runs many times, and a
result you cannot attribute teaches the next iteration nothing.

State before implementing:

- which lever it pulls (cycles, area or frequency), and why the reports
  point there;
- the expected area delta, with the area-report number supporting it;
- the expected cycle-count effect, and which benchmarks would show it (this is
  measured only after your session, so it has to be reasoned, not measured);
- the expected frequency effect, and whether the structure appears in the STA
  report's worst paths;
- the resulting `perf_area_eff` estimate as a ratio, with the frequency term
  stated explicitly even when you expect it to be 1.0.

Check it against the failure modes specific to this objective:

- **Removing logic can cost frequency.** Sharing a unit adds a mux; narrowing a
  structure can expose a previously-slack path.
- **Parameters are coupled.** Check the `require` statements near the one you are
  changing — an inconsistent set fails elaboration.
- **Some area is not yours to remove.** SRAM macros are generated by CACTI from
  cache and predictor *geometry*, so they do not respond to datapath edits.

## Phase 3: Implement

Implement with `chipyard_bash`, editing in place.

## Phase 4: Verify, then A/B

First by inspection: re-read each edited region with `sed -n`; confirm package
and imports are intact; for new IO ports, confirm the module and its parent have
matching connections; confirm the change reaches the target config.

Then measure — do not trust the edit until synthesis has confirmed what it did:

1. **`rebuild_verilog()`**. If it errors, your Chisel does not compile. Fix and
   repeat before going on.
2. **`list_modules()`** — pick the smallest `vlsi_top` containing your edit.
3. **`start_synth_child` and `start_synth_parent` in one turn**, then poll both
   with `synth_status` across turns until both complete.
4. **Compare.** `area_delta = child.area − parent.area` against your Phase 2
   estimate; a large miss means the structure was not what you thought. Read the
   fmax delta as evidence about paths *internal* to the module, not as the tile's
   frequency.
5. **Iterate** if the area missed your estimate, or if the A/B shows your edit
   lengthened an internal path in a module the STA report already lists among its
   worst. The parent side is fixed, so only the child needs re-synthesizing.

Do not finish until the A/B supports your plan, or you have established that it
cannot work. A well-documented negative result is a legitimate outcome and more
useful to the next iteration than a change you cannot explain.

---

## Final response

- the change, and which lever it pulls;
- the measured sub-block A/B: area and fmax on both sides;
- your `perf_area_eff` estimate with the ratio arithmetic shown;
- both gates: how you priced the frequency term and what the STA report says
  about the structure; and which riscv-tests are at risk and why;
- anything you tried that did not work, and what the A/B said about it.

---

# Reports

All on the chipyard build node, read with `chipyard_bash`. The STA report can be
hundreds of KB — **do not `cat` it whole.**

## Area report (Yosys) — `/tmp/improve_perf_area/area_report.txt`

- **Tile total:** `grep -A3 'Chip area for module' /tmp/improve_perf_area/area_report.txt | tail -20`
- **Per-module, largest first:**
  `grep 'Chip area for module' /tmp/improve_perf_area/area_report.txt | sort -t: -k2 -g -r | head -40`
- **Hierarchy (where the SRAM macros are counted):**
  `awk '/=== design hierarchy ===/,0' /tmp/improve_perf_area/area_report.txt | head -60`
- **One module's cell mix:** `awk '/module \\\\<name>/,/^$/' /tmp/improve_perf_area/area_report.txt`

Work top-down: only the modules at the top of that sorted list can move the
objective.

## IPC report — `/tmp/improve_perf_area/ipc_report.md`

Per-benchmark IPC for the parent, with the area and fmax headline. Small enough
to read whole: `cat /tmp/improve_perf_area/ipc_report.md`.

The objective is built from these benchmarks' *cycle counts*, not from the IPC
column: each is scored against a fixed reference platform and the 19 are combined
geometrically, so every benchmark counts equally regardless of length and a large
loss on any one cannot be averaged away. IPC is shown because it separates a
cycle-count change from a frequency change, which the objective alone does not.

## STA report (OpenSTA) — `/tmp/improve_perf_area/sta_report.rpt`

At `tt_025C_1v80` against a 20.0 ns target. The design does not close
at that target, so a violation is not by itself a problem — read it as a ranking.

- **Count paths:** `grep -c '^Startpoint' /tmp/improve_perf_area/sta_report.rpt`
- **Worst path and achievable period:**
  `grep -E 'slack|data arrival time' /tmp/improve_perf_area/sta_report.rpt | head -20`
- **Endpoints at a glance:**
  `grep -E '^(Startpoint|Endpoint)' /tmp/improve_perf_area/sta_report.rpt | head -60`
- **One path in full:** `awk '/^Startpoint/{n++} n==1' /tmp/improve_perf_area/sta_report.rpt`
- **Paths through a structure:**
  `grep -B3 -A1 '<module_or_signal_name>' /tmp/improve_perf_area/sta_report.rpt | head -40`

Cluster paths by endpoint family before concluding a structure is critical:
several paths ending in the same register class usually share one bottleneck.
Worst paths typically *start* in one module and *end* in another, so the
structure that owns a path is not always the one the endpoint names.
