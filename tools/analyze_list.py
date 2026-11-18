"""Summarise a probe-list.lua run: python -I tools/analyze_list.py work/runs/NAME [from] [to]
Joins list.log with cyclebudget.log (block 1), sums each pair of frames (the game ticks at 30 Hz)
and prints means, maxima and the correlation of the builder's and the sort's cycles with counts."""
import os
import sys

rd = sys.argv[1]
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 700
hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 9
lst = {}
for line in open(os.path.join(rd, "list.log")):
    p = line.split()
    if p[0] == "frame":
        continue
    lst[int(p[0])] = dict(a2=int(p[1], 16), d=int(p[2]), nodes=int(p[3]), drawn=int(p[4]),
                          maxfill=int(p[5], 16), relinks=int(p[6]), viol=int(p[7]))
cb = {}
for line in open(os.path.join(rd, "cyclebudget.log")):
    p = line.split()
    if not p or not p[0].startswith("f"):
        continue
    d = {}
    for k, v in zip(p[1::2], p[2::2]):
        d[k] = float(v)
    cb[int(p[0][1:])] = d
frames = sorted(f for f in lst if f in cb and lo <= f <= hi)
keys = [k for k in cb[frames[0]]]
# pair frames by tick: a tick is two frames; pair (even A2, odd A2) is not needed, just sum pairs
ticks = []
for i in range(0, len(frames) - 1, 2):
    a, b = frames[i], frames[i + 1]
    t = {k: cb[a][k] + cb[b][k] for k in keys}
    t["nodes"] = lst[b]["nodes"]
    t["drawn"] = lst[b]["drawn"]
    t["relinks"] = lst[a]["relinks"] + lst[b]["relinks"]
    t["viol"] = max(lst[a]["viol"], lst[b]["viol"])
    t["d"] = max(lst[a]["d"], lst[b]["d"])
    t["maxfill"] = max(lst[a]["maxfill"], lst[b]["maxfill"])
    t["frame"] = a
    ticks.append(t)
print("frames %d..%d, %d ticks (2 frames each)" % (frames[0], frames[-1], len(ticks)))
for k in keys + ["nodes", "drawn", "relinks", "viol", "d", "maxfill"]:
    v = [t[k] for t in ticks]
    print("  %-10s mean %9.1f  min %7.0f  max %7.0f" % (k, sum(v) / len(v), min(v), max(v)))


def fit(xk, yk):
    xs = [t[xk] for t in ticks]
    ys = [t[yk] for t in ticks]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        return
    b = sxy / sxx
    a = my - b * mx
    syy = sum((y - my) ** 2 for y in ys)
    r = sxy / (sxx * syy) ** 0.5 if syy else 0
    print("  %s = %.1f + %.1f * %s   (r=%.3f)" % (yk, a, b, xk, r))


print("fits per tick:")
fit("drawn", "build")
fit("nodes", "build")
fit("relinks", "sort")
fit("nodes", "scrollobj")
fit("nodes", "sort")
worst = sorted(ticks, key=lambda t: -t["build"])[:5]
for t in worst:
    print("  busiest build: frame %d build %d nodes %d drawn %d maxfill %02X" % (
        t["frame"], t["build"], t["nodes"], t["drawn"], t["maxfill"]))
v = [t for t in ticks if t["viol"]]
print("ticks with an order violation: %d of %d" % (len(v), len(ticks)))
for t in v[:10]:
    print("   frame %d viol %d" % (t["frame"], t["viol"]))
