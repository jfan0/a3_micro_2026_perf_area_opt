Improve the performance-area efficiency of an implementation of the BOOM out-of-order processor core.

## Target config

`MediumBoomV3Config`.

Check that your edit reaches it. BOOM's parameters have defaults in
`parameters.scala`, and the config sets its own values over them in
`config-mixins.scala`. Change a default there that the config already sets and
nothing happens — change it in the mixin instead.

Configs live in `generators/chipyard/src/main/scala/config/`; this one's BOOM
parameters come from `chipyard`.

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

**The parent design you are improving — branch `baseline_area_v10`:**

| metric | value |
|---|---|
| total cell area | 5,481,536 um2 |
| embench speed score | 84.499 |
| embench speed per MHz | 2.197645 |
| mean embench IPC | 1.432266 (reported, not the objective) |
| fmax | 38.45 MHz (tt_025C_1v80) |
| perf_area_eff (speed/mm2) | 15.415286 speed/mm2 |

### What earlier iterations already did

The lineage that produced the parent, plus the attempts rejected along the way.
The parent's code already contains every change in the lineage rows; what you
cannot see from the code is which of them worked and what was thrown away. The
hunk behind each row is under **Earlier edits** at the end of this document.

| branch | built on | area mm2 | fmax MHz | IPC | speed/MHz | speed/mm2 | status | files this step touched |
|---|---|---|---|---|---|---|---|---|
| seed | -- | 8.435 | 45.00 | 1.449806 | 2.229238 | 11.892713 | ok | -- |
| v1 | seed | 7.372 | 39.51 | 1.449806 | 2.229238 | 11.947760 | ok | dcache.scala, mshrs.scala |
| v2 | v1 | 6.738 | 46.60 | 1.449806 | 2.229238 | 15.416671 | ok | issue-slot.scala |
| v3 | v2 | 6.548 | 47.88 | 1.446213 | 2.224019 | 16.263380 | ok | btb.scala, faubtb.scala |
| v4_1 | v3 | 6.409 | 47.44 | 1.446032 | 2.223746 | 16.459788 | ok | fdiv.scala |
| v5_1 | v4_1 | 6.106 | 47.26 | 1.444178 | 2.219955 | 17.182764 | ok | tage.scala |
| v6_2 | v5_1 | 5.965 | 46.24 | 1.444178 | 2.219955 | 17.209139 | ok | config-mixins.scala, execution-unit.scala |
| v7_1 | v6_2 | 5.637 | 45.39 | 1.432266 | 2.197645 | 17.696157 | ok | -- |
| v8 | v7_1 | 5.473 | 46.79 | 1.432266 | 2.197645 | 18.786882 | ok | -- |
| v9 | v8 | 5.476 | 48.17 | 1.432266 | 2.197645 | 19.332549 | ok | core.scala, regfile.scala |
| v10 | v9 | 5.482 | 38.45 | 1.432266 | 2.197645 | 15.415286 | gates_failed | fpu.scala |

Edits off the lineage -- rejected attempts, and alternatives tried from a different starting point. Read `built on`: these do not all branch from the same place, so each row's deltas are against its own parent, not against yours.

| branch | built on | area mm2 | fmax MHz | IPC | speed/MHz | speed/mm2 | status | files this step touched |
|---|---|---|---|---|---|---|---|---|
| v10_1 | v9 | 5.495 | 39.40 | 1.432191 | 2.197531 | 15.755212 | gates_failed | fpu.scala |
| v10_synth_only_flatten | v10 | 4.818 | 47.91 | n/a | n/a | n/a | ok | -- |
| v11 | v10 | n/a | n/a | n/a | n/a | n/a | n/a | -- |

Re-measurements: the same RTL synthesized again, no edit and no simulation, so they carry no cycle counts and no objective.

| branch | built on | area mm2 | fmax MHz | IPC | speed/MHz | speed/mm2 | status | files this step touched |
|---|---|---|---|---|---|---|---|---|
| v10_synth_only | v10 | 5.482 | 38.45 | n/a | n/a | n/a | ok | -- |

The edit behind each row is at the end of this document.

Use it to find structures already picked over (less left in them than their size
suggests), directions that failed and how, and large structures absent from every
row — usually where the unclaimed win is.

**For a rejected edit, find which factor it lost on.** `speed/mm2` is
`(1/cycles) x fmax / area`, so a drop in it names no culprit. The **Earlier
edits** section at the end gives each edit's three deltas beside its hunk.

For an edit that was after area, look at its area delta first. If the area came
down, the edit did find real area to remove — the structure was the right
target, and what failed was how the edit was written. Go back into that same
structure and write it differently.

Lost on cycles: narrow the stall it added — block the one requester that
conflicts, in the cycle it conflicts.

Lost on frequency: look up the structure the edit touched in the STA report. If
it owns one of the worst paths, the loss is yours — shorten that path, or
pipeline it. If it does not appear in the report at all, the loss did not come
from the edit. Area and frequency move largely independently here, so do not
redesign the edit to chase it.

If the area did not move, there is no area to take there — do not send another
area edit into that structure. It can still be the right place for a cycles or a
frequency edit; those are separate levers.

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

**Check which levers the history has actually pulled before you pick.** The
branch names all say `area` and the earlier edits may all be area cuts, but that
is what previous iterations happened to try, not a finding that the other two
levers are spent. A lever nobody has pulled yet is where the headroom is: the
cycle counts in the IPC report and the worst paths in the STA report are as
unclaimed as any structure missing from the history.

### Fewer cycles

The highest-leverage lever, and the one you get no feedback on:
`perf_area_experiment` returns area and fmax in minutes, cycle counts only after
your session has ended. That asymmetry is not evidence that area is the better
target. It means a cycle argument has to be reasoned from the reports instead of
measured — not that it is worth less.

**Read the IPC report as a spread, not a mean.** Look up this config's
`decodeWidth`: that is the ceiling, and a benchmark near it is already issuing
as fast as the machine can and has nothing left to win. Everything the objective
can still take is at the bottom of that list. Find what the slowest benchmarks
have in common — on integer workloads that is usually branchy control flow and
pointer chasing rather than arithmetic — and go after the structure serving
whatever they wait on.

**Speculation.** A better *algorithm* at the same area is free: a TAGE-style
predictor reaching the parent's accuracy in fewer bits, a differently-banked
BTB, a cheaper RAS, a prefetcher whose accuracy justifies its storage.
Predictors live in `generators/boom/src/main/scala/v3/ifu/` (`bpd*.scala`,
`tage.scala`, `btb.scala`, `bim.scala`, `loop.scala`, `ras.scala`). Mispredict
cost is high on a 10-stage out-of-order core, so accuracy changes show up
clearly in the cycle counts. Predictor tables are real SRAM, so check the area
report before assuming they are free.

**The memory path.** A miss costs only what it blocks. `nMSHRs` bounds how many
misses can be outstanding, so a low count serializes misses that the program
issued in parallel; the LDQ/STQ search, store-to-load forwarding and the D$
replay path decide how long a load waits when it cannot be served at once. These
are in `generators/boom/src/main/scala/v3/lsu/`.

**Capacity stalls.** ROB entries, issue-queue depths, physical registers,
LDQ/STQ, fetch buffer and FTQ: whichever fills first stops dispatch, and the
rest are oversized until it does. Growing the binding one buys cycles at an area
cost, which this objective allows whenever the cycles pay — it is a ratio, not
an area budget.

**Operation latency.** A unit's latency lands in the cycle count even where its
area does not, so check which units the workload actually exercises. Embench is
integer-only: nothing done to the FP pipeline moves these cycle counts at all,
which cuts both ways — an FP change cannot win here, and an FP regression cannot
be seen here either.

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
- the expected cycle-count effect, with the IPC report's per-benchmark spread
  supporting it: which benchmarks would move and why (this is measured only
  after your session, so it has to be reasoned, not measured);
- the expected frequency effect, and whether the structure appears in the STA
  report's worst paths;
- the resulting `perf_area_eff` estimate as a ratio. Write all three factors,
  including `(1 + dFmax/Fmax)` when you expect it to be exactly 1 — a factor you
  leave out is an assumption you never checked, and frequency is the one these
  edits lose on;
- if an earlier edit already failed in this structure: the factor it lost, and
  the line of your version that changes that factor — a different file, or the
  same mechanism written more carefully, is not a different implementation.

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

---

# Earlier edits

Each branch's own hunk, on top of its parent -- not the cumulative diff, which for the lineage is already in the checkout you are editing. `area`/`cycles`/`fmax` after the status say which factor the edit moved (`cycles` in the speed sense: + is faster).

A rejected edit is not automatically a dead direction. Read its hunk and its three factors before avoiding it: an area win cancelled by a cycle loss is an implementation to fix, not a structure to leave alone, and it reads the same in the table as a plain regression.

### v1 (ok, on seed) -- area -12.6%  cycles +0.0%  fmax -12.2%

