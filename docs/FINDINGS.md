# Desert Falcon (7800): findings

ROM: `Desert Falcon (NTSC) (Atari) (1987) (A1DC0899).a78`, linear 48K at `$4000-$FFFF`, TIA sound.
All of this was worked out on 2026-11-18 with the a7800 toolkit and the user's MAME fork
(`a78.exe`, windowless, `-bios skip`). Names in `CamelCase` are this project's labels in
`annotations.json`; regenerate the listing to see them (README).

Evidence tags: **(live)** seen in MAME (a tap, a RAM model checked every frame, a poke that changed
the picture), **(code)** read from the listing only, **(hint)** a guess. Section 9 lists the runs.

In one paragraph: the game keeps every drawable thing in one doubly linked list sorted far to near.
A builder walks that list once per tick (30 Hz) and drops each object into one or two of twelve
16-line zone lists, after a fixed tile header. World position is three bytes (A along the flight
path, B across it, C height); the screen position is two adds each, the depth key is one subtract.
A shadow is the same picture drawn a second time in an all-dark palette at height 0. The ground is
twelve rows of characters whose headers slide left a pixel at a time, and the whole zone grid
slides down by changing the heights of the first and last zones in the DLL.

## 1. Depth order

**What it is.** One doubly linked list of object slots. `ListHead` (`$CD`) is the farthest,
`ListTail` (`$D0`) the nearest; `ObjNext` (`$2650,X`) and `ObjPrev` (`$2250,X`) are the links, `$FF`
ends the chain. The builder walks it head to tail, so far objects are written first and near ones
cover them. It is kept between ticks and repaired when something moves; it is never rebuilt.
(live: list dumps at six frames; the builder model in section 3 uses this order and matches every
list byte.)

**The key is an interval, not a point.** Each slot has `ObjDepthNear` (`$1CA4,X`) and `ObjDepthFar`
(`$26A4,X`). For a flier the far key is `A - B + k` and the near key is `far - depth` (5 for a shot,
`$12` for an enemy, `$0C` for a walker, 14-15 for the falcon). Since ground screen y is `B - A + k'`,
the key is just "how far up the screen the object's foot is". (live: `far = A - B + $6E` and
`near = far - 5` held for all 2,810 shot nodes logged; per class constants in section 2.)

**The comparison** (`ListInsertWalk`, `$9CC0`), for new object X against list node Y:

1. `Y.far < X.near`: Y is wholly nearer. Insert X before Y.
2. else `X.far < Y.near`: X is wholly nearer. Go on to the next node.
3. else the intervals overlap: compare `ObjC` (`$1EA4`, height for fliers, stacking rank 1-3 for the
   16-line pieces of a tall object). If `Y.C >= X.C` insert before Y, else go on. Higher draws later.

End of chain: append and set `ListTail`. (code)

**Four anchors.** Slots `$50-$53` are sentinel nodes that never move, with keys `$FC`, `$C8`, `$8C`,
`$50` (table `$9595`, set by `InitPlayfield` at `$9400`). `ListInsert` (`$9CA6`) first compares the
new far key with the anchors, nearest first, and starts the walk at the first anchor above it; only
if none is, at the head. The builder skips them (`CPY #$50`). (code; live: of 690 fresh inserts, 310
started at the head, and an insert examined 2.6 nodes on average.)

**Incremental repair** (`ListUpdate`, `$9D39`): called by whatever moved object X, with the new
keys in `$8A`/`$8E`.
- Near key unchanged: return.
- Moved nearer: if the next node's far key is still below the new near key, return.
- Moved farther: if the previous node's near key is still above the new far key, return.
- Otherwise unlink (`ListUnlink`, `$9D0B`) and re-insert, starting the walk at the neighbour, not
  at the head.

(live, 3,143 ticks: 11,647 calls, 3.7 a tick; 59% returned without touching a link; 41% relinked.)

**The scroll does not disturb it.** `ScrollObjects` (`$9DA3`) subtracts the same step from both
keys of every ground slot (`$10-$3A`), so ground objects keep their order among themselves. Only a
ground object whose next node is a flier or an anchor is re-sorted against it
(`ListResortAgainstNext`, `$9D86`; 3,933 calls in the same run). (live)

