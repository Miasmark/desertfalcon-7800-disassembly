-- probe-regs.lua: every write to MARIA's registers ($20-$3F) in a window of frames,
-- with the raster line and the PC. Runs after tools/harness/input.lua.
--   REGS_FROM / REGS_TO  frame window (default 1500..1503)
-- Output regs.log: frame line addr value pc
local FROM = tonumber(os.getenv("REGS_FROM") or "1500")
local TO = tonumber(os.getenv("REGS_TO") or "1503")
local out = io.open("regs.log", "w")
local PC = cpu.state["PC"]
local scr
for _, s in pairs(M.screens) do scr = s break end
local function line()
  local lines = scr.frame_period / scr.scan_period
  local left = scr:time_until_pos(0, 0) / scr.scan_period
  return (lines - left) % lines
end
REGS_TAP = mem:install_write_tap(0x20, 0x3F, "regs", function(a, d)
  if FRAME >= FROM and FRAME <= TO then
    out:write(string.format("%d %.2f %02X %02X %04X\n", FRAME, line(), a, d, PC.value))
  end
  return d
end)
REGS_STOP = emu.add_machine_stop_notifier(function() out:close() end)
