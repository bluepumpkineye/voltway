# HDRIs

The worlds the cars stand in, from Poly Haven (CC0). They are not in git
(25 MB each); download the 4k .hdr files into this folder before a cabin
bake or an `export_outside()`:

| File | Used by | Source |
|---|---|---|
| `shanghai_riverside_4k.hdr` | Xiaomi SU7 Ultra (`export_gltf.OUTSIDE`) | https://polyhaven.com/a/shanghai_riverside |
| `zhengyang_gate_4k.hdr` | Luxeed RX (`export_rx.OUTSIDE`) | https://polyhaven.com/a/zhengyang_gate |

Direct links:

    https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/shanghai_riverside_4k.hdr
    https://dl.polyhaven.org/file/ph-assets/HDRIs/hdr/4k/zhengyang_gate_4k.hdr

The web app does not need them: it ships the tone-mapped view and the light
HDR derived from them (`public/models/*-outside.jpg`, `*-outside-light.hdr`).
