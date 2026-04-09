# Capstone — unified task runner

default:
    @just --list

# --- Hardware ---

hw-build:
    @echo "TODO: firmware build command"

hw-test:
    @echo "TODO: hardware test runner"

# --- Software ---

sw-build:
    @echo "TODO: software build command"

sw-test:
    @echo "TODO: software test runner"

# --- ML ---

ml-train:
    @echo "TODO: training entrypoint"

ml-eval:
    @echo "TODO: evaluation runner"

ml-export:
    @echo "TODO: model export (ONNX/TFLite)"

# --- Cross-cutting ---

test-all: hw-test sw-test ml-eval

docs-serve:
    @echo "TODO: docs server"