**Shadows need no sorting.** A shadow is inserted with both keys `$FE`, above every anchor, so all
shadows sit at the head and are drawn first, under everything. (live: every list dump; poking
`ListHead` to `$50` removed all eight shadow entries from the lists and nothing else: run
`pokehead`.)

**Cost.** (live, `tools/probe-list.lua` with the toolkit's cycle counter, 1,450 ticks, about 21
objects on the list, about 8 of them moving)
- PC range `$9CA6-$9D9C` (insert, walk, unlink, update, resort): mean **755 cycles a tick**, that is
  about 380 a frame, 5% of the tick's work. Fit: 262 + 46 per link write.
- By the code: `ListUpdate` returning early costs 41 cycles with the `JSR` (near key unchanged) or
  about 57 (changed, still in order). A relink is about 150-250.
- RAM: two link bytes, two key bytes and the rank/height byte per slot (84 slots here).
- Code: `$9CA6-$9D9C`, 247 bytes.

**It is a heuristic, not a strict order.** At the moment the builder started, 68 adjacent pairs in
1,467 builds (about 31,000 pairs) had the earlier node wholly nearer than the later one. They are
around the anchors and between fliers of equal rank with overlapping intervals: the early-out tests
look at one neighbour only. Nothing visible came of it in the snapshots looked at. (live count; the
reading of the cause is from code.)

**Safe against an asynchronous reader.** Every edit stores the forward link in an order that leaves
the chain walkable: unlink writes `prev.next` once; insert sets `X.next` before pointing the
previous node at X. The builder runs in the NMI and could, on an overrun, walk the list while the
main loop is mid-edit; it would see either the old or the new chain. (code; whether it was meant is
unknown.)

## 2. Three axes to the screen, shadows, collisions

**World axes.** `ObjA` (`$1F50,X`) runs along the flight path (the falcon sits at `$50`, things ahead
have larger A), `ObjB` (`$1E50,X`) across it (`$39-$79` playable), `ObjC` (`$1EA4,X`) is height
(5 = on the ground, `$2D` = ceiling).

**Projection** (live: `tools/fit_proj.py` over every node of 1,467 builds):

| | formula | shots (slots 1-4) | enemies (5-`$C`) | walkers (`$D-$F`) |
|---|---|---|---|---|
| screen x (`$25A5,X`) | `A + B + k1` | `$7B`, 2,810 of 2,810 | `$81` (or `$82` by frame) | `$84` |
| screen y (`$1FA4,X`) | `B - A - C + k2` | `$7E`, all | `$71`, 1,107 of 1,114 | `$71` |
| depth far (`$26A4,X`) | `A - B + k3` | `$6E`, all | `$7B` | `$78` |
| depth near (`$1CA4,X`) | `far - k4` | 5 | `$12` | `$0C` |

The constants are each picture's hot spot. Code: shots at `$E4A4-$E4E8`; enemies `EnemyScreenX/Y`,
`EnemyDepthKeys` (`$F1DD`, `$F1E7`, `$F1F5`); walkers `$F820`, `$F82B`, `$F83A`. No table, no
multiply: 160-mode pixels are twice as wide as tall, so `x = A + B`, `y = B - A` is already a 2:1
isometric view. The falcon (slot 0) follows the same form with constants that change with its pose.

**Height on screen.** Height only subtracts from screen y. Holding the falcon's `ObjC` at 5 by a
poke dropped it from y `$62` to `$88` onto its shadow (y `$8E`); the shadow did not move. 38 lines
for 40 of height: the landed pose has a different hot spot. (live: run `pokez`)

**Shadows.** (live)
- A shadow is a second object slot paired with its owner: falcon `$47`, shots `$48-$4B` (slot +
  `$47`), enemies `$3F-$46` (`dat_F120`).
