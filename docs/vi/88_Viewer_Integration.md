# Viewer Integration

`viewer_bridge.js` la adapter giua Workspace va Viewer hien co. Bridge goi
`setFrame`, `resetView`, `focusBodyPart` va renderer hien co; no khong biet
JSON loader va khong sua scene.

Voi `viewer_pose.json`:

1. Viewer doc pose document.
2. App nap cung frame vao Workspace.
3. Timeline seek se goi Viewer voi frame chung.
4. Inspector va status bar doc cung frame tu Workspace.

Viewer van co the xu ly FlyGym rollout thong qua DigitalFly3D nhu truoc.
