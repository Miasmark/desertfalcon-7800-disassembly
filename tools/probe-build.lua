-- probe-build.lua: what the display-list builder ($FB0D) was given and what it wrote.
-- Runs after tools/harness/input.lua (globals M, cpu, mem, FRAME).
--   BUILD_FROM / BUILD_TO   frame window (default 600..1e9)
-- Output build.log. For each build inside the window:
--   B frame A1 line          at the fetch of $FB0D (A1 = vertical fine scroll $A1, line = raster line)
--   N slot near far z A B sx sy gfx pw base thr     one per list node, in list order (hex)
--   E frame line             at the fetch of the builder's last RTS ($FB0C)
--   Z zone fill bytes...     the zone's list, offsets 0..fill+1 (hex), 12 lines
--   T frame line             a top-of-frame DLI ($9717) that found the builder still running ($18E0 bit 7)
local FROM = tonumber(os.getenv("BUILD_FROM") or "600")
local TO = tonumber(os.getenv("BUILD_TO") or "1000000000")
local out = io.open("build.log", "w")
local PC = cpu.state["PC"]
local scr
for _, s in pairs(M.screens) do scr = s break end
local function line()
  local lines = scr.frame_period / scr.scan_period
  local left = scr:time_until_pos(0, 0) / scr.scan_period
  return math.floor((lines - left) % lines)
end
local function r(a) return mem:read_u8(a) end
local busy = false
local inbuild = false
local PAGES = {0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x26, 0x27, 0x22, 0x23}
BUILD_TAP = mem:install_read_tap(0xFB0C, 0xFB0D, "build", function(a, d)
  if busy or a ~= PC.value then return d end
  if FRAME < FROM or FRAME > TO then return d end
  busy = true
  if a == 0xFB0D then
    inbuild = true
    out:write(string.format("B %d %02X %d\n", FRAME, r(0xA1), line()))
    local y = r(0xCD)
    local guard = 0
    while y < 0x80 and guard < 100 do
      out:write(string.format("N %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X %02X\n", y,
        r(0x1CA4 + y), r(0x26A4 + y), r(0x1EA4 + y), r(0x1F50 + y), r(0x1E50 + y), r(0x25A5 + y), r(0x1FA4 + y),
        r(0x22A4 + y), r(0x2378 + y), r(0x1C50 + y), r(0x1D50 + y)))
      y = r(0x2650 + y)
      guard = guard + 1
    end
  elseif inbuild then
    inbuild = false
    out:write(string.format("E %d %d\n", FRAME, line()))
    for z = 0, 11 do
      local fill = r(0xB5 + 2 * z)
      if z == 11 then
        -- the fix-up loop leaves $CB past the last entry of the bottom zone
        fill = r(0xCB)
      end
      local t = {}
      for i = 0, fill + 1 do t[#t + 1] = string.format("%02X", r(PAGES[z + 1] * 256 + i)) end
      out:write(string.format("Z %d %02X %s\n", z, fill, table.concat(t, " ")))
    end
  end
  busy = false
  return d
end)
BUILD_TAP2 = mem:install_read_tap(0x9747, 0x9747, "topdli", function(a, d)
  if busy or a ~= PC.value then return d end
  if FRAME < FROM or FRAME > TO then return d end
  out:write(string.format("T %d %d\n", FRAME, line()))
  return d
end)
BUILD_STOP = emu.add_machine_stop_notifier(function() out:close() end)