```diff
diff --git a/src/main/scala/v3/lsu/dcache.scala b/src/main/scala/v3/lsu/dcache.scala
index 1c35493a..b19350ff 100644
--- a/src/main/scala/v3/lsu/dcache.scala
+++ b/src/main/scala/v3/lsu/dcache.scala
@@ -576,10 +576,33 @@ class BoomNonBlockingDCacheModule(outer: BoomNonBlockingDCache) extends LazyModu
   mshrs.io.prefetch.ready := metaReadArb.io.in(5).ready
   // Prefetch does not need to read data array
 
+  // ------------
+  // Incoming LSU requests
+  // The D$ pipeline itself only ever reads mem_cmd/mem_size/mem_signed/uses_ldq/
+  // uses_stq/br_mask off a request's uop, and the only other uop fields the LSU
+  // reads back off io.lsu.resp/io.lsu.nack are ldq_idx/stq_idx/is_amo. Carrying the
+  // rest of the MicroOp through s0/s1/s2_req, the MSHRs and the MSHR replay queue is
+  // dead storage, so narrow it at the pipeline's entry point.
+  val lsu_req = Wire(Vec(memWidth, new BoomDCacheReq))
+  for (w <- 0 until memWidth) {
+    val req_uop = io.lsu.req.bits(w).bits.uop
+    lsu_req(w)                := io.lsu.req.bits(w).bits
+    lsu_req(w).uop            := 0.U.asTypeOf(new MicroOp)
+    lsu_req(w).uop.br_mask    := req_uop.br_mask
+    lsu_req(w).uop.mem_cmd    := req_uop.mem_cmd
+    lsu_req(w).uop.mem_size   := req_uop.mem_size
+    lsu_req(w).uop.mem_signed := req_uop.mem_signed
+    lsu_req(w).uop.uses_ldq   := req_uop.uses_ldq
+    lsu_req(w).uop.uses_stq   := req_uop.uses_stq
+    lsu_req(w).uop.ldq_idx    := req_uop.ldq_idx
+    lsu_req(w).uop.stq_idx    := req_uop.stq_idx
+    lsu_req(w).uop.is_amo     := req_uop.is_amo
+  }
+
   val s0_valid = Mux(io.lsu.req.fire, VecInit(io.lsu.req.bits.map(_.valid)),
                  Mux(mshrs.io.replay.fire || wb_fire || prober_fire || prefetch_fire || mshrs.io.meta_read.fire,
                                         VecInit(1.U(memWidth.W).asBools), VecInit(0.U(memWidth.W).asBools)))
-  val s0_req   = Mux(io.lsu.req.fire        , VecInit(io.lsu.req.bits.map(_.bits)),
+  val s0_req   = Mux(io.lsu.req.fire        , lsu_req,
                  Mux(wb_fire                  , wb_req,
                  Mux(prober_fire              , prober_req,
                  Mux(prefetch_fire            , prefetch_req,
diff --git a/src/main/scala/v3/lsu/mshrs.scala b/src/main/scala/v3/lsu/mshrs.scala
index ae5e4c52..53d743ff 100644
--- a/src/main/scala/v3/lsu/mshrs.scala
+++ b/src/main/scala/v3/lsu/mshrs.scala
@@ -134,6 +134,23 @@ class BoomMSHR(implicit edge: TLEdgeOut, p: Parameters) extends BoomModule()(p)
 
   rpq.io.enq.valid := ((io.req_pri_val && io.req_pri_rdy) || (io.req_sec_val && io.req_sec_rdy)) && !isPrefetch(io.req.uop.mem_cmd)
   rpq.io.enq.bits  := io.req
+  // The RPQ only has to remember the few uop fields that the D$ pipeline and the
+  // LSU actually consume off a replay/response: mem_cmd/mem_size/mem_signed and
+  // uses_ldq/uses_stq/br_mask are read inside dcache.scala + mshrs.scala, and
+  // ldq_idx/stq_idx/is_amo are the only other fields the LSU reads off
+  // io.dmem.resp/nack. Keeping the whole MicroOp here costs ~400 flops/entry and
+  // also keeps the rest of the uop artificially alive around the
+  // rpq -> replay -> s0/s1/s2_req -> mshrs.io.req -> rpq register ring.
+  rpq.io.enq.bits.uop := 0.U.asTypeOf(new MicroOp)
+  rpq.io.enq.bits.uop.br_mask    := io.req.uop.br_mask
+  rpq.io.enq.bits.uop.mem_cmd    := io.req.uop.mem_cmd
+  rpq.io.enq.bits.uop.mem_size   := io.req.uop.mem_size
+  rpq.io.enq.bits.uop.mem_signed := io.req.uop.mem_signed
+  rpq.io.enq.bits.uop.uses_ldq   := io.req.uop.uses_ldq
+  rpq.io.enq.bits.uop.uses_stq   := io.req.uop.uses_stq
+  rpq.io.enq.bits.uop.ldq_idx    := io.req.uop.ldq_idx
+  rpq.io.enq.bits.uop.stq_idx    := io.req.uop.stq_idx
+  rpq.io.enq.bits.uop.is_amo     := io.req.uop.is_amo
   rpq.io.deq.ready := false.B
```

### v2 (ok, on v1) -- area -8.6%  cycles +0.0%  fmax +17.9%

```diff
diff --git a/src/main/scala/v3/exu/issue-units/issue-slot.scala b/src/main/scala/v3/exu/issue-units/issue-slot.scala
index 40cb5ae6..30fe45eb 100644
--- a/src/main/scala/v3/exu/issue-units/issue-slot.scala
+++ b/src/main/scala/v3/exu/issue-units/issue-slot.scala
@@ -292,4 +292,51 @@ class IssueSlot(val numWakeupPorts: Int)(implicit p: Parameters)
   io.debug.p3 := p3
   io.debug.ppred := ppred
   io.debug.state := state
+
+  // The fields below are architecturally dead downstream of issue: they are read
+  // only on the dispatch->ROB/LSU path (commit-log/trace, exception reporting,
+  // rename rollback) or upstream of rename.  IssueSlot is a Module, so its uop
+  // output ports keep them alive and every slot burns a flop per bit carrying
+  // them across the issue window.  Tie them off so the storage, the collapsing
+  // shift muxes and the issue-select muxes for them all disappear.
+  //   inst        : only read by DecodeUnit (and RoCC, not present)
+  //   debug_inst  : only rob.io.commit.uops / rob_debug_inst_mem (enq-side copy)
+  //   debug_pc    : only rob.io.commit.uops (commit-log + trace)
+  //   exc_cause   : ROB takes it from io.enq_uops, or overwrites it with
+  //                 new_xcpt.cause for the lxcpt/csr_replay path
+  //   stale_pdst  : rename + ROB commit (enq-side copy)
+  //   ldst,lrs*   : rename map/busy tables only
+  //   debug_tsrc  : no readers
+  //   xcpt_*_if, bp_*_if : folded into exception/exc_cause by DecodeUnit
+  io.uop.inst               := 0.U
+  io.uop.debug_inst         := 0.U
+  io.uop.debug_pc           := 0.U
+  io.uop.exc_cause          := 0.U
+  io.uop.stale_pdst         := 0.U
+  io.uop.ldst               := 0.U
+  io.uop.lrs1               := 0.U
+  io.uop.lrs2               := 0.U
+  io.uop.lrs3               := 0.U
+  io.uop.debug_tsrc         := 0.U
+  io.uop.xcpt_pf_if         := false.B
+  io.uop.xcpt_ae_if         := false.B
+  io.uop.xcpt_ma_if         := false.B
+  io.uop.bp_debug_if        := false.B
+  io.uop.bp_xcpt_if         := false.B
+
+  io.out_uop.inst           := 0.U
+  io.out_uop.debug_inst     := 0.U
+  io.out_uop.debug_pc       := 0.U
+  io.out_uop.exc_cause      := 0.U
+  io.out_uop.stale_pdst     := 0.U
+  io.out_uop.ldst           := 0.U
+  io.out_uop.lrs1           := 0.U
+  io.out_uop.lrs2           := 0.U
+  io.out_uop.lrs3           := 0.U
+  io.out_uop.debug_tsrc     := 0.U
+  io.out_uop.xcpt_pf_if     := false.B
+  io.out_uop.xcpt_ae_if     := false.B
+  io.out_uop.xcpt_ma_if     := false.B
+  io.out_uop.bp_debug_if    := false.B
+  io.out_uop.bp_xcpt_if     := false.B
 }
```

### v3 (ok, on v2) -- area -2.8%  cycles -0.2%  fmax +2.7%

