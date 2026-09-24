Improve the performance-area efficiency of an implementation of the BOOM out-of-order processor core.

## Target config

`$ARGUMENTS`.

Check that your edit reaches it. BOOM's parameters have defaults in
`parameters.scala`, and the config sets its own values over them in
`config-mixins.scala`. Change a default there that the config already sets and
nothing happens — change it in the mixin instead.

Configs live in `generators/chipyard/src/main/scala/config/`; this one's BOOM
parameters come from `$BUILD_CONFIG_PACKAGE`.

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

**The parent design you are improving — branch `$PARENT_BRANCH`:**

| metric | value |
|---|---|
| total cell area | $PARENT_AREA um2 |
| embench speed score | $PARENT_SPEED |
| embench speed per MHz | $PARENT_SPEED_PER_MHZ |
| mean embench IPC | $PARENT_MEAN_IPC (reported, not the objective) |
| fmax | $PARENT_FMAX MHz ($STA_CORNER) |
| perf_area_eff (speed/mm2) | $PARENT_EFF |

**The bar you have to clear is not that last row.** It is `$BEST_EFF`, reached
by branch `$BEST_BRANCH` — the best figure any branch in the tree has measured,
and what the gate compares you against.

Usually `$BEST_BRANCH` *is* the parent and the two are the same number. When
they are not, this run was started from a branch that is not the tree's best:
beating your parent is then not enough, because the tree already holds a better
result and repeating it is no gain. Close the gap first, then improve on it.

### What earlier iterations already did

The lineage that produced the parent, plus the attempts rejected along the way.
The parent's code already contains every change in the lineage rows; what you
cannot see from the code is which of them worked and what was thrown away. The
hunk behind each row is under **Earlier edits** at the end of this document.

$HISTORY_TABLE

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

1. **`perf_area_eff` must exceed `$BEST_EFF`** — the best any branch has
   measured (`$BEST_BRANCH`), not the parent's figure. Strictly exceed:
   this flow is deterministic, so landing exactly on the bar means the RTL came
   back to a design the tree already has, and that is recorded as a failure.
   Frequency is a factor of the score, so this gate covers timing too.
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

Those deltas are against the **parent**, because the parent is the code you are
editing. The gate is against the **best so far**. When the parent is not the
best branch, `> 1` is not the threshold — you need
`parent_eff x (your ratio) > $BEST_EFF`, so work out that gap in percent first
and add it to whatever you are trying to win.

SRAM macros are the largest single blocks, so cache and predictor *geometry*
changes move both area and cycle counts a lot, while datapath tweaks mostly move
area a little.

## The path that is currently capping fmax

Two branches in a row (v15, v15_1) removed real area at almost no cycle cost and
were still rejected, because both lost 10-17% of fmax to the same path. **All 100
of the worst paths in each of those reports end in an issue queue.** Until this
path has margin, any edit that perturbs it loses more on the frequency term than
it can win on area, and this is the first thing to check about a candidate.

Measured, worst path in each:

```
v14   -0.7594   dfma        76 levels, 20.643 ns, no stage over 1 ns   (issue-queue endpoints: 27/100)
v15   -3.0016   issue slot  53 levels: 11.907 ns over 51 stages + 11.012 ns in TWO
v15_1 -5.1202   issue slot  54 levels: 10.414 ns over 51 stages + 14.624 ns in THREE
```

### What the path is

Speculative load wakeup and its recovery. At D$ s1 the LSU asserts
`spec_ld_wakeup`, betting the load hits, and wakes dependents a cycle early,
marking them poisoned (`issue-slot.scala:213`). At s2, if the load actually
missed, `ld_miss` must undo that in the same cycle:

```
core.scala:1602   iu.io.spec_ld_wakeup := io.lsu.spec_ld_wakeup
core.scala:1679   issue_units.map(_.io.ld_miss := io.lsu.ld_miss)
core.scala:1710   iss_valids(w) && !(io.lsu.ld_miss && (iss_uops(w).iw_p1_poisoned || ...))
issue-slot.scala:175/179   when (io.ldspec_miss && next_p1_poisoned) { ... }
```