- It gets the owner's graphics address and width, the same screen x, screen y = owner's y + C (the
  ground point), and palette 1. Checked on 5,390 owner/shadow pairs: x always equal; graphics equal
  except the falcon's wing-beat frames, which have their own flatter shadow pictures (`gfx + $34`);
  y equal for shots and enemies, within 5 lines for the falcon.
- Palette 1 is `$02`, `$02`, `$02` during play (`P1C1`/`P1C3` written at `$6523`/`$6528`, `P1C2`
  from a RAM shadow at `$9728`): any picture drawn in it is a flat dark silhouette. No shadow art
  is stored except those few falcon frames.
- Keys `$FE`/`$FE` put it under everything (section 1).
- Cost: one more object per flier in the list and in the zone lists (8 of 23 entries at frame
  1560).

**Collisions respect height.** Each collidable slot carries a box as absolute edges on all three
axes: A `$1B50,X`..`$1B8F,X`, B `$198F,X`..`$2000,X`, C `$1A50,X`..`$1A8F,X` (63 slots; note the `$3F`
stride between each pair). `CollidePointVsNeighbours` (`$D008`) tests a point (`$87`, `$85`, `$86`)
of object X for `min <= p < max` on the three axes and returns the hit slot's type byte
(`ObjActive`, `$1950,X`). Enemy boxes come from half-extent tables by size class (`$F260-$F277`).
(code)

**The depth list is the broad phase.** The test does not loop over all objects. It walks forward
from X while the next node's far key is at least `X.near - 15`, then backward from X while the
previous node's near key is at most `X.far + 15`, and stops. (code; live: 27,310 calls in 3,143
ticks looked at 7.5 candidates each on a list of about 21. PC range `$D000-$D0A0`: mean 2,023
cycles a tick.)

**The ground under an object** (`TileUnderObject`, `$D0CD`): the zone comes from screen y plus the
height (so the foot), the row pointer is read back out of that zone's tile header in the display
list, and the character is `(x + fine) / 8` along it. The display list is the map index. Used for
water, landing and walkers. (code; executed in every run)

## 3. The display-list builder

**Layout.** (live: `dlwalk.py` on RAM dumps; the model below)
- DLL at `$2750`, copied from a ROM template (`$96CE` for play, 20 entries; `$9208` for the title).
  Blank zones share the empty list at `$27A4`.
- Twelve playfield zones, 16 lines, 16-line holey DMA (`$4F`). List pages `$18-$1F`, `$26`, `$27`,
  `$22`, `$23` (table `$D2DB`), each list in bytes `$00-$4E` of its page; the rest of each page is
  game variables.
- Bytes 0-4 of every list: a 5-byte indirect header drawing 21 two-byte characters of ground
  (`lo, $60, hi, $4B, x`). It is permanent; only the scroll touches it.
- Objects are 4-byte headers from offset 5. Two zero bytes end the list.
- The fill pointers are the zero-page pointers themselves: `$B5+2z` is the low byte, `$B6+2z` the
  page, so an entry is written with `STA (ZoneFill0,X)` / `INC ZoneFill0,X` and no pointer set-up.

**`BuildDisplayLists` (`$FB0D`).**
1. `BuildBusy` (`$18E0`) = `$80`; all twelve fill bytes = 5.
2. For each node from `ListHead`: skip anchors; skip if x is `$A0-$DB` or y is `$B0-$F0`.
3. `y' = y - (ScrollFineY - 14)`. Zone = high nibble of y', line offset = low nibble. No table.
4. If that zone's fill is `$4B` or more (18 objects), drop the object.
5. Write `gfx lo`, `palette|width`, `ObjGfxPage + offset`, `x`.
6. If that page byte is at or above `ObjStraddlePage` (`$1D50,X`) the object crosses into the next
   zone: write it there too with `page - $10`. The art sits in `$A000-$AFFF` and `$C000-$CFFF`;
   whatever a zone's window reaches outside those lands in an odd 4K block and reads as zero.
   An object above the top zone (`y' >= $F1`) only gets its lower half, in zone 0.
7. `BuildFinish` (`$FAAF`): two zeros at every fill pointer; then every page byte in the bottom
   zone's list gets `ScrollFineY + 1` added (that zone is short and must show the top of its
   16-line cell); `BuildBusy` = 0.

