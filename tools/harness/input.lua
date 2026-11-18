-- input.lua: scripted input, snapshots and RAM dumps for a windowless MAME run.
-- (After a homebrew project's build/harness/harness/flight.lua.)
--   SCRIPT  "frames:stick:button;..."  stick is a letter set of l r u d (or -),
--           buttons: 0 none, 1 button 1, 2 button 2, 3 both; + 4 Pause, + 8 Select, + 16 Reset.
--   SNAPS   frames to snapshot, "a,b,c" (MAME's -snapshot_directory)
--   DUMPS   frames at whose end RAM $0000-$27FF is written to dump_f<frame>.bin
--   END     the frame to exit on (default: after the script)
--   PEEK    hex addresses, comma separated: peek.txt gets "frame v v v" (hex) every frame
--   POKES   "frame:addr=val,addr=val;frame:..." (hex addr/val) written at that frame's end;
--           "frame-frame:addr=val" holds the value over a range of frames.
-- Port tags are upper-case on MAME 0.289 and its Atari fork, lower on 0.287.
M = manager.machine
local P = M.ioport.ports
cpu = M.devices[":maincpu"]
mem = cpu.spaces["program"]
local function fld(n)
  for _, t in ipairs({":JOYSTICKS", ":BUTTONS", ":joysticks", ":buttons"}) do
    local f = P[t] and P[t].fields[n]
    if f then return f end
  end
end
local stick = {l = fld("P1 Left"), r = fld("P1 Right"), u = fld("P1 Up"), d = fld("P1 Down")}
local fire = fld("P1 Button 1")
local fire2 = fld("P1 Button 2")
local pause, select, reset
for _, t in ipairs({":CONSOLE", ":console", ":console_buttons"}) do
  if P[t] and P[t].fields["Pause"] then pause = P[t].fields["Pause"] end
  if P[t] and P[t].fields["Select"] then select = P[t].fields["Select"] end
  if P[t] and P[t].fields["Reset"] then reset = P[t].fields["Reset"] end
end
local steps = {}
for n, s, b in string.gmatch(os.getenv("SCRIPT") or "600:-:0", "(%d+):([lrud%-]+):(%d+)") do
  steps[#steps + 1] = {tonumber(n), s, tonumber(b)}
end
local total = 0
for _, s in ipairs(steps) do total = total + s[1] end
local snaps, dumps = {}, {}
for w in string.gmatch(os.getenv("SNAPS") or "", "%d+") do snaps[tonumber(w)] = true end
for w in string.gmatch(os.getenv("DUMPS") or "", "%d+") do dumps[tonumber(w)] = true end
local END = tonumber(os.getenv("END") or tostring(total))
local peek = {}
for a in string.gmatch(os.getenv("PEEK") or "", "[^,]+") do peek[#peek + 1] = tonumber(a, 16) end
local pout = (#peek > 0) and io.open("peek.txt", "w")
local pokes = {}
for spec in string.gmatch(os.getenv("POKES") or "", "[^;]+") do
  local a, b, list = string.match(spec, "^(%d+)%-(%d+):(.+)$")
  if not a then a, list = string.match(spec, "^(%d+):(.+)$"); b = a end
  if a then
    local t = {}
    for ad, val in string.gmatch(list, "(%x+)=(%x+)") do t[#t + 1] = {tonumber(ad, 16), tonumber(val, 16)} end
    pokes[#pokes + 1] = {tonumber(a), tonumber(b), t}
  end
end
FRAME = 0
INPUT_F = emu.register_frame_done(function()
  FRAME = FRAME + 1
  local f = FRAME
  local t, cur = f, nil
  for _, s in ipairs(steps) do
    if t <= s[1] then cur = s break end
    t = t - s[1]
  end
  for k, fl in pairs(stick) do fl:set_value((cur and cur[2]:find(k)) and 1 or 0) end
  fire:set_value((cur and cur[3] % 2 == 1) and 1 or 0)
  if fire2 then fire2:set_value((cur and math.floor(cur[3] / 2) % 2 == 1) and 1 or 0) end
  if pause then pause:set_value((cur and cur[3] % 8 >= 4) and 1 or 0) end
  if select then select:set_value((cur and cur[3] % 16 >= 8) and 1 or 0) end
  if reset then reset:set_value((cur and cur[3] >= 16) and 1 or 0) end
  if snaps[f] then M.video:snapshot() end
  if dumps[f] then
    local o = io.open(string.format("dump_f%05d.bin", f), "wb")
    local parts = {}
    for a = 0, 0x27FF do parts[#parts + 1] = string.char(mem:read_u8(a)) end
    o:write(table.concat(parts)); o:close()
  end
  if pout then
    local v = {}
    for _, a in ipairs(peek) do v[#v + 1] = string.format("%02X", mem:read_u8(a)) end
    pout:write(string.format("%d %s\n", f, table.concat(v, " ")))
  end
  for _, p in ipairs(pokes) do
    if f >= p[1] and f <= p[2] then
      for _, w in ipairs(p[3]) do mem:write_u8(w[1], w[2]) end
    end
  end
  if f >= END then
    if pout then pout:close() end
    M:exit()
  end
end)