```diff
diff --git a/src/main/scala/v3/ifu/bpd/btb.scala b/src/main/scala/v3/ifu/bpd/btb.scala
index 367cbe3e..12918eb7 100644
--- a/src/main/scala/v3/ifu/bpd/btb.scala
+++ b/src/main/scala/v3/ifu/bpd/btb.scala
@@ -24,7 +24,11 @@ class BTBBranchPredictorBank(params: BoomBTBParams = BoomBTBParams())(implicit p
 {
   override val nSets         = params.nSets
   override val nWays         = params.nWays
-  val tagSz         = vaddrBitsExtended - log2Ceil(nSets) - log2Ceil(fetchWidth) - 1
+  // Tag only has to disambiguate PCs the program actually contains, not the whole
+  // 40-bit VA: with the 7-bit index (pc[9:3]) 9 real tag bits cover pc[18:3], a 512KB
+  // window.  The MSB is forced to 1 so an all-zero tag stays "invalid" for the
+  // btb_mispredicts fast-repair path below, which is what the full-width tag gave for free.
+  val tagSz         = 10
   val offsetSz      = params.offsetSz
   val extendedNSets = params.extendedNSets
 
@@ -73,7 +77,7 @@ class BTBBranchPredictorBank(params: BoomBTBParams = BoomBTBParams())(implicit p
   val s1_req_rbtb  = VecInit(btb.map { b => VecInit(b.read(s0_idx , s0_valid).map(_.asTypeOf(new BTBEntry))) })
   val s1_req_rmeta = VecInit(meta.map { m => VecInit(m.read(s0_idx, s0_valid).map(_.asTypeOf(new BTBMeta))) })
   val s1_req_rebtb = ebtb.read(s0_idx, s0_valid)
-  val s1_req_tag   = s1_idx >> log2Ceil(nSets)
+  val s1_req_tag   = Cat(1.U(1.W), (s1_idx >> log2Ceil(nSets))(tagSz-2,0))
 
   val s1_resp   = Wire(Vec(bankWidth, Valid(UInt(vaddrBitsExtended.W))))
   val s1_is_br  = Wire(Vec(bankWidth, Bool()))
@@ -159,7 +163,7 @@ class BTBBranchPredictorBank(params: BoomBTBParams = BoomBTBParams())(implicit p
   val s1_update_wmeta_data = Wire(Vec(bankWidth, new BTBMeta))
 
   for (w <- 0 until bankWidth) {
-    s1_update_wmeta_data(w).tag     := Mux(s1_update.bits.btb_mispredicts(w), 0.U, s1_update_idx >> log2Ceil(nSets))
+    s1_update_wmeta_data(w).tag     := Mux(s1_update.bits.btb_mispredicts(w), 0.U, Cat(1.U(1.W), (s1_update_idx >> log2Ceil(nSets))(tagSz-2,0)))
     s1_update_wmeta_data(w).is_br   := s1_update.bits.br_mask(w)
   }
 
diff --git a/src/main/scala/v3/ifu/bpd/faubtb.scala b/src/main/scala/v3/ifu/bpd/faubtb.scala
index 85f31484..a3958811 100644
--- a/src/main/scala/v3/ifu/bpd/faubtb.scala
+++ b/src/main/scala/v3/ifu/bpd/faubtb.scala
@@ -21,7 +21,11 @@ case class BoomFAMicroBTBParams(
 class FAMicroBTBBranchPredictorBank(params: BoomFAMicroBTBParams = BoomFAMicroBTBParams())(implicit p: Parameters) extends BranchPredictorBank()(p)
 {
   override val nWays         = params.nWays
-  val tagSz         = vaddrBitsExtended - log2Ceil(fetchWidth) - 1
+  // Fully associative, so the tag carries the whole fetch index.  15 real bits cover
+  // pc[17:3] (a 256KB window), which is more than any of the workloads text spans; the
+  // MSB is forced to 1 so the RegInit(0) reset state can never alias a real PC (and so
+  // the uninitialized btb offsets are never read before being written).
+  val tagSz         = 16
   val offsetSz      = params.offsetSz
   val nWrBypassEntries = 2
 
@@ -59,7 +63,7 @@ class FAMicroBTBBranchPredictorBank(params: BoomFAMicroBTBParams = BoomFAMicroBT
 
   val mems = Nil
 
-  val s1_req_tag   = s1_idx
+  val s1_req_tag   = Cat(1.U(1.W), s1_idx(tagSz-2,0))
 
 
   val s1_resp   = Wire(Vec(bankWidth, Valid(UInt(vaddrBitsExtended.W))))
@@ -140,7 +144,7 @@ class FAMicroBTBBranchPredictorBank(params: BoomFAMicroBTBParams = BoomFAMicroBT
         (s1_update.bits.cfi_taken || s1_update.bits.cfi_is_jal))
 
       meta(s1_update_write_way)(w).is_br := s1_update.bits.br_mask(w)
-      meta(s1_update_write_way)(w).tag   := s1_update_idx
+      meta(s1_update_write_way)(w).tag   := Cat(1.U(1.W), s1_update_idx(tagSz-2,0))
       meta(s1_update_write_way)(w).ctr   := Mux(!s1_update_meta.hits(w),
         Mux(was_taken, 3.U, 0.U),
         bimWrite(meta(s1_update_write_way)(w).ctr, was_taken)
```

### v4_1 (ok, on v3) -- area -2.1%  cycles -0.0%  fmax -0.9%

```diff
diff --git a/src/main/scala/v3/exu/execution-units/fdiv.scala b/src/main/scala/v3/exu/execution-units/fdiv.scala
index 00bfb743..46eae3e5 100644
--- a/src/main/scala/v3/exu/execution-units/fdiv.scala
+++ b/src/main/scala/v3/exu/execution-units/fdiv.scala
@@ -140,7 +140,7 @@ class FDivSqrtUnit(implicit p: Parameters)
   //-----------
   // fdiv/fsqrt
 
-  val divsqrt = Module(new hardfloat.DivSqrtRecF64)
+  val divsqrt = Module(new hardfloat.DivSqrtRecFN_small(11, 53, 0))
 
   val r_divsqrt_val = RegInit(false.B)  // inflight uop?
   val r_divsqrt_killed = Reg(Bool())           // has inflight uop been killed?
@@ -156,13 +156,13 @@ class FDivSqrtUnit(implicit p: Parameters)
     !r_divsqrt_val &&
     output_buffer_available
 
-  val divsqrt_ready = Mux(divsqrt.io.sqrtOp, divsqrt.io.inReady_sqrt, divsqrt.io.inReady_div)
+  val divsqrt_ready = divsqrt.io.inReady
   divsqrt.io.inValid := may_fire_input // must be setup early
   divsqrt.io.sqrtOp := r_buffer_fin.sqrt
   divsqrt.io.a := r_buffer_fin.in1
   divsqrt.io.b := Mux(divsqrt.io.sqrtOp, r_buffer_fin.in1, r_buffer_fin.in2)
   divsqrt.io.roundingMode := r_buffer_fin.rm
-  divsqrt.io.detectTininess := DontCare
+  divsqrt.io.detectTininess := hardfloat.consts.tininess_afterRounding
 
   r_divsqrt_killed := r_divsqrt_killed || IsKilledByBranch(io.brupdate, r_divsqrt_uop) || io.req.bits.kill
   r_divsqrt_uop.br_mask := GetNewBrMask(io.brupdate, r_divsqrt_uop)
```

### v5_1 (ok, on v4_1) -- area -4.7%  cycles -0.2%  fmax -0.4%

