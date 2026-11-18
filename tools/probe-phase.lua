-- probe-phase.lua: executed 6502 cycles per phase of Desert Falcon's 30 Hz tick.
-- The cycle counting is the toolkit's probes/cyclebudget.lua (opcode base counts, taken
-- branches, page crossings on indexed reads, 7 per NMI entry); what is added is that each
-- instruction's cycles go to the "phase" set by the last checkpoint the PC passed.
-- Runs after tools/harness/input.lua (globals M, cpu, mem, FRAME).
--   PHASE_FROM / PHASE_TO  frame window (default 700..1e9)
-- Output phase.log: one line per tick (from one fetch of $9B87 to the next):
--   frame nodes  name=cycles ...
-- and phase_summary.txt: per phase, mean and max cycles a tick.
local FROM = tonumber(os.getenv("PHASE_FROM") or "700")
local TO = tonumber(os.getenv("PHASE_TO") or "1000000000")
local PCs, SPs, Xs, Ys = cpu.state["PC"], cpu.state["SP"], cpu.state["X"], cpu.state["Y"]
local CYC = {7,6,0,8,3,3,5,5,3,2,2,2,4,4,6,6,2,5,0,8,4,4,6,6,2,4,2,7,4,4,7,7,6,6,0,8,3,3,5,5,4,2,2,2,4,4,6,6,2,5,0,8,4,4,6,6,2,4,2,7,4,4,7,7,6,6,0,8,3,3,5,5,3,2,2,2,3,4,6,6,2,5,0,8,4,4,6,6,2,4,2,7,4,4,7,7,6,6,0,8,3,3,5,5,4,2,2,2,5,4,6,6,2,5,0,8,4,4,6,6,2,4,2,7,4,4,7,7,2,6,2,6,3,3,3,3,2,2,2,2,4,4,4,4,2,6,0,6,4,4,4,4,2,5,2,5,5,5,5,5,2,6,2,6,3,3,3,3,2,2,2,2,4,4,4,4,2,5,0,5,4,4,4,4,2,4,2,4,4,4,4,4,2,6,2,8,3,3,5,5,2,2,2,2,4,4,6,6,2,5,0,8,4,4,6,6,2,4,2,7,4,4,7,7,2,6,2,8,3,3,5,5,2,2,2,2,4,4,6,6,2,5,0,8,4,4,6,6,2,4,2,7,4,4,7,7}
local REL = {[0x10]=1,[0x30]=1,[0x50]=1,[0x70]=1,[0x90]=1,[0xB0]=1,[0xD0]=1,[0xF0]=1}
-- opcodes whose indexed read costs one more on a page crossing: mode per opcode
local PENM = {[0x11]="izy",[0x31]="izy",[0x51]="izy",[0x71]="izy",[0xB1]="izy",[0xD1]="izy",[0xF1]="izy",
  [0x19]="aby",[0x39]="aby",[0x59]="aby",[0x79]="aby",[0xB9]="aby",[0xD9]="aby",[0xF9]="aby",[0xBE]="aby",
  [0x1D]="abx",[0x3D]="abx",[0x5D]="abx",[0x7D]="abx",[0xBD]="abx",[0xDD]="abx",[0xFD]="abx",[0xBC]="abx"}
local MAINCP = {[0x9B61]="idle",[0x9B87]="scrollobj_9DA3",[0x9B8E]="m_60CC",[0x9B91]="m_61C9",[0x9B94]="m_E000",
  [0x9B97]="m_F128",[0x9B9A]="m_F6BA",[0x9B9D]="m_FBD3",[0x9BA0]="m_B03A",[0x9BA3]="m_B2B3",[0x9BA6]="m_B7AA",
  [0x9BA9]="m_B44C",[0x9BAC]="m_B8FF",[0x9BAF]="m_6312",[0x9BB2]="m_FA2A",[0x9BB5]="m_F9D5",[0x9BB8]="m_50BA",
  [0x9BBB]="m_5410",[0x9BBE]="idle"}