**Checked** (live): `tools/check_build.py` replays steps 1-7 in Python from the list logged at the
fetch of `$FB0D` and compares with the twelve lists read at the fetch of the final `RTS`. 3,167
builds over two runs: 3,165 identical byte for byte. The two that differ are the bug below.

**What a zone holds.** Most entries in one zone: 13 (frame window 3600-7000). The cap of 18 was
never reached, so the drop path is (code) only. Because the list is far to near, the cap would drop
the nearest objects first, the falcon among them. 23-27% of entries are second halves.

**The straddle threshold** is the one refinement over the two-zone recipe already in the skills: a
16-line piece has `ObjStraddlePage = ObjGfxPage + 1` (crosses unless the offset is 0), a short one
such as a shot `$CC` against `$C0` (crosses only from offset 12), so short objects usually cost one
header. `$00` means "always both" (walkers).

**Cost** (live, `tools/probe-phase.lua`, 1,423 ticks): `839 + 146 x nodes` cycles a build; mean
3,894, 95th percentile 5,407, most 6,749 (37 nodes). By the code a one-zone object is about 148
cycles, a two-zone object about 228, a skipped node about 30.

**Where it runs.** Inside the NMI: the DLI at the top of the HUD (raster line 217) falls into
`VblankWork` (`$97E1`); on odd frames with `FrameReady` (`$FD`) set it calls `ScrollMapPixels` then
`BuildDisplayLists` (`$9885`/`$9888`). Builds started on lines 221-229 (a few at 247) and ended
between line 245 of the same frame and line 49 of the next. One set of lists, no double buffer.
(live)

**The safety net, and its bug.** The first playfield DLI (`DLI_PlayfieldTop`, `$9717`, line 41)
tests `BuildBusy`. If the builder is still running it calls `TerminateAllZoneLists` (`$9C68`), which
writes two zeros at each of the twelve fill pointers so MARIA never meets a half-written entry; the
builder then carries on over them. (live: taken at frames 4661 and 5125 of 6,301, DLI at line 43,
builds ending at lines 48 and 49.)
- **Bug** (live, both times): at that moment the builder was in step 7's fix-up, which reuses the
  bottom zone's fill pointer `$CB` as its walking pointer. The DLI zeroed the entry being walked,
  which ended the bottom zone's list there: 3 objects and then 2 were missing from the bottom zone
  for that tick. `check_build.py` shows the zeroed bytes (`$64,$3C` and `$00,$7C` became `0,0`).
- Lesson: an interrupt that patches up shared state must not trust a pointer the interrupted code
  re-purposes.

## 4. The diagonal scroll

All (code) from `$D119-$D34C`, with a model checked (live) by `tools/check_scroll.py`: 6,301 frames,
0 mismatches outside a 69-frame restart window (frames 2869-2937, the pre-roll below).

**Storage.** A ring of 12 rows of 33 characters in RAM (`$2400`, `+$21` ... `$24C6`, then `$2500` ...
`$2584`; tables `$D2C3`/`$D2CF`). Rows never cross a page. Each row is copied once from ROM map data
when it enters at the top. Characters are two bytes wide in 160A (`CTRL = $50`), 8 pixels by 16
lines, at `CHARBASE $80`.

