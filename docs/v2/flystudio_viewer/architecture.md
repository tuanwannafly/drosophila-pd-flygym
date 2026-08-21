# Architecture

The Viewer provides a Model-View-Controller (MVC) like separation between UI abstraction and backend states:
- **Global State**: `ViewerState` holds runtime toggles and play states. `ViewerPreferences` holds persistent settings.
- **Layout & Panels**: `ViewerLayout` specifies viewport arrangements. The individual panels (`TimelinePanel`, `CameraPanel`, `PlaybackPanel`, `SelectionPanel`, `StatisticsPanel`, `RecordingPanel`) act as abstractions that GUI frameworks (e.g. PySide, DearPyGui, Web UI) can bind to.
- **Controllers**: `ViewportController` manages viewport-specific rendering toggles (grid, skeleton).
- **Workspace & Sessions**: `ViewerSession` wraps the full application state, and `ProjectWorkspace` represents active open files.
- **Event Bus**: `ViewerEvents` allows loose coupling between viewer components and external plugins.
- **Persistence**: `ViewerSerializer` exports/imports application layouts and states.
