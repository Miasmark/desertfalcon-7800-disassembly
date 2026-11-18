"""Run Desert Falcon windowless on the fork's MAME with a scripted input and a probe.

usage: python -I tools/run.py NAME [--script S] [--snaps a,b] [--dumps a,b] [--end N]
                               [--peek hexlist] [--pokes P] [--probe tools/x.lua] [-e K=V ...]

Each run gets its own folder work/runs/NAME (cfg, nv, snap, ui.ini with skip_warnings 1),
so several MAMEs can run at once. Never opens a window: -video none -sound none -nothrottle.
The probe (optional) is dofile'd after tools/harness/input.lua, which defines the globals
M, cpu, mem and FRAME. Output files land in the run folder.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAME = os.environ.get("A7800_MAME", "a78.exe")
CART = os.path.join(ROOT, "work", "df.a78")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--script", default="600:-:0")
    ap.add_argument("--snaps", default="")
    ap.add_argument("--dumps", default="")
    ap.add_argument("--end", default="")
    ap.add_argument("--peek", default="")
    ap.add_argument("--pokes", default="")
    ap.add_argument("--probe", default="")
    ap.add_argument("--cart", default=CART)
    ap.add_argument("-e", action="append", default=[])
    a = ap.parse_args()
    rd = os.path.join(ROOT, "work", "runs", a.name)
    shutil.rmtree(rd, ignore_errors=True)
    os.makedirs(os.path.join(rd, "cfg"))
    shutil.copy(os.path.join(HERE, "harness", "ui.ini"), rd)
    shutil.copy(a.cart, os.path.join(rd, "cart.a78"))
    env = dict(os.environ, SCRIPT=a.script, SNAPS=a.snaps, DUMPS=a.dumps, PEEK=a.peek, POKES=a.pokes,
               INPUTLUA=os.path.join(HERE, "harness", "input.lua"))
    if a.end:
        env["END"] = a.end
    if a.probe:
        env["PROBE"] = os.path.abspath(a.probe)
    for kv in a.e:
        k, v = kv.split("=", 1)
        env[k] = v
    cmd = [MAME, "a7800", "-cart", "cart.a78", "-bios", "skip", "-skip_gameinfo", "-video", "none",
           "-sound", "none", "-nothrottle", "-inipath", ".", "-cfg_directory", "cfg", "-nvram_directory", "nv",
           "-snapshot_directory", "snap", "-autoboot_script", os.path.join(HERE, "harness", "boot.lua")]
    with open(os.path.join(rd, "mame.out"), "w") as o:
        r = subprocess.run(cmd, cwd=rd, env=env, stdout=o, stderr=subprocess.STDOUT, timeout=3000)
    snaps = sorted(int(s) for s in a.snaps.split(",") if s)
    files = sorted(glob.glob(os.path.join(rd, "snap", "a7800", "*.png")))
    for f, fr in zip(files, snaps):
        os.replace(f, os.path.join(rd, "snap", "f%05d.png" % fr))
    out = open(os.path.join(rd, "mame.out")).read()
    print("run %s: exit %d, %d/%d snaps" % (a.name, r.returncode, len(files), len(snaps)))
    if out.strip():
        print(out[-3000:])


if __name__ == "__main__":
    main()