**One scroll pixel** (`ScrollMapPixels`, once per pixel of the tick's step):
- *Down* (`ScrollMapDown1`, `$D12F`): `ScrollFineY` (`$A1`) counts -1..14. The first playfield zone's
  DLL byte becomes `$C0 | fine` (fine+1 lines), the last one's `$C0 | (14 - fine)` (15-fine lines),
  so the eleven zones between slide down a line. The short last zone must show the top of its
  characters, so its DLI loads `CHARBASE` from `$EF` = `$81 + fine`. When the last zone is one line
  the two bottom DLIs are merged (`NextDliLo` = `$76` instead of `$50`, and the DLI bit at `$277A`
  cleared).
- *Left* (`ScrollMapLeft1`, `$D2F5`): `DEC` the x byte of all twelve tile headers (twelve absolute
  `DEC`s). For zones 6-11, every eighth pixel (`ScrollFineX`, `$A5`) x goes back to 0 and the
  header's low byte is `INC`ed: one character further along the row.
- *Every 16th pixel* (`$D193`): the twelve headers (lo, hi, x) are copied down one zone, the next
  ring row is filled from ROM (33 bytes) and zone 0's header points at it with x = `$5A`. The
  top-zone-absent state (`fine = -1`) re-splits the blank lines above (8+9+8 instead of 16+9+n).

**Why x starts at `$5A`.** A row enters at the top with its left edge at x 90 and slides left 16
pixels per zone; by zone 6 it has reached the left edge and starts dropping characters. So the
top-left triangle of the screen has no tiles at all, only the background colour. The sand is the
background; tiles are only features (water, pebbles). 21 characters shown of 33 stored = 12
characters dropped over the six lower zones.

**Objects follow by subtraction.** `ScrollObjects` (`$9DA3`) applies the same step to each ground
slot: screen y + d, screen x - d, `ObjA`, both A box edges and both depth keys - d. Ground objects
always land on offset 0 of a zone because the grid itself slides, so a 16-line piece of an obelisk
costs one header.

**Cost** (live, per tick):
- `ScrollMapPixels`: median 18 cycles (no step), 95th percentile 282, most 1,813 (a 16th-pixel
  step with its row copy).
- `ScrollObjects`: median 51, 95th percentile 4,214, most 5,447: about 110-130 cycles per ground
  object on a tick that scrolls. This is the dear part: seven bytes per object.
- MARIA: 13,300 cycles of DMA a frame, 45% of the frame, mostly the 21 two-byte characters on 176
  lines.

**The opening screen** (`PreRollScroll`, `$95A7`): with the picture off, the normal scroll, spawn
and map routines are run 241 times, so the screen fills by the same code that later scrolls it.
(code; live only as the header churn in frames 2869-2937)

## 5. Spawns and difficulty

All (code) unless marked.

**Terrain.** The ground is a chain of segments. `MapSegment` (`$AB`) is one of 14 types; a segment is
2-7 rows (`$D2E7`). Per type, tables at `$D34D-$D3BC` give the row data and three bytes per row of
"cells free for building" (24 bits). The next type comes from `PickNextMapSegment` (`$6312`): tables
`$635D-$638A` indexed by the low bits of a per-row Fibonacci state (`$71-$74`, stepped in
`RowCounterAndCheckpoint`, `$638B`). Every 16 rows the row counter, that state and the segment
position (11 bytes) are saved in one of two alternating checkpoint slots (`$2100-$212B`), and
`$6081` restores them after a death: the same desert comes back.

**Ground objects.** `SpawnOnNewRow` (`$61C9`) runs when a new row has entered. An object type has a
footprint (cells wide `$648B`, rows deep `$649B`); `ClaimRowCells` (`$63F1`) checks and clears those
bits in the rows' masks (kept in three 4-deep FIFOs `$18AB`/`$18AF`/`$18B3` beside the row
pointers), and refuses the spawn if a cell is taken or not buildable. Slots come from a ring of
free slot numbers (`GroundSlotAlloc`/`Free`, `$9E53`/`$9E6E`, 43 slots `$10-$3A`).

**Enemy waves** (`WaveScheduler`, `$60CC`).
- `WavePressure` (`$77`) starts at `$20` and gains 3 per wave group, clamped at `$C0`. (live:
  `$23`, `$26`, `$29`, `$2C` at about 1,100-frame steps.)
- Enemy type for the group: `$6177[pressure >> 3]` (32 entries, high nibble), with 2-5 waves.
- Delay between waves `$6167[pressure >> 5]` = 12,5,4,3,2,1,1,1; between groups
  `$616F[...]` = 20,10,8,5,4,3,2,1 (units of 16 ticks).
- A wave is 1-4 enemies (`SpawnEnemyRandom`, `$F020`): B and height picked from two 16-entry tables
  (`$F000`, `$F010`), A = `$D2` (far ahead), limited by `EnemyBudget` (`$EB`, 8).