```diff
diff --git a/src/main/scala/v3/ifu/bpd/tage.scala b/src/main/scala/v3/ifu/bpd/tage.scala
index 39ef8583..74130213 100644
--- a/src/main/scala/v3/ifu/bpd/tage.scala
+++ b/src/main/scala/v3/ifu/bpd/tage.scala
@@ -86,8 +86,12 @@ class TageTable(val nRows: Int, val tagSz: Int, val histLength: Int, val uBitPer
 
   val (s1_hashed_idx, s1_tag) = compute_tag_and_hash(fetchIdx(io.f1_req_pc), io.f1_req_ghist)
 
-  val hi_us  = SyncReadMem(nRows, Vec(bankWidth, Bool()))
-  val lo_us  = SyncReadMem(nRows, Vec(bankWidth, Bool()))
+  // The merged useful-counter array only needs 2 bits per entry, but CACTI
+  // refuses to compile a macro below 2048 bits (128x8 fails, 256x8 works), and
+  // a rejected macro falls back to flip-flops at ~46 um2/bit. Pad the entry so
+  // the array is always large enough to become a real SRAM macro.
+  val uSz    = Seq(2, 4, 8).find(w => nRows * bankWidth * w >= 2048).get
+  val tage_us = SyncReadMem(nRows, Vec(bankWidth, UInt(uSz.W)))
   val table  = SyncReadMem(nRows, Vec(bankWidth, UInt(tageEntrySz.W)))
 
   val mems = Seq((f"tage_l$histLength", nRows, bankWidth * tageEntrySz))
@@ -95,14 +99,13 @@ class TageTable(val nRows: Int, val tagSz: Int, val histLength: Int, val uBitPer
   val s2_tag       = RegNext(s1_tag)
 
   val s2_req_rtage = VecInit(table.read(s1_hashed_idx, io.f1_req_valid).map(_.asTypeOf(new TageEntry)))
-  val s2_req_rhius = hi_us.read(s1_hashed_idx, io.f1_req_valid)
-  val s2_req_rlous = lo_us.read(s1_hashed_idx, io.f1_req_valid)
+  val s2_req_rus   = tage_us.read(s1_hashed_idx, io.f1_req_valid)
   val s2_req_rhits = VecInit(s2_req_rtage.map(e => e.valid && e.tag === s2_tag && !doing_reset))
 
   for (w <- 0 until bankWidth) {
     // This bit indicates the TAGE table matched here
     io.f3_resp(w).valid    := RegNext(s2_req_rhits(w))
-    io.f3_resp(w).bits.u   := RegNext(Cat(s2_req_rhius(w), s2_req_rlous(w)))
+    io.f3_resp(w).bits.u   := RegNext(s2_req_rus(w)(1,0))
     io.f3_resp(w).bits.ctr := RegNext(s2_req_rtage(w).ctr)
   }
 
@@ -110,8 +113,6 @@ class TageTable(val nRows: Int, val tagSz: Int, val histLength: Int, val uBitPer
   when (doing_reset) { clear_u_ctr := 1.U } .otherwise { clear_u_ctr := clear_u_ctr + 1.U }
 
   val doing_clear_u = clear_u_ctr(log2Ceil(uBitPeriod)-1,0) === 0.U
-  val doing_clear_u_hi = doing_clear_u && clear_u_ctr(log2Ceil(uBitPeriod) + log2Ceil(nRows)) === 1.U
-  val doing_clear_u_lo = doing_clear_u && clear_u_ctr(log2Ceil(uBitPeriod) + log2Ceil(nRows)) === 0.U
   val clear_u_idx = clear_u_ctr >> log2Ceil(uBitPeriod)
 
   val (update_idx, update_tag) = compute_tag_and_hash(fetchIdx(io.update_pc), io.update_hist)
@@ -124,18 +125,11 @@ class TageTable(val nRows: Int, val tagSz: Int, val histLength: Int, val uBitPer
     Mux(doing_reset, ~(0.U(bankWidth.W))                                , io.update_mask.asUInt).asBools
   )
 
-  val update_hi_wdata = Wire(Vec(bankWidth, Bool()))
-  hi_us.write(
-    Mux(doing_reset, reset_idx, Mux(doing_clear_u_hi, clear_u_idx, update_idx)),
-    Mux(doing_reset || doing_clear_u_hi, VecInit((0.U(bankWidth.W)).asBools), update_hi_wdata),
-    Mux(doing_reset || doing_clear_u_hi, ~(0.U(bankWidth.W)), io.update_u_mask.asUInt).asBools
-  )
-
-  val update_lo_wdata = Wire(Vec(bankWidth, Bool()))
-  lo_us.write(
-    Mux(doing_reset, reset_idx, Mux(doing_clear_u_lo, clear_u_idx, update_idx)),
-    Mux(doing_reset || doing_clear_u_lo, VecInit((0.U(bankWidth.W)).asBools), update_lo_wdata),
-    Mux(doing_reset || doing_clear_u_lo, ~(0.U(bankWidth.W)), io.update_u_mask.asUInt).asBools
+  val update_u_wdata = Wire(Vec(bankWidth, UInt(uSz.W)))
+  tage_us.write(
+    Mux(doing_reset, reset_idx, Mux(doing_clear_u, clear_u_idx, update_idx)),
+    Mux(doing_reset || doing_clear_u, VecInit(Seq.fill(bankWidth) { 0.U(uSz.W) }), update_u_wdata),
+    Mux(doing_reset || doing_clear_u, ~(0.U(bankWidth.W)), io.update_u_mask.asUInt).asBools
   )
 
   val wrbypass_tags    = Reg(Vec(nWrBypassEntries, UInt(tagSz.W)))
@@ -163,8 +157,7 @@ class TageTable(val nRows: Int, val tagSz: Int, val histLength: Int, val uBitPer
     update_wdata(w).valid := true.B
     update_wdata(w).tag   := update_tag
 
-    update_hi_wdata(w)    := io.update_u(w)(1)
-    update_lo_wdata(w)    := io.update_u(w)(0)
+    update_u_wdata(w)     := io.update_u(w)
   }
 
   when (io.update_mask.reduce(_||_)) {
@@ -191,7 +184,7 @@ case class BoomTageParams(
                                               (  256,      16,     8),
                                               (  128,      32,     9),
                                               (  128,      64,     9)),
-  uBitPeriod: Int = 2048
+  uBitPeriod: Int = 4096
 )
```

### v6_2 (ok, on v5_1) -- area -2.3%  cycles +0.0%  fmax -2.2%

```diff
diff --git a/src/main/scala/v3/common/config-mixins.scala b/src/main/scala/v3/common/config-mixins.scala
index d8e2183f..a04ba253 100644
--- a/src/main/scala/v3/common/config-mixins.scala
+++ b/src/main/scala/v3/common/config-mixins.scala
@@ -208,7 +208,7 @@ class WithNMediumBooms(n: Int = 1) extends Config(
                 IssueParams(issueWidth=2, numEntries=20, iqType=IQT_INT.litValue, dispatchWidth=2),
                 IssueParams(issueWidth=1, numEntries=16, iqType=IQT_FP.litValue , dispatchWidth=2)),
               numIntPhysRegisters = 80,
-              numFpPhysRegisters = 64,
+              numFpPhysRegisters = 48,
               numLdqEntries = 16,
               numStqEntries = 16,
               maxBrCount = 12,
diff --git a/src/main/scala/v3/exu/execution-units/execution-unit.scala b/src/main/scala/v3/exu/execution-units/execution-unit.scala
index c3c97b2b..59fbec46 100644
--- a/src/main/scala/v3/exu/execution-units/execution-unit.scala
+++ b/src/main/scala/v3/exu/execution-units/execution-unit.scala
@@ -352,7 +352,7 @@ class ALUExeUnit(
 
     // buffer up results since we share write-port on integer regfile.
     val queue = Module(new BranchKillableQueue(new ExeUnitResp(dataWidth),
-      entries = intToFpLatency + 10)) // TODO being overly conservative
+      entries = intToFpLatency + 4)) // max occupancy is latency+3 (issue->rrd->exe->resp, busy gates issue once non-empty); +1 margin
     queue.io.enq.valid       := ifpu.io.resp.valid
     queue.io.enq.bits.uop    := ifpu.io.resp.bits.uop
     queue.io.enq.bits.data   := ifpu.io.resp.bits.data
@@ -545,7 +545,7 @@ class FPUExeUnit(
     // TODO instantiate our own fpiu; and remove it from fpu.scala.
     // buffer up results since we share write-port on integer regfile.
     val queue = Module(new BranchKillableQueue(new ExeUnitResp(dataWidth),
-      entries = dfmaLatency + 10)) // TODO being overly conservative
+      entries = dfmaLatency + 4)) // max occupancy is latency+3 (issue->rrd->exe->resp, busy gates issue once non-empty); +1 margin
     queue.io.enq.valid       := (fpu.io.resp.valid &&
                                  fpu.io.resp.bits.uop.fu_code_is(FU_F2I) &&
                                  fpu.io.resp.bits.uop.uopc =/= uopSTA) // STA means store data gen for floating point
```

### v7_1 (ok, on v6_2) -- area -5.5%  cycles -1.0%  fmax -1.8%

