# Desert Falcon (Atari 7800) disassembly notes

An annotated disassembly project for *Desert Falcon* (NTSC, Atari, 1987; `Desert Falcon (NTSC) (Atari) (1987) (A1DC0899).a78`, 48K).

## How this was made, and how far to trust it

This is the output of **one automated research pass** on 2026-11-18: a single AI agent
session (Claude, working through the a7800-toolkit and MAME) given a list of questions and
about half an hour, not a long-running hand disassembly like
[galaga-7800-disassembly](https://github.com/Miasmark/galaga-7800-disassembly) and its
siblings. A second session then checked the report's main tables and routines against the
ROM's bytes; they matched. Nothing here was checked on a console.

Treat a **live** tag as "one agent saw this in MAME once", a **code** tag as a reading, and
the coverage figures below as what the tracer reached, not what was understood.

## Effort: a deep single-game pass on four questions

| | |
|---|---|
| Session | one agent, about 29 minutes, 104 tool calls |
| Questions asked | depth order; the three axes to the screen, shadows; the display-list builder; the diagonal scroll; spawns and difficulty; the frame |
| Coverage | 13,378 of 49,152 bytes traced as code (27.2%); no remaining gap holds a call to a known routine, so probably nearly all the code. Rebuild byte-identical |
| Read closely | about a quarter of the code: the list, the builder, the scroll, the projection, the collision test, the enemy scripts, the wave scheduler, the frame chain |
| Skimmed or not read | the falcon's control beyond its outline, gun emplacements, the sphinx and bonus rounds, hieroglyph powers, scoring, sound, title and High Score Cart code |
| Live checks | a model of the builder against 3,167 builds (3,165 byte-identical; the other two are a bug it found), a scroll model over 6,301 frames, the projection fitted on every logged node, 76 labels, 74 RAM names |
| Not determined | the drop path at 18 objects in a zone (never reached); the map row data; whether hardware shows the bug |

## What is here, and what is not

- `annotations.json`: entry points, labels, RAM names, data blocks and comments, in the
  [a7800-toolkit](https://github.com/Miasmark/a7800-toolkit)'s format.
- `docs/FINDINGS.md`: what the code does, with addresses, record formats and an evidence
  tag on every claim: **live** (watched in MAME: a tap, a trace, a RAM model, a poke that
  changed behaviour), **code** (read from the listing only), **hint** (a guess). Dead ends
  and corrections are kept in it.
- `tools/`: the probes and scripts the findings were made with.

**No ROM is here, and no listing.** A listing is the game's machine code in readable form;
it is rebuilt from `annotations.json` and your own legally owned dump with the toolkit's
`disasm.py`, and checked byte for byte with its `verify.py`. Captures, memory dumps,
renders of the graphics and traces are left out for the same reason.

## Running the tools

The scripts look for three things in the environment:

| Variable | What | Default |
|---|---|---|
| `A7800_ROMS` | the folder with your ROM dumps, named as below | `roms` |
| `A7800_TOOLKIT` | the a7800-toolkit's `tools` folder | `a7800-toolkit/tools` |
| `A7800_MAME` | a MAME with the Atari 7800 driver | `a78.exe` |

The live runs were made on [Miasmark/mame-Atari8bit7800](https://github.com/Miasmark/mame-Atari8bit7800),
windowless (`-video none -sound none -nothrottle`).

## Licence

MIT (see `LICENSE`) for the annotations, the findings and the tools. It does not cover the
games, which belong to their owners; nothing of theirs is distributed here.

## The session's own notes

A reading of the retail cartridge `Desert Falcon (NTSC) (Atari) (1987) (A1DC0899).a78` (48K, no
banking, TIA sound), made with the a7800 toolkit to find techniques worth reusing. The cartridge is
not in this folder's tracked files: `work/` holds a copy for the tools and must not be published.

## What is here

- `annotations.json`: every name, note and data block. The listing is generated from it.
- `docs/FINDINGS.md`: what the game does, with addresses and evidence tags.
- `tools/`: the windowless MAME harness and the probes and checkers used.
- `work/`: the cartridge copy, the generated listing (`work/src/rom.asm`), MAME run folders
  (`work/runs/<name>`). Disposable; contains cartridge bytes.

## Regenerating the listing

With `T` the toolkit folder (`Documents\Atari 7800\a7800-toolkit`):

    python -I tools/annotate.py
    python -I T/tools/disasm.py work/df.a78 -c annotations.json -o work/src --cycles
    python -I T/tools/verify.py work/df.a78 -d work/src        (must say ROUND-TRIP PASSED)
    python -I tools/lst.py FB0D FBD2                           (a compact slice of the listing)

Coverage: 13,378 of 49,152 bytes traced as code (27.2%); the rest is graphics, map rows, sound and
tables. See FINDINGS section 9 for what was read closely and what was not.

## Running the game without a window

`tools/run.py NAME` starts the user's MAME fork (`Documents\mame-fork\a78.exe`) with `-video none
-sound none -nothrottle -bios skip`, its own run folder `work/runs/NAME` (cfg, nvram, snapshots,
`ui.ini` with `skip_warnings 1`), a scripted input and an optional probe:

    python -I tools/run.py demo --script "200:-:0;10:-:1;200:-:0;10:-:1;300:-:0;300:r:1" --snaps 900 --dumps 900

The script is `frames:stick:buttons;...` (stick letters l r u d or `-`; buttons 1 = fire, +8 Select,
+16 Reset). Two presses of fire about 200 frames apart start a one-player game. `--peek` logs RAM
bytes per frame, `--pokes` writes or holds bytes, `--dumps` writes RAM `$0000-$27FF` at a frame's end.

| tool | what it answers |
|---|---|
| `probe-build.lua` + `check_build.py` | does a Python model of the display-list builder reproduce the game's lists? (it does) |
| `fit_proj.py` | the constants in screen x = A + B + k, screen y = B - A - C + k, depth = A - B + k |
| `probe-list.lua` + `analyze_list.py` | the sorted list each frame, link writes, cycles in chosen PC ranges |
| `probe-phase.lua` | executed cycles per phase of the 30 Hz tick |
| `check_scroll.py` | the diagonal scroll model against a `--peek` log |
| `probe-pchits.lua` | how often chosen routines run |
| `probe-regs.lua` | MARIA register writes with their raster line |

A RAM dump taken at the end of an odd frame holds half-built lists: the builder runs across MAME's
frame boundary. Use even frames, or the taps in `probe-build.lua`.