- Per enemy type (16): script start, palette|width, size class (`$F4FC`, `$F50C`, `$F51C`).
- The level's length before the sphinx: 16-bit row counts by level + difficulty, clamped at 7
  (`$621E`). (hint: read from the compare at `$61E7`, not watched.)

**Enemy behaviour is byte-code** (`EnemyScriptStep`, `$F3DC`; scripts `$F530-$F608`, 217 bytes).
High nibble = opcode, low nibble = operand; a step runs until a yield; each enemy steps every
fourth tick, two enemies per tick.

| op | handler | meaning |
|---|---|---|
| 0, 1, 2 | `$F3FF`, `$F40D`, `$F41B` | set velocity on B, C, A (signed nibble) |
| 3 | `$F478` | yield |
| 4 | `$F429` | steer B toward the falcon at speed n, dead band of 5 |
| 5 | `$F450` | steer height toward the falcon's, same |
| 6 | `$F479` | loop back n+1 bytes |
| 7 | `$F48C` | while A is beyond threshold n (`$F52C`: `$B0,$A0,$90,$80`) jump to the next byte's address, else skip it |
| 8 | `$F4C1` | fire shot type n |
| 9 | `$F485` | set animation n |
| A | `$F4B5` | jump |
| B | `$F4A8` | random branch on mask n |

Velocities are added each tick to the position and to both box edges on that axis
(`EnemyMoveAndScript`, `$F34A`). Opcodes 0-6 were seen executing in the traced run; 7-B were added
as entries by hand. All meanings are read from code.

**Scroll speed** (`ScrollSpeed`, `$A6`) is the difficulty lever for the ground: a base from a
ladder of level compares (`$E1A0-$E1BC`), plus the difficulty switch, capped by height above
ground (a low falcon flies slowly).

## 6. Frame architecture

(live unless marked; raster lines of MAME's 263-line frame, from register-write taps)

- **NMI vector is `$0040`**: a `JMP` kept in zero page. Each handler stores the next handler's low
  byte into `$41` (all handlers in `$97xx`/`$98xx`).
- **Chain during play:** line 41 `DLI_PlayfieldTop` (`$9717`: `CTRL $50`, four colours from RAM
  shadows, `BACKGRND`, the late-build check) -> the bottom zone's line (209 at fine 7)
  `DLI_BottomZoneCharbase` (`$9750`) -> line 217 `DLI_Hud` (`$97CC`: `CHARBASE $80`, `CTRL $43`,
  HUD colours, then `VblankWork`) -> lines 234 and 257 `DLI_Resync` (`$9763`): two `WSYNC`s, then
  the first handler is re-armed only if `MSTAT` shows vblank twice.
- **The frame's own work starts at the HUD, not at vblank:** sound and timers every frame, the map
  scroll and list build every second frame, from line 217. That gives the builder the HUD's lines
  as well as vblank.
- **Main loop** (`MainLoop` `$9982`, `JMP (MainVecLo)` at `$99EF`; play state `GameTick` `$9B61`):
  waits until `FrameCount` (`$A2`) is 2 past `TickFrame` (`$A3`), spinning in `Random` (`$9C0D`);
  waits for the NMI to clear `FrameReady`; scrolls the objects; sets `FrameReady`; runs 16 logic
  routines. So the tick is 30 Hz and the lists shown are one tick behind the logic.
- **Budget per tick** (two frames, about 59,700 cycles): DMA 25,400; work mean 13,760, 95th
  percentile 20,450, most 27,090; the rest idle. The work would not fit one frame, hence 30 Hz.
  Largest items: the build 3,894, `FalconControl` (`$E000`, with shots and their collisions) 2,671,
  `EnemiesTick` (`$F128`) 2,054, `ScrollObjects` 1,370, the three sound routines about 950.

## 7. Other things noticed

- **Code lives where MARIA sees holes.** Sprite art is in `$A000-$AFFF` and `$C000-$CFFF`; the odd
  4K blocks either side (`$9000`, `$B000`, `$D000`) hold code and tables. (code: the gap map)
- **Asserts shipped:** `$F158` `BNE` to itself if an enemy's state is not 1 or 3; `$FEE2` `BMI` to
  itself if the animator pool underflows. (code)
- **The random number depends on idle time:** `Random` adds `FrameCount` and two state bytes and is
  called from the idle loop and from the top DLI, so its sequence follows frame timing. (code)
- **Free-slot ring:** freed ground slots go to the back of a 43-entry ring and are checked against
  the last three entries (a double-free guard). (code)
- **`$98CF`** calls `$3FEB`, below the cartridge: taken to be the High Score Cart. (hint)

## 8. Dead ends and corrections

- First reading of the dump had the zone bytes at `$B6` as (page, fill) pairs; they are pointers
  starting at `$B5` (fill is the low byte).
- The tile rows looked like a 13-row ring with strides of 33, 34 and 35; the code shows 12 rows of
  33 in two pages, and the odd strides are the low-byte `INC`s of the lower six zones.
- The obelisk's 16-line pieces looked pre-cut and placed by a separate path. They are ordinary
  objects that sit at offset 0 because the grid slides.
- Palette 0 was taken for the shadows at first; palette 1 is. Read off the screenshot.
- The depth key was guessed as "A plus or minus 1" from one frame (B happened to be `$68`); it is
  `A - B + k`.
- `cyclebudget.lua` showed about 1,800 cycles of builder in every frame. It builds every second
  frame; MAME's frame callback falls in the middle of the build.
- `check_build.py`'s first "build length" used that frame count and gave 83 lines; the start and
  end raster lines are the usable figure.
- An order check sampled at the end of each frame found "violations" in 75 ticks; most were the
  list caught mid-update. Sampled at the builder's entry: 68 pairs, as in section 1.
- A RAM dump at the end of an odd frame holds half-built lists (run `pokehead`, frame 1499).
- `probe-phase.lua`'s first NMI checkpoints were two bytes off (the build and map scroll went to
  "other"); fixed and rerun.
