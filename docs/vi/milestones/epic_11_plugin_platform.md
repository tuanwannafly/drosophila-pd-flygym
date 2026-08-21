# Epic 11 — Plugin Platform và tài liệu kỹ thuật tiếng Việt

## Mục tiêu

Epic này mở rộng Fly Studio bằng một plugin platform additive và đồng thời
cung cấp tài liệu tiếng Việt đồng bộ với source. Workflow hiện có và
Workspace source of truth không thay đổi.

## Kiến trúc

```text
Plugin definition
      ↓ validate manifest
PluginLoader
      ↓ dependency check
PluginPlatform
      ↓ lifecycle + capability filter
PluginContext
      ↓
run() / hooks
```

`PluginContext` chỉ chứa metadata plugin và các service hẹp do host cung cấp.
Implementation kiểm tra và từ chối context có key `workspace`, tránh lộ
Workspace nội bộ cho plugin.

## API chính

`PluginPlatform` hỗ trợ:

- `register` / `unregister`;
- `enable` / `disable`;
- `reload` / `unload`;
- `run` và `emit` hook;
- `list` theo capability;
- validate manifest và dependency checking.

Manifest yêu cầu `id`, `name`, `version`, `author`, `description`,
`dependencies` và `capabilities`. Hook chỉ được dùng tên đã đăng ký. Loader
được expose qua `platform.loader`.

## Files mới

- `web/plugin_platform.js`
- `web/plugins/analysis_plugin.js`
- `web/plugins/statistics_plugin.js`
- `web/plugins/export_plugin.js`
- contract tests trong `tests/test_web_experiment_workspace_contract.py`
- tài liệu trong `docs/vi/`

`web/experiment_workspace.js` chỉ được bổ sung `pluginPlatform`; API legacy
`plugins` vẫn tồn tại để giữ backward compatibility.

## Workflow sử dụng

```js
import { PluginPlatform } from './web/plugin_platform.js';
import { analysisPlugin } from './web/plugins/analysis_plugin.js';

const platform = new PluginPlatform();
platform.register(analysisPlugin);
platform.enable(analysisPlugin.manifest.id);
const result = platform.run(analysisPlugin.manifest.id, analysisInput);
platform.disable(analysisPlugin.manifest.id);
```

Trong workflow nghiên cứu, host phải truyền rollout/analysis thật; plugin
không được tự tạo dữ liệu khoa học hoặc sửa frozen evidence.

## Ảnh hưởng

Thay đổi là additive. Không sửa simulation, FlyGym controller, evidence,
notebook, manuscript, release artifact hoặc public API legacy.

## Manual testing

- đăng ký plugin hợp lệ và kiểm tra `list`;
- enable, run, emit hook, disable, reload và unload;
- thử manifest thiếu field;
- thử capability không hợp lệ;
- thử dependency thiếu và dependency cycle;
- xác nhận context không chứa Workspace;
- chạy toàn bộ compileall, pytest và `git diff --check`.