```diff
index 1c35493a..2233994a 100644
@@ -266,12 +266,22 @@ class BoomL1DataReadReq(implicit p: Parameters) extends BoomBundle()(p) {
   val valid = Vec(memWidth, Bool())
 }
 
+/** L1DataWriteReq plus a byte-granular write mask: the single-ported data array
+ *  writes with byte enables, so a plain store needs no read-modify-write. */
+class BoomL1DataWriteReq(implicit p: Parameters) extends L1DataWriteReq()(p) {
+  val bmask = UInt((rowBits/8).W)
+}
+
 abstract class AbstractBoomDataArray(implicit p: Parameters) extends BoomModule with HasL1HellaCacheParameters {
   val io = IO(new BoomBundle {
     val read  = Input(Vec(memWidth, Valid(new L1DataReadReq)))
-    val write = Input(Valid(new L1DataWriteReq))
+    val write = Input(Valid(new BoomL1DataWriteReq))
     val resp  = Output(Vec(memWidth, Vec(nWays, Bits(encRowBits.W))))
     val nacks = Output(Vec(memWidth, Bool()))
+    // Driven by BoomSinglePortDataArray: a write is queued behind the single
+    // port / the array claims the port for a cycle to drain a starved write
+    val write_pending = Output(Bool())
+    val read_block    = Output(Bool())
   })
 
   def pipeMap[T <: Data](f: Int => T) = VecInit((0 until memWidth).map(f))
@@ -300,6 +310,8 @@ class BoomDuplicatedDataArray(implicit p: Parameters) extends AbstractBoomDataAr
     }
     io.nacks(j) := false.B
   }
+  io.write_pending := false.B
+  io.read_block    := false.B
 }
 
 class BoomBankedDataArray(implicit p: Parameters) extends AbstractBoomDataArray {
@@ -371,6 +383,123 @@ class BoomBankedDataArray(implicit p: Parameters) extends AbstractBoomDataArray
   }
 
   io.nacks := s2_nacks
+  io.write_pending := false.B
+  io.read_block    := false.B
+}
+
+/**
+ * Single-ported data array.  BoomDuplicatedDataArray gives every way a 1R1W
+ * SRAM, and a 1R1W macro of this geometry (512x64) is ~2.5x the area of the
+ * single-port macro the I$ uses for the same bits.  The array is written with
+ * byte enables, so plain stores do not read the row they merge into and the
+ * port sees exactly the parent's traffic (one access per LSU request).  Reads
+ * (loads, AMOs, replays, writebacks) always win the port because they are
+ * latency critical and cannot be delayed (replays / writebacks cannot be
+ * nacked); writes (store/AMO hits from s3, refill beats) go through a small
+ * write-combining FIFO and land in cycles with no read.  Three rules keep this
+ * invisible to the rest of the cache:
+ *   1. a write to a row+way that already has a queued write merges into that
+ *      entry, so every row+way has at most one queued entry;
+ *   2. a read of a row with queued writes gets their bytes forwarded at s2,
+ *      per way (a slot matched at s0 is never recycled before the end of s2);
+ *      a write entering the queue in the same cycle as a read is older than
+ *      that read by three pipeline stages, which the s3/s4/s5 bypass covers,
+ *      exactly as for the parent's read-before-write on the 1R1W array;
+ *   3. when the queue holds nWQ-1 writes or its head has waited 3 cycles the
+ *      array claims the port for one cycle (io.read_block), so writes never
+ *      starve and occupancy stays <= nWQ-1: the queue can never overflow.
+ */
+class BoomSinglePortDataArray(implicit p: Parameters) extends AbstractBoomDataArray
+{
+  require(memWidth == 1)
+  require(encDataBits == wordBits, "single-port data array assumes no data ECC")
+  val nWQ        = 4
+  val rowIdxBits = log2Ceil(nSets * refillCycles)
+  def rowIdx(addr: UInt) = (addr >> rowOffBits)(rowIdxBits-1, 0)
+  def mergeBytes(mask: UInt, newData: UInt, oldData: UInt) =
+    Cat((0 until rowBytes).reverse.map(b => Mux(mask(b), newData(8*b+7, 8*b), oldData(8*b+7, 8*b))))
+
+  val wq_valid = RegInit(VecInit(Seq.fill(nWQ)(false.B)))
+  val wq_bits  = Reg(Vec(nWQ, new BoomL1DataWriteReq))
+  val wq_head  = RegInit(0.U(log2Ceil(nWQ).W))
+  val wq_tail  = RegInit(0.U(log2Ceil(nWQ).W))
+  val wq_count = RegInit(0.U(log2Ceil(nWQ+1).W))
+  val wq_age   = RegInit(0.U(2.W))
+  val wq_nonempty = wq_count =/= 0.U
+
+  val s0_read_valid = io.read(0).valid
+  val s0_raddr      = rowIdx(io.read(0).bits.addr)
+
+  // A write lands whenever nothing reads the port this cycle: queued writes go
+  // first (in order), a new write goes straight through if the queue is empty,
+  // merges into a queued write to the same row+way, or is queued.
+  val port_free = !s0_read_valid
+  val do_deq    = wq_nonempty && port_free
+  val do_direct = io.write.valid && !wq_nonempty && port_free
+  val wmatch    = VecInit((0 until nWQ).map(i => wq_valid(i) && !(do_deq && i.U === wq_head) &&
+                    rowIdx(wq_bits(i).addr) === rowIdx(io.write.bits.addr) &&
+                    wq_bits(i).way_en === io.write.bits.way_en))
+  val do_merge  = io.write.valid && !do_direct && wmatch.asUInt.orR
+  val do_enq    = io.write.valid && !do_direct && !do_merge
+  val do_write  = do_deq || do_direct
+  val wreq      = Mux(wq_nonempty, wq_bits(wq_head), io.write.bits)
+
+  assert(!(do_enq && wq_count === nWQ.U), "[dcache] single-port data array write queue overflow")
+  assert(!(io.read_block && s0_read_valid), "[dcache] data array read while read_block")
+  assert(PopCount(wmatch.asUInt) <= 1.U, "[dcache] write queue holds two entries for one row+way")
+
+  when (do_enq) {
+    wq_bits(wq_tail)  := io.write.bits
+    wq_valid(wq_tail) := true.B
+    wq_tail           := WrapInc(wq_tail, nWQ)
+  }
+  for (i <- 0 until nWQ) {
+    when (do_merge && wmatch(i)) {
+      wq_bits(i).bmask := wq_bits(i).bmask | io.write.bits.bmask
+      wq_bits(i).data  := mergeBytes(io.write.bits.bmask, io.write.bits.data, wq_bits(i).data)
+    }
+  }
+  when (do_deq) {
+    wq_valid(wq_head) := false.B
+    wq_head           := WrapInc(wq_head, nWQ)
+  }
+  when (do_enq && !do_deq) {
+    wq_count := wq_count + 1.U
+  } .elsewhen (do_deq && !do_enq) {
+    wq_count := wq_count - 1.U
+  }
+  when (wq_nonempty && !do_deq) {
+    wq_age := Mux(wq_age.andR, wq_age, wq_age + 1.U)
+  } .otherwise {
+    wq_age := 0.U
+  }
+
+  io.write_pending := wq_nonempty
+  io.read_block    := wq_nonempty && (wq_count >= (nWQ-1).U || wq_age >= 3.U)
+  io.nacks(0)      := false.B
+
+  // Forwarding: remember which slots matched the read's row at s0, and merge
+  // that slot's bytes into the way it belongs to at s2.
+  val s0_match = VecInit((0 until nWQ).map(i => s0_read_valid && wq_valid(i) && rowIdx(wq_bits(i).addr) === s0_raddr))
+  val s1_match = RegNext(s0_match, VecInit(Seq.fill(nWQ)(false.B)))
+  val s2_match = RegNext(s1_match, VecInit(Seq.fill(nWQ)(false.B)))
+
+  val port_addr = Mux(do_write, rowIdx(wreq.addr), s0_raddr)
+  val wdata     = VecInit((0 until rowBytes).map(b => wreq.data(8*b+7, 8*b)))
+  for (w <- 0 until nWays) {
+    val array = DescribedSRAM(
+      name = s"array_${w}_0",
+      desc = "Non-blocking DCache Data Array",
+      size = nSets * refillCycles,
+      data = Vec(rowBytes, UInt(8.W))
+    )
+    val wen     = do_write && wreq.way_en(w)
+    val ren     = s0_read_valid && io.read(0).bits.way_en(w)
+    val rdata   = RegNext(array.readWrite(port_addr, wdata, wreq.bmask.asBools, ren || wen, wen).asUInt)
+    val fwd_sel = VecInit((0 until nWQ).map(i => s2_match(i) && wq_bits(i).way_en(w)))
+    val fwd     = Mux1H(fwd_sel, wq_bits)
+    io.resp(0)(w) := mergeBytes(Fill(rowBytes, fwd_sel.asUInt.orR) & fwd.bmask, fwd.data, rdata)
+  }
 }
 
 /**
@@ -457,18 +586,18 @@ class BoomNonBlockingDCacheModule(outer: BoomNonBlockingDCache) extends LazyModu
   metaWriteArb.io.out.ready := meta.map(_.io.write.ready).reduce(_||_)
 
   // data
-  val data = Module(if (boomParams.numDCacheBanks == 1) new BoomDuplicatedDataArray else new BoomBankedDataArray)
-  val dataWriteArb = Module(new Arbiter(new L1DataWriteReq, 2))
+  val data = Module(if (boomParams.numDCacheBanks == 1) new BoomSinglePortDataArray else new BoomBankedDataArray)
+  val dataWriteArb = Module(new Arbiter(new BoomL1DataWriteReq, 2))
   // 0 goes to pipeline, 1 goes to MSHR refills
   val dataReadArb = Module(new Arbiter(new BoomL1DataReadReq, 3))
   // 0 goes to MSHR replays, 1 goes to wb, 2 goes to pipeline
   dataReadArb.io.in := DontCare
 
   for (w <- 0 until memWidth) {
-    data.io.read(w).valid := dataReadArb.io.out.bits.valid(w) && dataReadArb.io.out.valid
+    data.io.read(w).valid := dataReadArb.io.out.bits.valid(w) && dataReadArb.io.out.fire
     data.io.read(w).bits  := dataReadArb.io.out.bits.req(w)
   }
-  dataReadArb.io.out.ready := true.B
+  dataReadArb.io.out.ready := !data.io.read_block // single-port array draining a starved write
 
   data.io.write.valid := dataWriteArb.io.out.fire
   data.io.write.bits  := dataWriteArb.io.out.bits
@@ -486,7 +615,10 @@ class BoomNonBlockingDCacheModule(outer: BoomNonBlockingDCache) extends LazyModu
     metaReadArb.io.in(4).bits.req(w).way_en := DontCare
     metaReadArb.io.in(4).bits.req(w).tag    := DontCare
     // Data read for new requests
-    dataReadArb.io.in(2).bits.valid(w)      := io.lsu.req.bits(w).valid
+    // Plain stores are written with byte enables (no read-modify-write), so
+    // they leave the single data port to loads and queued writes
+    val lsu_cmd = io.lsu.req.bits(w).bits.uop.mem_cmd
+    dataReadArb.io.in(2).bits.valid(w)      := io.lsu.req.bits(w).valid && !(isWrite(lsu_cmd) && !isRead(lsu_cmd))
     dataReadArb.io.in(2).bits.req(w).addr   := io.lsu.req.bits(w).bits.addr
     dataReadArb.io.in(2).bits.req(w).way_en := ~0.U(nWays.W)
   }
@@ -576,10 +708,33 @@ class BoomNonBlockingDCacheModule(outer: BoomNonBlockingDCache) extends LazyModu
@@ -796,7 +951,13 @@ class BoomNonBlockingDCacheModule(outer: BoomNonBlockingDCache) extends LazyModu
     mshrs.io.mem_grant <> tl_out.d
   }
 
-  dataWriteArb.io.in(1) <> mshrs.io.refill
+  dataWriteArb.io.in(1).valid       := mshrs.io.refill.valid
+  dataWriteArb.io.in(1).bits.addr   := mshrs.io.refill.bits.addr
+  dataWriteArb.io.in(1).bits.way_en := mshrs.io.refill.bits.way_en
+  dataWriteArb.io.in(1).bits.wmask  := mshrs.io.refill.bits.wmask
+  dataWriteArb.io.in(1).bits.data   := mshrs.io.refill.bits.data
+  dataWriteArb.io.in(1).bits.bmask  := ~(0.U((rowBits/8).W))
+  mshrs.io.refill.ready             := dataWriteArb.io.in(1).ready
   metaWriteArb.io.in(0) <> mshrs.io.meta_write
 
   tl_out.e <> mshrs.io.mem_finish
@@ -887,15 +1048,23 @@ class BoomNonBlockingDCacheModule(outer: BoomNonBlockingDCache) extends LazyModu
   val s4_bypass = widthMap(w => s4_valid && ((s2_req(w).addr >> wordOffBits) === (s4_req.addr >> wordOffBits)))
   val s5_bypass = widthMap(w => s5_valid && ((s2_req(w).addr >> wordOffBits) === (s5_req.addr >> wordOffBits)))
 
-  // Store -> Load bypassing
+  // Store -> Load bypassing. A plain store does not read the row it lands in
+  // (the array is written with byte enables), so an older write in s3/s4/s5 may
+  // only supply the bytes it actually wrote; the rest come from the array.
+  val s2_store_mask = new StoreGen(s2_req(0).uop.mem_size, s2_req(0).addr, 0.U, xLen/8).mask
+  val s3_mask8 = RegNext(s2_store_mask)
+  val s4_mask8 = RegNext(s3_mask8)
+  val s5_mask8 = RegNext(s4_mask8)
   for (w <- 0 until memWidth) {
-    s2_data_word(w) := Mux(s3_bypass(w), s3_req.data,
-                       Mux(s4_bypass(w), s4_req.data,
-                       Mux(s5_bypass(w), s5_req.data,
-                                         s2_data_word_prebypass(w))))
+    s2_data_word(w) := Cat((0 until wordBytes).reverse.map { b =>
+      Mux(s3_bypass(w) && s3_mask8(b), s3_req.data(8*b+7, 8*b),
+      Mux(s4_bypass(w) && s4_mask8(b), s4_req.data(8*b+7, 8*b),
+      Mux(s5_bypass(w) && s5_mask8(b), s5_req.data(8*b+7, 8*b),
+                                       s2_data_word_prebypass(w)(8*b+7, 8*b))))
+    })
   }
   val amoalu   = Module(new AMOALU(xLen))
-  amoalu.io.mask := new StoreGen(s2_req(0).uop.mem_size, s2_req(0).addr, 0.U, xLen/8).mask
+  amoalu.io.mask := s2_store_mask
   amoalu.io.cmd  := s2_req(0).uop.mem_cmd
   amoalu.io.lhs  := s2_data_word(0)
   amoalu.io.rhs  := s2_req(0).data
@@ -909,7 +1078,9 @@ class BoomNonBlockingDCacheModule(outer: BoomNonBlockingDCache) extends LazyModu
   dataWriteArb.io.in(0).bits.wmask  := UIntToOH(s3_req.addr.extract(rowOffBits-1,offsetlsb))
   dataWriteArb.io.in(0).bits.data   := Fill(rowWords, s3_req.data)
   dataWriteArb.io.in(0).bits.way_en := s3_way
+  dataWriteArb.io.in(0).bits.bmask  := (if (rowWords == 1) s3_mask8 else
+    (s3_mask8 << Cat(s3_req.addr.extract(rowOffBits-1,offsetlsb), 0.U(log2Ceil(wordBytes).W)))(rowBits/8-1, 0))
 
 
-  io.lsu.ordered := mshrs.io.fence_rdy && !s1_valid.reduce(_||_) && !s2_valid.reduce(_||_)
+  io.lsu.ordered := mshrs.io.fence_rdy && !s1_valid.reduce(_||_) && !s2_valid.reduce(_||_) && !data.io.write_pending
 }
```