So a signal that resolves late in the cycle (the D$ tag compare) has to reach the
operand-ready state of every issue slot -- 20 integer + 12 memory + the FP slots --
and also gate the issue that is happening in that same cycle. It cannot be
registered without giving up the speculation it exists to support.

### Where the time actually goes

Split the worst path by stage delay before deciding what to do. In both branches
about 11 ns is spread evenly over ~51 stages -- that is real logic depth, and on
its own it fits in the 20 ns period. The violation comes from **two or three
stages**:

```
v15     5.831 ns  lsu/_38262_   a41oi_1        v15_1   8.365 ns  lsu/_49102_   a21boi_0
        5.181 ns  core/_1913_   o21ai_0                5.104 ns  core/_1952_   o21ai_0
```

`_0` and `_1` are the weakest drive strengths in this library. A gate taking 5-8 ns
when its neighbours take 0.2 ns is not deep logic -- it is a minimum-size cell
driving a very large load. These nets leave their module, so the mapper sized them
against a default output load and never saw the real fanout.

That has two consequences for you:

- **Do not try to fix this by shortening logic.** The 51 stages of real logic are
  not the problem.
- **Do not try to fix it by replicating the driver in RTL.** That was tried: Yosys
  `opt_merge` merges the copies back and the fix does not survive.

The lever that is left is **structural: reduce how far and how wide this signal has
to go inside one cycle.** Ideas worth pricing, not a list to work through:

- Does every slot need the full-width broadcast, or can the poison recovery be
  narrowed to the slots that were actually speculatively woken?
- Can the s2 miss information be pre-decoded on the LSU side so that what crosses
  into the issue unit is already narrow and late-arriving-free?
- Is the same-cycle `iss_valids` gate (`core.scala:1710`) separable from the state
  update, so only the cheaper of the two stays on the critical path?
- Would restricting speculative wakeup (fewer slots eligible, or only for the
  common case) cost less in cycles than the frequency it currently costs?

### How to tell whether you fixed it

Run a **full-tile A/B** (`vlsi_top=BoomTile`, both sides) and compare the worst
path's endpoint family, not just the slack number. If the top of the report has
moved off the issue queues and back onto `dfma` or `rename_stage/busytable`, the
path is no longer binding. If it is still an issue slot, it is not fixed, whatever
the slack says.

Two cautions about that A/B. Its **area** figure is accurate to the um2 and you can
trust it. Its **fmax** is not reliable: the A/B feeds the mapper a smaller file set
than the scoring run, and on this design that is enough to change which nets get
minimum-size drivers. A green fmax from the A/B has been wrong before.

Same-RTL evidence for how much of this is synthesis rather than design: with Yosys
`flatten` on, where the mapper sees the real fanout, v15 measures 47.75 MHz and
v15_1 47.90 MHz instead of 43.48 and 39.81. The design is not 10 MHz slower than
its parent. But the scoring run does not use flatten, so the cost is real for you.

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
(~520,000 um2) takes about 1.5–2 min per side.

`BoomCore` and `BoomTile` both fit the 5400s cap (a full BoomTile synthesis
measures 1500–2400s), but two sides cost most of a round, so A/B them only when
nothing smaller contains the edit. `BoomCore`'s own glue — the logic outside
every submodule — is one such case, and its area is printed in the area report
as `Chip area for module '\BoomCore'`, so an edit confined to it can be priced
from the report with no A/B at all.

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
  `$STA_REPORT_PATH`. If a structure you are touching appears in its worst paths,
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

## Area report (Yosys) — `$AREA_REPORT_PATH`

- **Tile total:** `grep -A3 'Chip area for module' $AREA_REPORT_PATH | tail -20`
- **Per-module, largest first:**
  `grep 'Chip area for module' $AREA_REPORT_PATH | sort -t: -k2 -g -r | head -40`
