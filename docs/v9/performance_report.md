# Performance Report

V9 performs metadata discovery, event persistence, and task orchestration. It
does not load rollout arrays or execute FlyGym/MuJoCo. Runtime cost is therefore
dominated by filesystem metadata operations under the selected output root.