### v8 (ok, on v7_1) -- area -2.9%  cycles +0.0%  fmax +3.1%

```diff
index d8e2183f..6564ecf6 100644
@@ -208,20 +208,22 @@ class WithNMediumBooms(n: Int = 1) extends Config(
               numFetchBufferEntries = 16,
               ftq = FtqParameters(nEntries=32),
               nPerfCounters = 6,
+              nL2TLBEntries = 0, // embench runs bare-metal (satp=0): vm_enabled is always false, so the 512x45 L2 TLB is never filled or read
+              nPTECacheEntries = 0, // same: the PTE cache is only read while walking page tables, which never happens with satp=0
               fpu = Some(freechips.rocketchip.tile.FPUParams(sfmaLatency=4, dfmaLatency=4, divSqrt=true))
             ),
             dcache = Some(
               DCacheParams(rowBits = 64, nSets=64, nWays=4, nMSHRs=2, nTLBWays=8)
             ),
             icache = Some(
-              ICacheParams(rowBits = 64, nSets=64, nWays=4, fetchBytes=2*4)
+              ICacheParams(rowBits = 64, nSets=64, nWays=4, nTLBWays=8, fetchBytes=2*4)
             ),
             tileId = i + idOffset
           ),
```

### v9 (ok, on v8) -- area +0.0%  cycles +0.0%  fmax +2.9%

