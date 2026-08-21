# Architecture

The Web Platform follows a component-based architecture:
- `app.js`: Main entry point binding modules together.
- `viewer.js`: Manages the visual viewport interface.
- `timeline.js`: Interfaces with playback temporal streams.
- `camera.js`, `sidebar.js`, `toolbar.js`, `layout.js`, `overlay.js`, `statistics.js`: UI abstraction implementations matching the Python viewer components.
- `json_loader.js`: Async HTTP loader for exported project data.
- `workspace.js`: Central state manager mimicking Python's `ProjectWorkspace`.
- `settings.js`: Persistent theme management mimicking `ViewerPreferences`.