- **Hierarchy (where the SRAM macros are counted):**
  `awk '/=== design hierarchy ===/,0' $AREA_REPORT_PATH | head -60`
- **One module's cell mix:** `awk '/module \\\\<name>/,/^$/' $AREA_REPORT_PATH`

Work top-down: only the modules at the top of that sorted list can move the
objective.

## IPC report — `$IPC_REPORT_PATH`

Per-benchmark IPC for the parent, with the area and fmax headline. Small enough
to read whole: `cat $IPC_REPORT_PATH`.

The objective is built from these benchmarks' *cycle counts*, not from the IPC
column: each is scored against a fixed reference platform and the 19 are combined
geometrically, so every benchmark counts equally regardless of length and a large
loss on any one cannot be averaged away. IPC is shown because it separates a
cycle-count change from a frequency change, which the objective alone does not.

## STA report (OpenSTA) — `$STA_REPORT_PATH`

At `$STA_CORNER` against a $CLOCK_PERIOD_NS ns target. The design does not close
at that target, so a violation is not by itself a problem — read it as a ranking.

- **Count paths:** `grep -c '^Startpoint' $STA_REPORT_PATH`
- **Worst path and achievable period:**
  `grep -E 'slack|data arrival time' $STA_REPORT_PATH | head -20`
- **Endpoints at a glance:**
  `grep -E '^(Startpoint|Endpoint)' $STA_REPORT_PATH | head -60`
- **One path in full:** `awk '/^Startpoint/{n++} n==1' $STA_REPORT_PATH`
- **Paths through a structure:**
  `grep -B3 -A1 '<module_or_signal_name>' $STA_REPORT_PATH | head -40`

Cluster paths by endpoint family before concluding a structure is critical:
several paths ending in the same register class usually share one bottleneck.
Worst paths typically *start* in one module and *end* in another, so the
structure that owns a path is not always the one the endpoint names.

The report holds the worst 100 endpoints and nothing else, so it ranks what is
already near-critical and says nothing about the rest of the design. A path it
does not list has more slack than its last entry — how much more, it cannot
tell you. Before you move logic onto a path, check whether that path is in here
at all; if it is not, you are estimating, not measuring, and should say so.

## Earlier branches' reports — `$HISTORY_REPORT_DIR/<branch>/`

The same three files for each of: $HISTORY_REPORT_BRANCHES — the most recent
branches, so not the same set as the history table above, which follows your
lineage. The same name means the same branch in both.

An earlier edit's hunk says what it *changed*; these say what it *did*. Those
are different, and the gap between them is where rounds get wasted: a mechanism
that reads plausibly off a diff is often not the one that fired. When you are
about to design around a previous failure, check the failure.

- **What did that edit actually break?**
  `grep -E '^Endpoint' $HISTORY_REPORT_DIR/<branch>/sta_report.rpt | sort | uniq -c | sort -rn | head`
- **Did it hurt the structure you think it hurt?**
  `grep -c '<module_name>' $HISTORY_REPORT_DIR/<branch>/sta_report.rpt` — zero
  means that structure owns none of its 100 worst paths, so whatever it lost, it
  did not lose there.
- **Was a path already tight, or did the edit push it?** Compare the same
  endpoint in two branches' reports.
- **Where its area went:**
  `grep 'Chip area for module' $HISTORY_REPORT_DIR/<branch>/area_report.txt | sort -t: -k2 -g -r | head -20`
- **Which benchmarks moved:** `cat $HISTORY_REPORT_DIR/<branch>/ipc_report.md`

A `_synth_only` branch is the same RTL synthesized again. It reproduces its
parent to the last digit, so a difference means the *synthesis settings*
differed: a `..._flatten` branch ran Yosys `flatten`, which optimizes across
module boundaries and changes both area and fmax on identical RTL. Never
compare its figures against a normal branch's.

Same warning as above: do not `cat` any of these `sta_report.rpt` whole.

---

# Earlier edits

$HISTORY_DIFFS