local NMICP = {[0x9885]="n_mapscroll_D119",[0x9888]="n_build_FB0D",[0x988B]="n_other",[0x988F]="n_sound_56B4",
  [0x9892]="n_sound_579D",[0x9895]="n_sound_5840",[0x9898]="n_other"}
local function r(a) return mem:read_u8(a & 0xFFFF) end
local phase, saved = "idle", "idle"
local acc, tot, mx, ticks = {}, {}, {}, 0
local lastpc, lastop = -1, 0
local in_nmi, nmi_sp = false, 0
local reading = false
local out = io.open("phase.log", "w")
local function endtick()
  local parts = {}
  local names = {}
  for k in pairs(acc) do names[#names + 1] = k end
  table.sort(names)
  for _, k in ipairs(names) do
    parts[#parts + 1] = string.format("%s=%d", k, acc[k])
    tot[k] = (tot[k] or 0) + acc[k]
    if acc[k] > (mx[k] or 0) then mx[k] = acc[k] end
  end
  -- objects on the list
  local n, y, g = 0, r(0xCD), 0
  while y < 0x80 and g < 100 do
    if y < 0x50 then n = n + 1 end
    y = r(0x2650 + y); g = g + 1
  end
  out:write(string.format("%d %d %s\n", FRAME, n, table.concat(parts, " ")))
  acc = {}
  ticks = ticks + 1
end
PHASE_TAP = mem:install_read_tap(0x0000, 0xFFFF, "phase-fetch", function(a, d)
  if reading or a ~= PCs.value then return d end
  if FRAME < FROM or FRAME > TO then lastpc = -1 return d end
  local cost = 0
  if lastpc >= 0 and REL[lastop] and a ~= ((lastpc + 2) & 0xFFFF) then
    cost = cost + 1
    if (a & 0xFF00) ~= ((lastpc + 2) & 0xFF00) then cost = cost + 1 end
  end
  if a == 0x0040 and not in_nmi and lastpc >= 0 and a ~= lastpc then
    in_nmi, nmi_sp = true, SPs.value & 0xFF
    saved = phase
    phase = "n_other"
    cost = cost + 7
  end
  if in_nmi then
    local p = NMICP[a]
    if p then phase = p end
  else
    local p = MAINCP[a]
    if p then
      if a == 0x9B87 then endtick() end
      phase = p
    end
  end
  cost = cost + CYC[d + 1]
  local m = PENM[d]
  if m then
    reading = true
    local base, idx = 0, 0
    if m == "abx" or m == "aby" then
      base = r(a + 1) | (r(a + 2) << 8)
      idx = (m == "abx") and Xs.value or Ys.value
    else
      local z = r(a + 1)
      base = r(z) | (r((z + 1) & 0xFF) << 8)
      idx = Ys.value
    end
    reading = false
    if ((base + idx) & 0xFF00) ~= (base & 0xFF00) then cost = cost + 1 end
  end
  acc[phase] = (acc[phase] or 0) + cost
  if in_nmi and d == 0x40 and (SPs.value & 0xFF) == nmi_sp then
    in_nmi = false
    phase = saved
  end
  lastpc, lastop = a, d
  return d
end)
PHASE_STOP = emu.add_machine_stop_notifier(function()
  out:close()
  local o = io.open("phase_summary.txt", "w")
  local names = {}
  for k in pairs(tot) do names[#names + 1] = k end
  table.sort(names)
  o:write(string.format("ticks %d\n", ticks))
  local sum = 0
  for _, k in ipairs(names) do
    o:write(string.format("%-20s mean %8.1f  max %7d\n", k, tot[k] / ticks, mx[k]))
    sum = sum + tot[k] / ticks
  end
  o:write(string.format("%-20s mean %8.1f\n", "all", sum))
  o:close()
end)
