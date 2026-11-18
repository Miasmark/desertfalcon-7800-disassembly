"""Per slot, the constants in  sx = A + B + k1,  sy = B - A - z + k2,  far = A - B + k3,  near = far - k4,
from the nodes probe-build.lua logged. python -I tools/fit_proj.py work/runs/NAME/build.log [maxslot]"""
import sys
from collections import Counter, defaultdict

mx = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x4F
k = defaultdict(lambda: [Counter(), Counter(), Counter(), Counter(), 0, Counter()])
for line in open(sys.argv[1]):
    p = line.split()
    if p[0] != "N":
        continue
    slot, near, far, z, A, B, sx, sy, gfx, pw, base, thr = [int(x, 16) for x in p[1:]]
    if slot > mx:
        continue
    if 0xB0 <= sy < 0xF1:
        continue
    e = k[slot]
    e[0][(sx - A - B) & 0xFF] += 1
    e[1][(sy - B + A + z) & 0xFF] += 1
    e[2][(far - A + B) & 0xFF] += 1
    e[3][(far - near) & 0xFF] += 1
    e[4] += 1
    e[5][(gfx, pw, base, thr)] += 1


def top(c):
    return " ".join("%02X:%d" % (v, n) for v, n in c.most_common(3))


print("slot  n      sx-(A+B)             sy-(B-A-z)           far-(A-B)            far-near        art(gfx,pw,base,thr)")
for slot in sorted(k):
    e = k[slot]
    art = " ".join("%02X/%02X/%02X/%02X:%d" % (a + (n,)) for a, n in e[5].most_common(2))
    print("%02X  %5d   %-20s %-20s %-20s %-15s %s" % (slot, e[4], top(e[0]), top(e[1]), top(e[2]), top(e[3]), art))
