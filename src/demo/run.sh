#!/usr/bin/env bash

export PYTHONPATH="../../"

demos="$(find $PYTHONPATH -type f -iname '*_demo.py' -exec basename {} \;)"

if [[ $# -eq 0 ]]; then
  echo "Please select one demo to run:"
  echo ''
  echo "${demos}"
  echo ''
else
  args=(${@})
  demo_py=$(find . -type f -iname "${args[0]}" | head -n 1)
  pushd "$(dirname "${demo_py}")" &>/dev/null || exit 1
  python3 "$(basename "${demo_py}")" "${args[@]:1}"
  popd &>/dev/null || exit 1
fi
