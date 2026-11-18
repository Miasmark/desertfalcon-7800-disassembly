"""Write this project's names, notes and data blocks into annotations.json (idempotent).
python -I tools/annotate.py          then regenerate with the toolkit's disasm.py -c annotations.json
All human judgement lives here so the listing stays disposable. Evidence tags as in docs/FINDINGS.md."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "annotations.json")
a = json.load(open(PATH))

ENTRIES = ["rom:98A1", "rom:98CF", "rom:F485", "rom:F48C", "rom:F4A8", "rom:F4B5", "rom:F4C1", "rom:9A26",
           "rom:9B46", "rom:9C1D", "rom:9C68"]
for e in ENTRIES:
    if e not in a["entries"]:
        a["entries"].append(e)

LABELS = {
    "rom:98DE": "ENTRY_Reset",
    "rom:9016": "InitTitleScreen",
    "rom:93E1": "InitPlayfield",
    "rom:95A7": "PreRollScroll",
    "rom:9964": "WaitVblankThenLoop",
    "rom:9982": "MainLoop",
    "rom:99EF": "MainDispatch",
    "rom:9B61": "GameTick",
    "rom:9C0D": "Random",
    "rom:9C1D": "ReadInputs",
    "rom:9C68": "TerminateAllZoneLists",
    "rom:9CA6": "ListInsert",
    "rom:9CC0": "ListInsertWalk",
    "rom:9D0B": "ListUnlink",
    "rom:9D39": "ListUpdate",
    "rom:9D86": "ListResortAgainstNext",
    "rom:9DA3": "ScrollObjects",
    "rom:9E53": "GroundSlotAlloc",
    "rom:9E6E": "GroundSlotFree",
    "rom:9717": "DLI_PlayfieldTop",
    "rom:9750": "DLI_BottomZoneCharbase",
    "rom:975D": "DLI_Resync_To9794",
    "rom:9763": "DLI_Resync_To9717",
    "rom:9766": "DLI_ResyncTail",
    "rom:9776": "DLI_BottomZoneAndHud",
    "rom:9794": "DLI_TitleTop",
    "rom:97B9": "DLI_TitleText",
    "rom:97CC": "DLI_Hud",
    "rom:97E1": "VblankWork",
    "rom:987C": "VblankBuildGate",
    "rom:98A1": "DLI_98A1",
    "rom:98CF": "DLI_98CF_HSC",
    "rom:D000": "CollideIfMoved",
    "rom:D008": "CollidePointVsNeighbours",
    "rom:D0A1": "FindLandingTarget",
    "rom:D0CD": "TileUnderObject",
    "rom:D0D4": "TileUnderPoint",
    "rom:D119": "ScrollMapPixels",
    "rom:D12F": "ScrollMapDown1",
    "rom:D2F5": "ScrollMapLeft1",
    "rom:E000": "FalconControl",
    "rom:E411": "PlayerShots",
    "rom:F020": "SpawnEnemyRandom",
    "rom:F054": "SpawnEnemy",
    "rom:F128": "EnemiesTick",
    "rom:F1DD": "EnemyScreenX",
    "rom:F1E7": "EnemyScreenY",
    "rom:F1F5": "EnemyDepthKeys",
    "rom:F207": "EnemyAnimate",
    "rom:F34A": "EnemyMoveAndScript",
    "rom:F3DC": "EnemyScriptStep",
    "rom:F3FF": "Op0_SetVelB",
    "rom:F40D": "Op1_SetVelC",
    "rom:F41B": "Op2_SetVelA",
    "rom:F478": "Op3_Yield",
    "rom:F429": "Op4_HomeB",
    "rom:F450": "Op5_HomeC",
    "rom:F479": "Op6_LoopBack",
    "rom:F48C": "Op7_BranchIfANear",
    "rom:F4C1": "Op8_Fire",
    "rom:F485": "Op9_SetAnim",
    "rom:F4B5": "OpA_Jump",
    "rom:F4A8": "OpB_RandomBranch",
    "rom:F6BA": "WalkersTick",
    "rom:F820": "WalkerScreenX",
    "rom:F82B": "WalkerScreenY",
    "rom:F83A": "WalkerDepthKeys",
    "rom:FAAF": "BuildFinish",
    "rom:FB0D": "BuildDisplayLists",
    "rom:FB35": "BuildNextNode",
    "rom:FBD3": "AnimateGroundObjects",
    "rom:60CC": "WaveScheduler",
    "rom:61C9": "SpawnOnNewRow",
    "rom:6312": "PickNextMapSegment",
    "rom:638B": "RowCounterAndCheckpoint",
    "rom:63F1": "ClaimRowCells",
}
a["labels"].update(LABELS)

RAM = {
    "40": "NmiJmp", "41": "NmiVecLo", "42": "NmiVecHi", "49": "MainVecLo", "4A": "MainVecHi",
    "4E": "RandA", "4F": "RandB", "58": "Player", "77": "WavePressure",
    "A1": "ScrollFineY", "A2": "FrameCount", "A3": "TickFrame", "A5": "ScrollFineX", "A6": "ScrollSpeed",
    "AB": "MapSegment", "AC": "MapSegRow", "B0": "MapSegFlag", "B1": "MapSegNext",
    "B5": "ZoneFill0", "B6": "ZonePage0", "CB": "ZoneFill11", "CC": "ZonePage11",
    "CD": "ListHead", "D0": "ListTail", "D1": "ScrollStep", "D2": "TickCount",
    "D3": "EnemyState", "EB": "EnemyBudget", "ED": "MapRingRow", "EE": "BackgrndShadow",
    "EF": "BottomZoneCharbase", "F0": "NextDliLo", "F1": "NextDliHi", "FD": "FrameReady",
    "18DE": "ScrolledFlag", "18DF": "ScrolledRowFlag", "18E0": "BuildBusy",
    "1950": "ObjActive", "198F": "ObjBoxBMin", "2000": "ObjBoxBMax",
    "1A50": "ObjBoxCMin", "1A8F": "ObjBoxCMax", "1B50": "ObjBoxAMin", "1B8F": "ObjBoxAMax",
    "1C50": "ObjGfxPage", "1CA4": "ObjDepthNear", "1D50": "ObjStraddlePage",
    "1E50": "ObjB", "1EA4": "ObjC", "1F50": "ObjA", "1FA4": "ObjScreenY",
    "2250": "ObjPrev", "22A4": "ObjGfxLo", "2378": "ObjPalWidth", "23CC": "FreeSlotRing",
    "23F7": "FreeSlotGet", "23F8": "FreeSlotPut", "25A5": "ObjScreenX", "2650": "ObjNext",
    "26A4": "ObjDepthFar", "2750": "DLL",
    "1AE0": "EnemyVelB", "1AE8": "EnemyVelC", "1AF0": "EnemyVelA", "1AF8": "EnemyScriptPc",
    "18A1": "RowSrcLoFifo", "18A5": "RowSrcHiFifo", "18AB": "RowCellsFifo0", "18AF": "RowCellsFifo1",
    "18B3": "RowCellsFifo2", "19D1": "WaveTypeCount", "19D2": "WaveDelay", "19D3": "WaveSpawnsLeft",
    "19D4": "WaveEnemyType",
}
a["ram"].update(RAM)

HEADERS = {
    "rom:FB0D": [
        "BuildDisplayLists (live: tools/check_build.py reproduces all 12 lists byte for byte over 1,467 builds).",
        "Runs inside the bottom-of-playfield NMI on odd frames when FrameReady ($FD) is set.",
        "Resets the 12 zone fill pointers to 5 (past the 5-byte tile header), then walks the depth-sorted",
        "linked list from ListHead ($CD) through ObjNext ($2650,Y): far first, near last.",
        "Per node: skip if x in $A0-$DB or y in $B0-$F0; y' = y - (ScrollFineY - 14); zone = y' >> 4,",
        "line offset = y' & 15; header = gfx lo, palette|width, ObjGfxPage + offset, x. If that page is",
        ">= ObjStraddlePage the object also goes into the next zone with page - $10 (16-line holey DMA",
        "blanks the rest). A zone whose fill is >= $4B (18 objects) drops the object.",
        "BuildFinish ($FAAF) writes a two-byte terminator in every zone and adds ScrollFineY+1 to every",
        "page in the bottom zone (a short zone shows the top of its 16-line cell).",
    ],
    "rom:9CA6": [
        "ListInsert: insert object X with depth interval near=$8A, far=$8E (far end first in the list).",
        "Starts at one of four sentinel nodes (slots $50-$53, keys $FC $C8 $8C $50) or at the head, then",
        "walks: before Y if Y.far < X.near; past Y if X.far < Y.near; intervals overlap -> the one with",
        "the larger ObjC ($1EA4, height or stacking rank) goes later (drawn on top).",
        "Forward links are written in an order that keeps the chain walkable at every instant.",
    ],
    "rom:9D39": [
        "ListUpdate: object X moved; new keys in $8A/$8E. Returns at once if the near key did not",
        "change, or if the neighbour on the side it moved toward is still in order; otherwise unlinks",
        "and re-inserts starting from that neighbour (not from the head).",
    ],
    "rom:9DA3": [
        "ScrollObjects: the tick's scroll step d (ScrollSpeed/2 with a half-step carry) applied to every",
        "ground slot ($10-$3A), walking the list backward from ListTail through ObjPrev: screen y += d,",
        "screen x -= d, world A, both A box edges and both depth keys -= d. A ground object whose next",
        "node is not a ground slot is re-sorted against it. Objects scrolled off (y $B0-$DF) are freed.",
    ],
    "rom:D119": [
        "ScrollMapPixels: d times ScrollMapDown1 + ScrollMapLeft1 (the tile field's diagonal scroll).",
        "Down: ScrollFineY -1..14 sets the top zone's height (DLL $2756 = $C0|fine), the bottom zone's",
        "(DLL $2777 = $C0|14-fine) and its CHARBASE ($EF = $81+fine). Every 16th pixel the twelve zone",
        "headers (lo, hi, x) move down one zone and a new 33-character row is copied into the ring",
        "($2400.., 12 rows) for zone 0 at x=$5A.",
        "Left: DEC x in all twelve headers; zones 6-11 wrap x to 0 every 8 pixels and INC the header's",
        "low byte (rows never cross a page, so no carry).",
    ],
    "rom:D008": [
        "CollidePointVsNeighbours: point (A=$87, B=$85, C=$86) of object X against the boxes of its",
        "neighbours on the depth list only: forward while their far key >= X.near-15, then backward",
        "while their near key <= X.far+15. Box test on all three axes (A, B and height C).",
        "Returns the hit object's ObjActive byte (its type), 0 for none.",
    ],
    "rom:D0CD": [
        "TileUnderObject: which ground character is under object X. Finds the zone from screen y",
        "(plus height, so the ground point), reads that zone's tile header back out of its display",
        "list to get the row pointer, and indexes it with (x + fine)/8.",
    ],
    "rom:F3DC": [
        "EnemyScriptStep: byte-code at dat_F530, high nibble = opcode (table $F4E4/$F4F0), low nibble",
        "= operand. Runs until Op3_Yield. Each enemy gets a step every 4th tick.",
    ],
    "rom:97E1": [
        "VblankWork: reached from the DLI at the top of the HUD (line 217). Sound and timers every",
        "frame; on odd frames with FrameReady set, ScrollMapPixels then BuildDisplayLists.",
    ],
    "rom:9717": [
        "DLI_PlayfieldTop (line 41): CTRL=$50, four colours from RAM shadows, arms the next DLI from",
        "NextDliLo ($F0). If BuildBusy ($18E0) is still set the builder has run into the picture:",
        "TerminateAllZoneLists ends every list where it stands so MARIA never reads a half entry.",
    ],
    "rom:9B61": [
        "GameTick: one tick per two frames (FrameCount - TickFrame >= 2). Idles in Random meanwhile.",
        "Waits for the NMI to have consumed FrameReady, scrolls the objects, sets FrameReady, then",
        "runs the logic. The lists for this tick are built by the NMI two frames later.",
    ],
}
a["headers"].update({k: chr(10).join(v) for k, v in HEADERS.items()})

COMMENTS = {
    "rom:FB65": "cap: fill >= $4B means 18 objects already; this one is dropped (live: never reached, max 10)",
    "rom:FB7F": "carry = page >= ObjStraddlePage: the object spills into the next zone",
    "rom:FBAD": "carry is clear here, so this is page - $10: the lower half's window",
    "rom:9CB2": "sentinels $53..$50: start at the first whose key is above the new far key",
    "rom:9CCF": "overlap: compare ObjC (height / stacking rank)",
    "rom:E4A4": "screen x = B + A + $7B (live: 100% of 2,810 shot nodes)",
    "rom:E4B3": "ground y = B - A + $7E -> the shadow slot (slot + $47); object y = that - C",
    "rom:E4D9": "depth far key = A - B + $6E, near = far - 5",
    "rom:E4C7": "shadow keys $FE/$FE: ahead of every sentinel, so drawn first, under everything",
    "rom:F156": "state must be 1 or 3: BNE to itself is an assert left in the shipped game",
    "rom:FEE2": "pool underflow assert: hangs here",
    "rom:9B8A": "set before the logic runs: the next odd-frame NMI may build from this tick's state",
    "rom:6100": "WavePressure += 3 per wave group, clamped at $C0",
}
a["comments"].update(COMMENTS)

BLOCKS = [
    ("rom:9208", 75, "DLL template for the title screen (25 entries), copied to $2750 by InitTitleScreen"),
    ("rom:96CE", 60, "DLL template for play (20 entries), copied to $2750 by InitPlayfield"),
    ("rom:9595", 4, "sentinel depth keys $FC $C8 $8C $50 for list slots $50-$53"),
    ("rom:D2BC", 7, "row offsets inside a map segment (multiples of 33)"),
    ("rom:D2C3", 12, "ring row address low bytes (12 rows of 33 characters at $2400/$2500)"),
    ("rom:D2CF", 12, "ring row address high bytes; the last byte doubles as dat_D2DA[0]"),
    ("rom:D2DB", 12, "zone list pages: $18-$1F, $26, $27, $22, $23"),
    ("rom:D2E7", 14, "rows per map segment type, minus one"),
    ("rom:D34D", 112, "map segment tables, 14 entries each: row data lo/hi, and three per-row cell-mask tables lo/hi"),
    ("rom:F000", 16, "enemy spawn B (cross-track) choices"),
    ("rom:F010", 16, "enemy spawn C (height) choices"),
    ("rom:F25C", 4, "enemy size class -> first animation script index"),
    ("rom:F260", 24, "enemy collision box half extents by size class: B-,B+ C-,C+ A-,A+ (4 bytes each)"),
    ("rom:F4E4", 24, "enemy script opcode handlers, low bytes then high bytes (12 opcodes)"),
    ("rom:F4FC", 48, "per enemy type (16): script start, palette|width, size class"),
    ("rom:F52C", 4, "Op7 A thresholds"),
    ("rom:F530", 217, "enemy behaviour scripts (nibble opcodes), to $F608"),
    ("rom:6167", 48, "wave pacing: delay within a group (8), delay between groups (8), enemy type by pressure (32)"),
    ("rom:621E", 16, "per level+difficulty (clamped at 7): 16-bit row count before the sphinx appears"),
    ("rom:635D", 46, "map segment succession tables"),
    ("rom:648B", 48, "ground object footprints: cells wide (16), rows deep (16), clear masks, bit masks"),
]
have = {b["loc"] for b in a["blocks"]}
for loc, ln, note in BLOCKS:
    if loc not in have:
        a["blocks"].append({"loc": loc, "len": ln, "note": note})

a["notes"]["rom"] = (
    "Desert Falcon (NTSC) (Atari) (1987) (A1DC0899).a78 -- linear 48K, TIA sound.\n"
    "Vectors: NMI $0040 (a JMP kept in RAM, its low byte rewritten by each DLI), RESET $98DE, IRQ $0000.\n"
    "Layout: $4000-$4FFF graphics; $5000-$67xx code and sound; $6786-$8FFF data and the two character\n"
    "sets ($80xx, $88xx); $9000-$9E9A code; $A000-$AFFF and $C000-$CFFF sprite art (even 4K blocks, so the\n"
    "odd blocks either side read as zero under 16-line holey DMA); $B000-$B92A, $D000-$DFFF, $E000-$FFFF\n"
    "code and tables: the code sits in the blocks MARIA sees as holes.\n"
    "See docs/FINDINGS.md.")
json.dump(a, open(PATH, "w"), indent=2)
print("annotations written:", len(a["labels"]), "labels,", len(a["ram"]), "ram names,", len(a["blocks"]), "blocks")
