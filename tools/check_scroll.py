"""Check the diagonal scroll model against a peek.txt from tools/run.py.
The run must be made with --peek set to PEEK below (python -I tools/check_scroll.py --peek prints it).
python -I tools/check_scroll.py work/runs/NAME/peek.txt [from]

Model (read from $D12F-$D34C):
  A1 = vertical fine scroll, -1..14.  Top playfield zone is A1+1 lines, bottom one 15-A1 lines,
       the bottom zone's CHARBASE ($EF) is $81+A1.
  Each scroll pixel: every zone header's x goes down one; for zones 6-11, every 8th pixel x returns
       to 0 and the header's low byte goes up one (A5 = -1..6 is that phase).
  Each 16th pixel: the twelve headers move down one zone and zone 0 gets a new row at x=$5A.
"""
import sys

PAGES = [0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x26, 0x27, 0x22, 0x23]
ADDRS = [0xA1, 0xA5, 0xD1, 0xEF, 0x2756, 0x2777, 0xED, 0xA6, 0x77, 0x19D1, 0x19D2, 0x19D3, 0x19D4, 0xEB]
for p in PAGES:
    ADDRS += [p * 256 + 0, p * 256 + 2, p * 256 + 4]
PEEK = ",".join("%X" % a for a in ADDRS)
if sys.argv[1] == "--peek":
    print(PEEK)
    raise SystemExit
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 700
rows = []
for line in open(sys.argv[1]):
    p = line.split()
    f = int(p[0])
    if f < lo:
        continue
    v = [int(x, 16) for x in p[1:]]
    d = dict(zip(ADDRS, v))
    d["f"] = f
    rows.append(d)
n = bad_top = bad_bot = bad_cb = bad_x = 0
steps = coarse = 0
bad_step = 0
prev = None
ROWS = [0x2400, 0x2421, 0x2442, 0x2463, 0x2484, 0x24A5, 0x24C6, 0x2500, 0x2521, 0x2542, 0x2563, 0x2584]
bad_rowbase = 0
for d in rows:
    a1 = d[0xA1]
    n += 1
    if a1 != 0xFF:
        if (d[0x2756] & 0x1F) != a1:
            bad_top += 1
        if (d[0x2777] & 0x1F) != 14 - a1:
            bad_bot += 1
        if a1 < 14 and d[0xEF] != 0x81 + a1:
            bad_cb += 1
    xs = [d[p * 256 + 4] for p in PAGES]
    ptr = [d[p * 256 + 2] * 256 + d[p * 256] for p in PAGES]
    want = (-(d[0xA5] + 1)) & 0xFF
    if any(x != want for x in xs[6:]):
        bad_x += 1
    # each zone's row pointer minus the characters already scrolled off must be a ring row
    if prev is not None:
        pxs = [prev[p * 256 + 4] for p in PAGES]
        pptr = [prev[p * 256 + 2] * 256 + prev[p * 256] for p in PAGES]
        if (xs, ptr) != (pxs, pptr):
            # how many pixels moved: compare zone 6-11 phase and A1
            da1 = (a1 - prev[0xA1]) & 0x1F
            steps += 1
            if ptr[1:] == pptr[:-1] and ptr[0] != pptr[0]:
                coarse += 1
                if ptr[0] not in ROWS or (xs[0] > 0x5A or xs[0] < 0x4A):
                    bad_rowbase += 1
    prev = d
print("frames checked %d" % n)
print("top zone height != A1+1: %d   bottom zone height != 15-A1: %d   CHARBASE shadow != $81+A1: %d" % (
    bad_top, bad_bot, bad_cb))
print("zones 6-11 x != -(A5+1): %d" % bad_x)
print("frames where the headers changed: %d, of which a rotation by one zone: %d (new row not a ring row: %d)" % (
    steps, coarse, bad_rowbase))
sp = [d[0xA6] for d in rows]
print("scroll speed $A6: min %d max %d mean %.2f" % (min(sp), max(sp), sum(sp) / len(sp)))
pr = [d[0x77] for d in rows]
print("pressure $77: first %02X last %02X max %02X" % (pr[0], pr[-1], max(pr)))
seen = []
last = None
for d in rows:
    k = (d[0x77], d[0x19D1] >> 4)
    if k != last:
        seen.append((d["f"],) + k)
        last = k
print("pressure / wave type over time (frame, $77, type):", " ".join("%d:%02X:%X" % s for s in seen[:60]))
