# Developer Guide

When developing the GUI layer:
- Bind your specific GUI framework components (e.g., QSlider, HTML `<video>`) to these panel classes.
- Do NOT add Qt/OpenGL/Three.js specific code to the viewer subsystem.
- Trigger `ViewerEvents` for cross-panel communications rather than direct references.
