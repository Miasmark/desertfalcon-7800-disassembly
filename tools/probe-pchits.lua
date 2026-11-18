-- probe-pchits.lua: how often chosen instructions are fetched, in a frame window.
-- Runs after tools/harness/input.lua.
--   HITS       hex addresses, comma separated
--   HITS_FROM / HITS_TO   frame window (default 700..1e9)
-- Output pchits.txt: address count, and the number of frames counted.
local FROM = tonumber(os.getenv("HITS_FROM") or "700")
local TO = tonumber(os.getenv("HITS_TO") or "1000000000")
local PC = cpu.state["PC"]
local n = {}
local lo, hi = 0xFFFF, 0
for a in string.gmatch(os.getenv("HITS") or "", "%x+") do
  local v = tonumber(a, 16)
  n[v] = 0
  if v < lo then lo = v end
  if v > hi then hi = v end
end
local frames = 0
HITS_TAP = mem:install_read_tap(lo, hi, "pchits", function(a, d)
  if n[a] and a == PC.value and FRAME >= FROM and FRAME <= TO then n[a] = n[a] + 1 end
  return d
end)
HITS_F = emu.register_frame_done(function()
  if FRAME >= FROM and FRAME <= TO then frames = frames + 1 end
end)
HITS_STOP = emu.add_machine_stop_notifier(function()
  local o = io.open("pchits.txt", "w")
  o:write(string.format("frames %d\n", frames))
  local keys = {}
  for k in pairs(n) do keys[#keys + 1] = k end
  table.sort(keys)
  for _, k in ipairs(keys) do o:write(string.format("%04X %d\n", k, n[k])) end
  o:close()
end)
