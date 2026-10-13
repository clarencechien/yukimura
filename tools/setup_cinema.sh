#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cinema_tools="${CINEMA_TOOLS:-/workspace/yukimura-tools}"
export UV_PYTHON_INSTALL_DIR="$cinema_tools/python"
export UV_PYTHON_BIN_DIR="$cinema_tools/python-bin"
export UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.uv-cache}"
export UV_SYSTEM_CERTS=true
mkdir -p "$UV_PYTHON_BIN_DIR"
uv python install 3.11.17
if [[ ! -x "$cinema_tools/render-env/bin/python" ]]; then
  uv venv --python 3.11.17 "$cinema_tools/render-env"
fi
uv pip install --python "$cinema_tools/render-env/bin/python" --index-url https://pypi.org/simple -r tools/cinema-requirements.txt
"$cinema_tools/render-env/bin/python" -c "import bpy,numpy; print('Cinema runtime:',bpy.app.version_string,'NumPy',numpy.__version__)"
