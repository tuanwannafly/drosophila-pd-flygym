# Colab

Colab là môi trường được dùng để chạy FlyGym/MuJoCo thật. Sau khi cài đúng
phiên bản, nạp cấu hình và gọi pipeline hiện hành; không chạy simulation từ
CI hoặc từ unit test adapter.

```python
from drosophila_pd.flygym_adapter import FlyGymConfig, FlyGymAdapter

config = FlyGymConfig.from_yaml("configs/v2/flygym/healthy.yaml")
adapter = FlyGymAdapter()
fly = adapter.create_fly(config.fly)
world = adapter.create_world(config.world)
adapter.attach_fly(
    world,
    fly,
    position=config.world.spawn_position,
    orientation=config.world.spawn_orientation,
    add_ground_contact_sensors=config.world.add_ground_contact_sensors,
)
simulation = adapter.create_simulation(world, config.simulation)
```

Đoạn trên chỉ xác minh construction. Muốn ghi rollout, gắn `RolloutRecorder`
và chạy `FlyGymRuntime` với số bước hữu hạn. Kết quả vẫn là dữ liệu mô phỏng
tính toán, không phải validation sinh học.