```diff
diff --git a/src/main/scala/v3/exu/core.scala b/src/main/scala/v3/exu/core.scala
index 998a7f8d..873f87da 100644
--- a/src/main/scala/v3/exu/core.scala
+++ b/src/main/scala/v3/exu/core.scala
@@ -120,7 +120,12 @@ class BoomCore()(implicit p: Parameters) extends BoomModule
                              numIrfReadPorts,
                              numIrfWritePorts,
                              xLen,
-                             Seq.fill(memWidth) {true} ++ exe_units.bypassable_write_port_mask)) // bypassable ll_wb
+                             Seq.fill(memWidth) {true} ++ exe_units.bypassable_write_port_mask, // bypassable ll_wb
+                             // Stage the ll_wb write port: its data is the D$ s2 response, which
+                             // arrives at the end of the cycle, and from the write port it fans
+                             // out into the regfile's write decode and bypass muxes.  The bypass
+                             // (enabled above) covers the one cycle the later write would miss.
+                             Seq.fill(memWidth) {true} ++ exe_units.bypassable_write_port_mask.map(_ => false)))
   val pregfile         = Module(new RegisterFileSynthesizable(
                             ftqSz,
                             exe_units.numIrfReaders,
diff --git a/src/main/scala/v3/exu/register-read/regfile.scala b/src/main/scala/v3/exu/register-read/regfile.scala
index 7165baa0..290dafb8 100644
--- a/src/main/scala/v3/exu/register-read/regfile.scala
+++ b/src/main/scala/v3/exu/register-read/regfile.scala
@@ -108,7 +108,8 @@ class RegisterFileSynthesizable(
    numReadPorts: Int,
    numWritePorts: Int,
    registerWidth: Int,
-   bypassableArray: Seq[Boolean])
+   bypassableArray: Seq[Boolean],
+   pipelinedArray: Seq[Boolean] = Seq[Boolean]())
    (implicit p: Parameters)
    extends RegisterFile(numRegisters, numReadPorts, numWritePorts, registerWidth, bypassableArray)
 {
@@ -116,6 +117,38 @@ class RegisterFileSynthesizable(
 
   val regfile = Mem(numRegisters, UInt(registerWidth.W))
 
+  // --------------------------------------------------------------
+  // Write-port staging.
+  //
+  // A "pipelined" write port is one whose data arrives at the very end of the
+  // cycle.  The long-latency (ll_wb) port is fed combinationally from the D$ s2
+  // response, through the LSU and the ll writeback arbiter, and from here it fans
+  // out into the memory's write-enable decode *and* into the bypass network -- the
+  // core's critical path.  Staging the port in a flop takes both of those fanouts
+  // off that path: the memory is written a cycle later, and the bypass, which now
+  // sees the staged copy, covers the readers that the later write would miss.
+  //
+  // This costs no cycles, because the earliest consumer of an ll_wb value already
+  // reads the regfile the cycle *after* the write.  The speculative load wakeup
+  // fires in the D$ s1 stage, one cycle before the data, so a dependent is granted
+  // in the writeback cycle W and reaches RRD in W+1 at the earliest (a dependent
+  // woken by the normal ll wakeup in W only reaches RRD in W+2).  Under the parent
+  // the W+1 reader hit the memory, written at the end of W; here it hits the
+  // bypass, and every later reader hits the memory, written at the end of W+1.
+  val pipelined = if (pipelinedArray.isEmpty) Seq.fill(numWritePorts)(false) else pipelinedArray
+  require (pipelined.length == numWritePorts)
+
+  val write_ports = Wire(Vec(numWritePorts, Valid(new RegisterFileWritePort(maxPregSz, registerWidth))))
+  for (i <- 0 until numWritePorts) {
+    if (pipelined(i)) {
+      write_ports(i).valid     := RegNext(io.write_ports(i).valid, false.B)
+      write_ports(i).bits.addr := RegNext(io.write_ports(i).bits.addr)
+      write_ports(i).bits.data := RegNext(io.write_ports(i).bits.data)
+    } else {
+      write_ports(i) := io.write_ports(i)
+    }
+  }
+
   // --------------------------------------------------------------
   // Read ports.
 
@@ -139,7 +172,7 @@ class RegisterFileSynthesizable(
 
   if (bypassableArray.reduce(_||_)) {
     val bypassable_wports = ArrayBuffer[Valid[RegisterFileWritePort]]()
-    io.write_ports zip bypassableArray map { case (wport, b) => if (b) { bypassable_wports += wport} }
+    write_ports zip bypassableArray map { case (wport, b) => if (b) { bypassable_wports += wport} }
 
     for (i <- 0 until numReadPorts) {
       val bypass_ens = bypassable_wports.map(x => x.valid &&
@@ -158,7 +191,7 @@ class RegisterFileSynthesizable(
   // --------------------------------------------------------------
   // Write ports.
 
-  for (wport <- io.write_ports) {
+  for (wport <- write_ports) {
     when (wport.valid) {
       regfile(wport.bits.addr) := wport.bits.data
     }
@@ -168,10 +201,10 @@ class RegisterFileSynthesizable(
   if (numWritePorts > 1) {
     for (i <- 0 until (numWritePorts - 1)) {
       for (j <- (i + 1) until numWritePorts) {
-        assert(!io.write_ports(i).valid ||
-               !io.write_ports(j).valid ||
-               (io.write_ports(i).bits.addr =/= io.write_ports(j).bits.addr) ||
-               (io.write_ports(i).bits.addr === 0.U), // note: you only have to check one here
+        assert(!write_ports(i).valid ||
+               !write_ports(j).valid ||
+               (write_ports(i).bits.addr =/= write_ports(j).bits.addr) ||
+               (write_ports(i).bits.addr === 0.U), // note: you only have to check one here
           "[regfile] too many writers a register")
       }
     }
```

### v10 (gates_failed, on v9) -- area +0.1%  cycles +0.0%  fmax -20.2%

```diff
diff --git a/src/main/scala/v3/exu/execution-units/fpu.scala b/src/main/scala/v3/exu/execution-units/fpu.scala
index 074170d2..19e3bce5 100644
--- a/src/main/scala/v3/exu/execution-units/fpu.scala
+++ b/src/main/scala/v3/exu/execution-units/fpu.scala
@@ -205,7 +205,7 @@ class FPU(implicit p: Parameters) extends BoomModule with tile.HasFPUParameters
     req
   }
 
-  val dfma = Module(new tile.FPUFMAPipe(latency = fpu_latency, t = tile.FType.D))
+  val dfma = Module(new BoomFPUFMAPipe(latency = fpu_latency, t = tile.FType.D))
   dfma.io.in.valid := io.req.valid && fp_ctrl.fma && (fp_ctrl.typeTagOut === D)
   dfma.io.in.bits := fuInput(Some(dfma.t))
 
@@ -249,3 +249,107 @@ class FPU(implicit p: Parameters) extends BoomModule with tile.HasFPUParameters
   io.resp.bits.fflags.valid      := io.resp.valid
   io.resp.bits.fflags.bits.flags := fpu_out_exc
 }
+
+/**
+ * Registered output of the FMA's operand-alignment stage.
+ */
+class BoomFMAPreMul(val expWidth: Int, val sigWidth: Int) extends Bundle
+{
+  val mulAddA   = UInt(sigWidth.W)
+  val mulAddB   = UInt(sigWidth.W)
+  val mulAddC   = UInt((sigWidth*2).W)
+  val toPostMul = new hardfloat.MulAddRecFN_interIo(expWidth, sigWidth)
+  val rm        = UInt(tile.FPConstants.RM_SZ.W)
+}
+
+/**
+ * FMA pipe with the operand-alignment stage moved ahead of the input register.
+ *
+ * rocket's FPUFMAPipe latches the raw FPInput and then spends one cycle on
+ * MulAddRecFNToRaw_preMul *plus* the sigWidth x sigWidth multiply and the
+ * 2*sigWidth+1 add.  For double precision that single stage owns every path in
+ * the tile that misses timing: it needs 20.64ns of a 20ns target, while the
+ * worst endpoint anywhere else in the design (the rename busy table) finishes
+ * in 19.63ns.  preMul -- the exponent compare and the ~160-position alignment
+ * shift of C -- is 6.64ns of that 20.64ns, and it reads nothing but operands
+ * that are already sitting in the register-read pipeline registers, so it fits
+ * in the cycle *before* the FMA where most of the period is going unused.
+ *
+ * The pipeline depth is unchanged: the input register is moved downstream of
+ * preMul rather than added to it, so dfmaLatency -- and every FP writeback
+ * schedule the core derives from it -- stays exactly as it was.  Stage
+ * boundaries become
+ *   s0: operand fixup + preMul           (~7ns of logic after register read)
+ *   s1: sigWidth x sigWidth mul + add    (~14ns, was the tail of s0)
+ *   s2: postMul
+ *   s3: round
+ * Every boundary carries the same values the original carried, just one
+ * combinational block earlier, so the unit is bit-identical cycle for cycle.
+ */
+class BoomFPUFMAPipe(val latency: Int, val t: tile.FType)(implicit p: Parameters)
+  extends BoomModule with HasFPUParameters
+{
+  override def desiredName = s"BoomFPUFMAPipe_l${latency}_f${t.ieeeWidth}"
+  require (latency >= 3)
+
+  val io = IO(new Bundle {
+    val in  = Flipped(Valid(new tile.FPInput))
+    val out = Valid(new tile.FPResult)
+  })
+
+  // --- s0: operand fixup + alignment ------------------------------------
+  // The fixups are the ones rocket applies as it writes its input register:
+  // an add/sub multiplies by one, and a bare multiply adds a signed zero.
+  val one        = 1.U << (t.sig + t.exp - 1)
+  val zero       = (io.in.bits.in1 ^ io.in.bits.in2) & (1.U << (t.sig + t.exp))
+  val cmd_fma    = io.in.bits.ren3
+  val cmd_addsub = io.in.bits.swap23
+
+  val premul = Module(new hardfloat.MulAddRecFNToRaw_preMul(t.exp, t.sig))
+  premul.io.op := io.in.bits.fmaCmd
+  premul.io.a  := io.in.bits.in1
+  premul.io.b  := Mux(cmd_addsub, one, io.in.bits.in2)
+  premul.io.c  := Mux(cmd_fma || cmd_addsub, io.in.bits.in3, zero)
+
+  val s0_out = Wire(new BoomFMAPreMul(t.exp, t.sig))
+  s0_out.mulAddA   := premul.io.mulAddA
+  s0_out.mulAddB   := premul.io.mulAddB
+  s0_out.mulAddC   := premul.io.mulAddC
+  s0_out.toPostMul := premul.io.toPostMul
+  s0_out.rm        := io.in.bits.rm
+
+  val s1 = Pipe(io.in.valid, s0_out, 1)
+
+  // --- s1: the multiply-add ---------------------------------------------
+  val mulAddResult = (s1.bits.mulAddA * s1.bits.mulAddB) +& s1.bits.mulAddC
+
+  val s2_valid     = RegNext(s1.valid, false.B)
+  val s2_result    = RegEnable(mulAddResult,      s1.valid)
+  val s2_toPostMul = RegEnable(s1.bits.toPostMul, s1.valid)
+  val s2_rm        = RegEnable(s1.bits.rm,        s1.valid)
+
+  // --- s2: normalize ------------------------------------------------------
+  val postmul = Module(new hardfloat.MulAddRecFNToRaw_postMul(t.exp, t.sig))
+  postmul.io.fromPreMul   := s2_toPostMul
+  postmul.io.mulAddResult := s2_result
+  postmul.io.roundingMode := s2_rm
+
+  val s3_valid      = RegNext(s2_valid, false.B)
+  val s3_invalidExc = RegEnable(postmul.io.invalidExc, s2_valid)
+  val s3_rawOut     = RegEnable(postmul.io.rawOut,     s2_valid)
+  val s3_rm         = RegEnable(s2_rm,                 s2_valid)
+
+  // --- s3: round ----------------------------------------------------------
+  val round = Module(new hardfloat.RoundRawFNToRecFN(t.exp, t.sig, 0))
+  round.io.invalidExc     := s3_invalidExc
+  round.io.infiniteExc    := false.B
+  round.io.in             := s3_rawOut
+  round.io.roundingMode   := s3_rm
+  round.io.detectTininess := hardfloat.consts.tininess_afterRounding
+
+  val res = Wire(new tile.FPResult)
+  res.data := sanitizeNaN(round.io.out, t)
+  res.exc  := round.io.exceptionFlags
+
+  io.out := Pipe(s3_valid, res, latency-3)
+}
```

