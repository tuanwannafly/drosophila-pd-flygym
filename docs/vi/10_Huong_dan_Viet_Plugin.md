# 11. Hướng dẫn viết Plugin

Plugin phải khai báo manifest đầy đủ:

```js
const plugin = {
  manifest: {
    id: 'example.analysis',
    name: 'Example Analysis',
    version: '1.0.0',
    author: 'Developer',
    description: 'Extension boundary',
    dependencies: [],
    capabilities: ['analysis'],
  },
  run(input, context) {
    return { input, pluginId: context.plugin.id };
  },
};
```

## Quy tắc

- Chỉ dùng capability đã khai báo.
- Dùng `context.get()` hoặc `context.getState()` khi host expose service.
- Không đặt `workspace` vào context.
- Không tự tạo hoặc sửa scientific evidence.
- Hook phải thuộc danh sách đã đăng ký.
- Dependency phải là plugin id đã register.
- Lifecycle cần có cleanup khi plugin unload.

Có thể xem ví dụ tại `web/plugins/analysis_plugin.js`,
`statistics_plugin.js` và `export_plugin.js`.
