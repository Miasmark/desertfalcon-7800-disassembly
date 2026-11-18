-- probe-list.lua: the depth-sorted object list, checked every frame.
-- Runs after tools/harness/input.lua (globals M, cpu, mem, FRAME).
--   LIST_FROM / LIST_TO  frame window (default 1..1e9)
--   LIST_DUMP            frames ("a,b,c") at which the whole list is written to list_f<frame>.txt
--   CB=1                 also load the toolkit's cyclebudget.lua (its A7800_CB_* settings apply)
-- Output list.log, one line per frame:
--   frame A2 d nodes drawn maxfill relinks viol
--     A2     the game's frame counter ($A2);  d  this tick's scroll step ($D1)
--     nodes  objects on the list (sentinels $50-$53 not counted)
--     drawn  objects the builder at $FB35 would accept (on-screen x and y tests)
--     maxfill the largest zone fill pointer low byte ($B5+2z), 5 = empty, $4D = full (18 objects)
--     relinks writes to the next-link array $2650-$26A3 and the head $CD in this frame
--     viol   adjacent pairs on the list that break the order rule (earlier node wholly nearer)
-- and relinkpc.log: writes to the links by PC, totalled.
local FROM = tonumber(os.getenv("LIST_FROM") or "1")
local TO = tonumber(os.getenv("LIST_TO") or "1000000000")
local dumps = {}
for w in string.gmatch(os.getenv("LIST_DUMP") or "", "%d+") do dumps[tonumber(w)] = true end
local out = io.open("list.log", "w")
out:write("frame A2 d nodes drawn maxfill relinks viol\n")
local relinks = 0
local bypc = {}
local PC = cpu.state["PC"]
LIST_TAP = mem:install_write_tap(0x2650, 0x26A3, "links", function(a, d)
  relinks = relinks + 1
  local pc = PC.value
  bypc[pc] = (bypc[pc] or 0) + 1
  return d
end)
LIST_TAP2 = mem:install_write_tap(0x00CD, 0x00CD, "head", function(a, d)
  relinks = relinks + 1
  local pc = PC.value
  bypc[pc] = (bypc[pc] or 0) + 1
  return d
end)
local function r(a) return mem:read_u8(a) end
local function walk()
  local t = {}
  local y = r(0xCD)
  local guard = 0
  while y < 0x80 and guard < 100 do
    t[#t + 1] = y
    y = r(0x2650 + y)
    guard = guard + 1
  end
  return t
end
LIST_F = emu.register_frame_done(function()
  local f = FRAME
  if f < FROM or f > TO then relinks = 0 return end
  local t = walk()
  local nodes, drawn, viol = 0, 0, 0
  for i, s in ipairs(t) do
    if s < 0x50 then
      nodes = nodes + 1
      local x, y = r(0x25A5 + s), r(0x1FA4 + s)
      local xok = not (x >= 0xA0 and x < 0xDC)
      local yok = (y >= 0xF1) or (y < 0xB0)
      if xok and yok then drawn = drawn + 1 end
    end
    if i > 1 then
      local p = t[i - 1]
      -- earlier node p must not be wholly nearer than s: p.far < s.near is a violation
      if r(0x26A4 + p) < r(0x1CA4 + s) then viol = viol + 1 end
    end
  end
  local maxfill = 0
  for z = 0, 11 do
    local v = r(0xB5 + 2 * z)
    if v > maxfill then maxfill = v end
  end
  out:write(string.format("%d %02X %d %d %d %02X %d %d\n", f, r(0xA2), r(0xD1), nodes, drawn, maxfill, relinks, viol))
  relinks = 0
  if dumps[f] then
    local o = io.open(string.format("list_f%05d.txt", f), "w")
    o:write("slot near far z  A  B  sx sy gfx pw base thr act\n")
    for _, s in ipairs(t) do
      o:write(string.format("%02X   %02X   %02X  %02X %02X %02X %02X %02X %02X  %02X %02X   %02X  %02X\n", s,
        r(0x1CA4 + s), r(0x26A4 + s), r(0x1EA4 + s), r(0x1F50 + s), r(0x1E50 + s), r(0x25A5 + s), r(0x1FA4 + s),
        r(0x22A4 + s), r(0x2378 + s), r(0x1C50 + s), r(0x1D50 + s), s < 0x3F and r(0x1950 + s) or 0))
    end
    o:close()
  end
end)
LIST_STOP = emu.add_machine_stop_notifier(function()
  out:close()
  local o = io.open("relinkpc.log", "w")
  local keys = {}
  for k in pairs(bypc) do keys[#keys + 1] = k end
  table.sort(keys)
  for _, k in ipairs(keys) do o:write(string.format("%04X %d\n", k, bypc[k])) end
  o:close()
end)
if os.getenv("CB") == "1" then
  dofile(os.getenv("CBLUA"))
end