### v10_1 (gates_failed, on v9) -- area +0.4%  cycles -0.0%  fmax -18.2%

```diff
index d8e2183f..b40e71e8 100644
-              fpu = Some(freechips.rocketchip.tile.FPUParams(sfmaLatency=4, dfmaLatency=4, divSqrt=true))
+              fpu = Some(freechips.rocketchip.tile.FPUParams(sfmaLatency=5, dfmaLatency=5, divSqrt=true)) // FMA is 5 stages (BoomFPUFMAPipe adds a preMul/mul register); embench is integer-only so the extra cycle costs nothing
diff --git a/src/main/scala/v3/exu/execution-units/fpu.scala b/src/main/scala/v3/exu/execution-units/fpu.scala
index 074170d2..d1be5b21 100644
--- a/src/main/scala/v3/exu/execution-units/fpu.scala
+++ b/src/main/scala/v3/exu/execution-units/fpu.scala
@@ -205,11 +205,11 @@ class FPU(implicit p: Parameters) extends BoomModule with tile.HasFPUParameters
     req
   }
 
-  val dfma = Module(new tile.FPUFMAPipe(latency = fpu_latency, t = tile.FType.D))
+  val dfma = Module(new BoomFPUFMAPipe(latency = fpu_latency, t = tile.FType.D))
   dfma.io.in.valid := io.req.valid && fp_ctrl.fma && (fp_ctrl.typeTagOut === D)
   dfma.io.in.bits := fuInput(Some(dfma.t))
 
-  val sfma = Module(new tile.FPUFMAPipe(latency = fpu_latency, t = tile.FType.S))
+  val sfma = Module(new BoomFPUFMAPipe(latency = fpu_latency, t = tile.FType.S))
   sfma.io.in.valid := io.req.valid && fp_ctrl.fma && (fp_ctrl.typeTagOut === S)
   sfma.io.in.bits := fuInput(Some(sfma.t))
 
@@ -249,3 +249,120 @@ class FPU(implicit p: Parameters) extends BoomModule with tile.HasFPUParameters
   io.resp.bits.fflags.valid      := io.resp.valid
   io.resp.bits.fflags.bits.flags := fpu_out_exc
 }
+
+/**
+ * Re-timed multiply-add core: same hardfloat blocks as rocket's MulAddRecFNPipe(2),
+ * but with one extra register between MulAddRecFNToRaw_preMul and the
+ * (mulAddA * mulAddB) +& mulAddC multiply-add, which otherwise share a stage
+ * and form the tile's worst timing path.
+ *   stage 1: preMul -> reg
+ *   stage 2: mul + add -> reg
+ *   stage 3: postMul -> reg
+ *   stage 4: round (combinational out)
+ */
+class BoomMulAddRecFNPipe(expWidth: Int, sigWidth: Int) extends Module
+{
+  override def desiredName = s"BoomMulAddRecFNPipe_e${expWidth}_s${sigWidth}"
+
+  val io = IO(new Bundle {
+    val validin        = Input(Bool())
+    val op             = Input(Bits(2.W))
+    val a              = Input(Bits((expWidth + sigWidth + 1).W))
+    val b              = Input(Bits((expWidth + sigWidth + 1).W))
+    val c              = Input(Bits((expWidth + sigWidth + 1).W))
+    val roundingMode   = Input(UInt(3.W))
+    val detectTininess = Input(UInt(1.W))
+    val out            = Output(Bits((expWidth + sigWidth + 1).W))
+    val exceptionFlags = Output(Bits(5.W))
+    val validout       = Output(Bool())
+  })
+
+  val preMul  = Module(new hardfloat.MulAddRecFNToRaw_preMul(expWidth, sigWidth))
+  val postMul = Module(new hardfloat.MulAddRecFNToRaw_postMul(expWidth, sigWidth))
+
+  preMul.io.op := io.op
+  preMul.io.a  := io.a
+  preMul.io.b  := io.b
+  preMul.io.c  := io.c
+
+  // stage 1: preMul outputs registered (the new cut). Plain RegNext (no enable):
+  // every consumer is qualified by the matching s*_valid, so the mux per bit is not needed
+  val s1_valid     = RegNext(io.validin, false.B)
+  val s1_mulAddA   = RegNext(preMul.io.mulAddA)
+  val s1_mulAddB   = RegNext(preMul.io.mulAddB)
+  val s1_mulAddC   = RegNext(preMul.io.mulAddC)
+  val s1_toPostMul = RegNext(preMul.io.toPostMul)
+  val s1_rm        = RegNext(io.roundingMode)
+  val s1_tin       = RegNext(io.detectTininess)
+
+  // stage 2: multiply-add
+  val mulAddResult = (s1_mulAddA * s1_mulAddB) +& s1_mulAddC
+  val s2_valid        = RegNext(s1_valid, false.B)
+  val s2_toPostMul    = RegNext(s1_toPostMul)
+  val s2_mulAddResult = RegNext(mulAddResult)
+  val s2_rm           = RegNext(s1_rm)
+  val s2_tin          = RegNext(s1_tin)
+
+  postMul.io.fromPreMul   := s2_toPostMul
+  postMul.io.mulAddResult := s2_mulAddResult
+  postMul.io.roundingMode := s2_rm
+
+  // stage 3: postMul registered, stage 4: round
+  val s3_valid = RegNext(s2_valid, false.B)
+  val round = Module(new hardfloat.RoundRawFNToRecFN(expWidth, sigWidth, 0))
+  round.io.invalidExc     := RegNext(postMul.io.invalidExc)
+  round.io.infiniteExc    := false.B
+  round.io.in             := RegNext(postMul.io.rawOut)
+  round.io.roundingMode   := RegNext(s2_rm)
+  round.io.detectTininess := RegNext(s2_tin)
+
+  io.validout       := s3_valid
+  io.out            := round.io.out
+  io.exceptionFlags := round.io.exceptionFlags
+}
+
+/**
+ * Drop-in for rocket's FPUFMAPipe with the input register and one/zero fixups
+ * kept as-is, but using BoomMulAddRecFNPipe (4 register stages after the input
+ * register). Total latency = 1 (in reg) + 3 + (latency-4) output pipe.
+ */
+class BoomFPUFMAPipe(val latency: Int, val t: tile.FType)(implicit p: Parameters)
+  extends BoomModule with tile.HasFPUParameters
+{
+  override def desiredName = s"BoomFPUFMAPipe_l${latency}_f${t.ieeeWidth}"
+  require(latency >= 4)
+
+  val io = IO(new Bundle {
+    val in  = Flipped(Valid(new tile.FPInput))
+    val out = Valid(new tile.FPResult)
+  })
+
+  val valid = RegNext(io.in.valid, false.B)
+  val in = Reg(new tile.FPInput)
+  when (io.in.valid) {
+    val one = 1.U << (t.sig + t.exp - 1)
+    val zero = (io.in.bits.in1 ^ io.in.bits.in2) & (1.U << (t.sig + t.exp))
+    val cmd_fma = io.in.bits.ren3
+    val cmd_addsub = io.in.bits.swap23
+    in := io.in.bits
+    when (cmd_addsub) { in.in2 := one }
+    when (!(cmd_fma || cmd_addsub)) { in.in3 := zero }
+  }
+
+  val fma = Module(new BoomMulAddRecFNPipe(t.exp, t.sig))
+  fma.io.validin        := valid
+  fma.io.op             := in.fmaCmd
+  fma.io.roundingMode   := in.rm
+  fma.io.detectTininess := hardfloat.consts.tininess_afterRounding
+  fma.io.a := in.in1
+  fma.io.b := in.in2
+  fma.io.c := in.in3
+
+  val res = Wire(new tile.FPResult)
+  res.data := sanitizeNaN(fma.io.out, t)
+  res.exc  := fma.io.exceptionFlags
+
+  // output padding to the requested latency; bits are unqualified (FPU response mux checks valid)
+  io.out.valid := ShiftRegister(fma.io.validout, latency-4, false.B, true.B)
+  io.out.bits  := ShiftRegister(res, latency-4)
+}
```
