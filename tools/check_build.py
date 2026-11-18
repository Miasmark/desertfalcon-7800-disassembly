"""Check a model of the display-list builder ($FB0D) against what the game wrote.
python -I tools/check_build.py work/runs/NAME/build.log
Also checks, over the same nodes, the projection formulas and the order rule, and prints
statistics: objects per zone, two-zone objects, lists that hit the cap."""
import sys
from collections import Counter

builds = []
cur = None
tops = 0
for line in open(sys.argv[1]):
    p = line.split()
    if p[0] == "B":
        cur = dict(frame=int(p[1]), a1=int(p[2], 16), line=int(p[3]), nodes=[], zones={}, end=None)
        builds.append(cur)
    elif p[0] == "N" and cur:
        cur["nodes"].append([int(x, 16) for x in p[1:]])
    elif p[0] == "E" and cur:
        cur["end"] = (int(p[1]), int(p[2]))
    elif p[0] == "Z" and cur:
        cur["zones"][int(p[1])] = (int(p[2], 16), [int(x, 16) for x in p[3:]])
    elif p[0] == "T":
        tops += 1
        if cur:
            cur["top"] = (int(p[1]), int(p[2]))


def model(b):
    a1 = b["a1"]
    t95 = (a1 - 0x0E) & 0xFF
    lists = [[] for _ in range(12)]
    fill = [5] * 12
    dropped = 0
    two = 0
    for n in b["nodes"]:
        slot, near, far, z, A, B, sx, sy, gfx, pw, base, thr = n
        if slot >= 0x50:
            continue
        if 0xA0 <= sx < 0xDC:
            continue
        if sy < 0xF1 and sy >= 0xB0:
            continue
        cf = (sy - t95) & 0xFF
        if cf >= 0xF1:
            hi = ((cf & 0x0F) + base) & 0xFF
            if hi < thr:
                continue
            if fill[0] >= 0x4B:
                dropped += 1
                continue
            lists[0] += [gfx, pw, (hi - 0x10) & 0xFF, sx]
            fill[0] += 4
            continue
        zn = cf >> 4
        if zn > 11:
            raise SystemExit("zone %d out of range at frame %d" % (zn, b["frame"]))
        if fill[zn] >= 0x4B:
            dropped += 1
            continue
        hi = ((cf & 0x0F) + base) & 0xFF
        lists[zn] += [gfx, pw, hi, sx]
        fill[zn] += 4
        if hi >= thr:
            two += 1
            if zn + 1 < 12:
                if fill[zn + 1] >= 0x4B:
                    dropped += 1
                else:
                    lists[zn + 1] += [gfx, pw, (hi - 0x10) & 0xFF, sx]
                    fill[zn + 1] += 4
    # bottom zone fix-up
    i = 2
    while i < len(lists[11]):
        lists[11][i] = (lists[11][i] + a1 + 1) & 0xFF
        i += 4
    return lists, fill, dropped, two


ok = bad = 0
perzone = Counter()
maxzone = 0
drops = 0
twos = objs = 0
late = 0
dur = []
viol = 0
proj_bad = Counter()
proj_n = Counter()
for b in builds:
    if not b["zones"]:
        continue
    lists, fill, dropped, two = model(b)
    good = True
    for zn in range(12):
        f, by = b["zones"][zn]
        got = by[5:f]
        if f != fill[zn] or got != lists[zn] or by[f:f + 2] != [0, 0]:
            good = False
        n = (f - 5) // 4
        perzone[n] += 1
        maxzone = max(maxzone, n)
    if good:
        ok += 1
    else:
        bad += 1
        if bad <= 3:
            print("MISMATCH at frame", b["frame"])
            for zn in range(12):
                f, by = b["zones"][zn]
                if by[5:f] != lists[zn]:
                    print("  zone", zn, "game", by[5:f], "model", lists[zn])
    drops += dropped
    twos += two
    objs += sum((f - 5) // 4 for f, _ in b["zones"].values())
    if "top" in b:
        late += 1
    if b["end"]:
        e = b["end"][1] - b["line"]
        if b["end"][0] != b["frame"]:
            e += 263 * (b["end"][0] - b["frame"])
        dur.append(e)
    # order rule: an earlier node must not be wholly nearer than a later one
    ns = b["nodes"]
    for p, s in zip(ns, ns[1:]):
        if p[2] < s[1]:
            viol += 1
    # projection (fliers: slots 0-15; shadows are slot + $47)
    byslot = {n[0]: n for n in ns}
    for n in ns:
        slot, near, far, z, A, B, sx, sy, gfx, pw, base, thr = n
        if slot < 0x10:
            proj_n["sx"] += 1
            if sx != (A + B + 0x7B) & 0xFF:
                proj_bad["sx"] += 1
            proj_n["sy"] += 1
            if sy != (B - A + 0x7E - z) & 0xFF:
                proj_bad["sy"] += 1
            proj_n["far"] += 1
            if far != (A - B + 0x6E) & 0xFF:
                proj_bad["far"] += 1
            sh = byslot.get(slot + 0x47)
            if sh:
                proj_n["shadow_x"] += 1
                if sh[6] != sx:
                    proj_bad["shadow_x"] += 1
                proj_n["shadow_y"] += 1
                if sh[7] != (sy + z) & 0xFF:
                    proj_bad["shadow_y"] += 1
                proj_n["shadow_gfx"] += 1
                if sh[8] != gfx:
                    proj_bad["shadow_gfx"] += 1
print("builds %d: model matches %d, differs %d" % (ok + bad, ok, bad))
print("entries per zone list (count of lists):", dict(sorted(perzone.items())))
print("most entries in one zone:", maxzone, " objects dropped by the cap (model):", drops)
print("entries written %d, of which second halves of two-zone objects %d" % (objs, twos))
print("builds still running at the top-of-frame DLI:", late, "of", len(builds), "(T lines %d)" % tops)
if dur:
    print("build length in raster lines: mean %.1f min %d max %d" % (sum(dur) / len(dur), min(dur), max(dur)))
    st = Counter(b["line"] for b in builds)
    print("build start line:", dict(sorted(st.items())))
print("order rule broken between adjacent nodes: %d" % viol)
for k in proj_n:
    print("  %-10s checked %6d  differs %6d" % (k, proj_n[k], proj_bad[k]))
