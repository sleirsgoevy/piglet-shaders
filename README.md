# Piglet custom shader PoC

This is a PoC for compiling Piglet fragment shaders using Mesa3D.

* You need to provide a compatible vertex shader, it's needed because Mesa3D compiles both shaders at once.
* At most one sampler is currently supported.
* This a PoC and can break at any time.

`victim.c` is loosely based on [this EGL sample](https://github.com/svenpilz/egl_offscreen_opengl)

## Dependencies

* Mesa3D (obviously)
* [CLRX](https://github.com/CLRX/CLRX-mirror)

## Usage

```
cd compiler
make
bash compile.sh vertex.glsl fragment.glsl output.bin # only outputs the fragment part for now
```

## Known non-trivial bugs (require Mesa patching to fix)

* Matrices other than `mat4` are broken (std140)
* Arrays of anything but `vec4` and `mat4` are broken (std140)
* Constant arrays are not supported, pass them as uniforms instead
