# Event System

`web/dashboard/event_bus.js` la event bus noi bo, dung de noi cac bridge ma
khong tao coupling truc tiep giua Viewer, Charts va Reports.

`web/dashboard/sync.js` chuyen event tu Workspace thanh ten on dinh:

- `workspace:frame-changed`
- `workspace:playback-started`
- `workspace:playback-paused`
- `workspace:playback-stopped`
- `workspace:playback-finished`

Selection duoc phat qua `selection:node` va `selection:keyframe`. Bus chi
truyen event; no khong luu ban sao rollout hay pose.
