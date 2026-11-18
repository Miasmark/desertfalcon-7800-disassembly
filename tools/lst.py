"""Print a slice of the generated listing compactly: python -I tools/lst.py 9964 9C0C [listing]
Lines look like 'ADDR  [label:] INSTR operand'. Data lines are kept; xref lines dropped."""
import re
import sys

lo, hi = int(sys.argv[1], 16), int(sys.argv[2], 16)
path = sys.argv[3] if len(sys.argv) > 3 else "work/src/rom.asm"
pend = []
on = False
for line in open(path, encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    m = re.search(r";\s*([0-9A-F]{4})[: ]", line)
    if line.startswith("; xrefs"):
        if "-x" in sys.argv:
            pend.append(line)
        continue
    if not m:
        pend.append(line)
        continue
    a = int(m.group(1), 16)
    on = lo <= a <= hi
    if on:
        for p in pend:
            if p.strip():
                print("      " + p.strip())
        code = line.split(";")[0].strip()
        code = re.sub(r"\s+", " ", code)
        cm = line.split(";", 1)[1]
        cyc = cm.rsplit(None, 1)[-1] if re.search(r"\s\d\+?$", cm) else ""
        extra = ""
        m2 = re.search(r";\s*[0-9A-F]{4}:\s*(?:[0-9A-F]{2} ?)+\s*\d?\+?\s*(.*)$", line)
        print("%04X  %-40s %s" % (a, code, cyc))
    pend = []
    if a > hi:
        break
