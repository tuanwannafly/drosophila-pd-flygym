# Động học thuận

`updateWorldTransforms()` truyền transform từ root xuống children:

```text
world_translation = parent_translation
                    + rotate(parent_quaternion, local_translation)
world_quaternion  = parent_quaternion * local_quaternion
```

`validateSkeleton3D()` kiểm tra root, parent-child consistency, quaternion và
bone reachability. Các kiểm tra này là software validation; chúng không phải
biomechanical validation.
