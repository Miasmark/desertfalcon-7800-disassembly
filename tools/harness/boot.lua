-- boot.lua: the autoboot script. Loads the input script, then the probe named in PROBE.
dofile(os.getenv("INPUTLUA"))
local p = os.getenv("PROBE")
if p and p ~= "" then dofile(p) end