- The first 1,467 builds never took the late-build path, and it was first noted as code only. A
  run twice as long took it twice and showed the bug.
- Toolkit: `exectrace.lua` labels a linear cart's code `b0:`/`f7:`; the log was rewritten to `rom:`
  before `dyn.py`. `dlitimes.lua` printed the zones but no NMI lines (the vector points into RAM;
  not diagnosed), so the lines above come from `tools/probe-regs.lua`.

## 9. Coverage, and what was not determined

- **Disassembly:** 13,378 of 49,152 bytes are traced code (27.2%, 6,152 instructions): the static
  trace from reset plus 4,251 instructions seen executing over about 5,800 frames of scripted play,
  plus eleven entries added by hand. No remaining gap contains a `JSR` to a known routine, so this
  is believed to be nearly all of the code; the other 73% is graphics, map rows, sound and tables.
  The rebuild is byte-identical.
- **Read closely:** the list, builder, scroll, projection, collision test, enemy scripts, wave
  scheduler, frame chain (about a quarter of the code). **Skimmed or not read:** the falcon's
  control beyond its outline, ground gun emplacements (`$B03A-$B8FF`), the sphinx and bonus
  rounds, hieroglyph powers, scoring, the sound driver (`$56B4`, `$579D`, `$5840`), title and High
  Score Cart code, two-player handling.
- **Not determined:** the map row data and its 24-bit masks beyond their pointers; what
  `$4000-$4FFF` draws (never fetched in play); the DMA load of the busiest line; the drop path at
  18 objects in a zone; whether real hardware shows the bottom-zone bug (MAME only, no Pocket
  run); PAL; why `dlitimes.lua` saw no NMI.
- **Runs** (all under `work/runs/`, made with `tools/run.py`): `first` (snapshots, dumps), `xt1`
  (execution trace), `list1`/`list2` (list order, cycle ranges), `build1`/`build2` (builder model),
  `phase1` (cycles per phase), `scroll1` (scroll model, wave pressure), `hits1` (call counts),
  `regs0`/`regs1` (register writes), `pokehead`, `pokez` (pokes), `dli1`.
