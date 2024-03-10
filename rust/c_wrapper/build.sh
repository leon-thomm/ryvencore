set -e

cargo build --release
cbindgen --config cbindgen.toml --crate c_wrapper --output ryvencore.h