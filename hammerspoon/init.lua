-- Command-click opens links in HerdR inside Ghostty.
--
-- HerdR captures the mouse, so Ghostty forwards clicks to it instead of
-- opening links itself. Terminal mouse reports cannot carry Command, so HerdR
-- opens links on Control-click. While Ghostty is frontmost, this rewrites
-- Command to Control on clicks and pointer moves over its focused window:
-- Command-click opens a link and Command-hover underlines it. Keyboard
-- shortcuts and other apps are untouched.

hs.autoLaunch(true)
hs.dockIcon(false)

local GHOSTTY = "com.mitchellh.ghostty"
local types = hs.eventtap.event.types

local function ghosttyFrame()
  local app = hs.application.frontmostApplication()
  if not app or app:bundleID() ~= GHOSTTY then return nil end
  local win = app:focusedWindow()
  return win and win:frame()
end

-- Pointer moves arrive many times a second, so reuse the window lookup briefly.
local cached = { at = 0, frame = nil }
local function ghosttyFrameCached()
  local now = hs.timer.absoluteTime()
  if now - cached.at > 300e6 then
    cached.at, cached.frame = now, ghosttyFrame()
  end
  return cached.frame
end

local function over(frame, e)
  local p = e:location()
  return frame ~= nil and hs.geometry.point(p.x, p.y):inside(frame)
end

local function toControl(e)
  local flags = e:getFlags()
  flags.cmd = nil
  flags.ctrl = true
  e:setFlags(flags)
end

local clicking = false -- a rewritten click is in progress

-- Globals so the tap and its watchdog are not garbage-collected.
herdrLinkClick = hs.eventtap.new(
  { types.leftMouseDown, types.leftMouseDragged, types.leftMouseUp, types.mouseMoved },
  function(e)
    -- Leave Shift-Command alone: Ghostty uses it to open links itself.
    local flags = e:getFlags()
    local kind, cmd = e:getType(), flags.cmd and not flags.shift
    if kind == types.leftMouseDown then
      clicking = cmd and over(ghosttyFrame(), e) or false
      if clicking then toControl(e) end
    elseif kind == types.mouseMoved then
      if cmd and over(ghosttyFrameCached(), e) then toControl(e) end
    elseif clicking then
      if cmd then toControl(e) end
      if kind == types.leftMouseUp then clicking = false end
    end
    return false
  end
)
herdrLinkClick:start()

-- macOS disables an event tap that ever responds too slowly; turn it back on.
herdrLinkClickWatchdog = hs.timer.doEvery(5, function()
  if not herdrLinkClick:isEnabled() then herdrLinkClick:start() end
end)
