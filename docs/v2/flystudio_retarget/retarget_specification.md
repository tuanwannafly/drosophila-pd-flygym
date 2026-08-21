# Retarget Specification

A retarget profile defines source channels mapping to target node IDs.
If a data channel mapped by a `RetargetMapping` is not found in the `PlaybackFrame`, the builder will safely skip that joint.
Use `PoseValidator` post-construction if you need strict validation.
Poses serialize directly to JSON using standard tuple expansions for transforms.
