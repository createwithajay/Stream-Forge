"""
VisionEdge Model Compilation Module

Provides a hardware-aware workflow for:
PyTorch model -> ONNX -> TensorRT

The module never reports a successful TensorRT compilation unless
the required dependencies and NVIDIA hardware are actually available.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path


def package_available(package_name: str) -> bool:
    """Return True when a Python package can be imported."""
    return importlib.util.find_spec(package_name) is not None


def nvidia_smi_available() -> bool:
    """Check whether NVIDIA's nvidia-smi command is available."""
    return shutil.which("nvidia-smi") is not None


def get_hardware_status() -> dict:
    """Detect the software and hardware required for GPU compilation."""
    return {
        "python": True,
        "pytorch": package_available("torch"),
        "onnx": package_available("onnx"),
        "onnxruntime": package_available("onnxruntime"),
        "tensorrt": package_available("tensorrt"),
        "cuda": nvidia_smi_available(),
        "ultralytics": package_available("ultralytics"),
        "cupy": package_available("cupy"),
    }


def get_nvidia_info() -> dict | None:
    """Return NVIDIA GPU information when nvidia-smi is available."""
    if not nvidia_smi_available():
        return None

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return None

        parts = [item.strip() for item in result.stdout.strip().split(",")]

        return {
            "name": parts[0] if len(parts) > 0 else "Unknown",
            "driver_version": parts[1] if len(parts) > 1 else "Unknown",
            "memory_total": parts[2] if len(parts) > 2 else "Unknown",
        }

    except (subprocess.SubprocessError, OSError):
        return None


def compilation_capability() -> dict:
    """
    Determine whether real TensorRT compilation can be performed.
    """
    status = get_hardware_status()

    required = {
        "pytorch": status["pytorch"],
        "onnx": status["onnx"],
        "tensorrt": status["tensorrt"],
        "cuda": status["cuda"],
    }

    ready = all(required.values())

    missing = [
        component
        for component, available in required.items()
        if not available
    ]

    return {
        "ready": ready,
        "required_components": required,
        "missing_components": missing,
        "mode": "REAL_TENSORRT" if ready else "SIMULATED",
    }


def compile_to_onnx(
    model_path: str | Path,
    output_path: str | Path,
) -> dict:
    """
    Convert a PyTorch model to ONNX.

    This function performs the conversion only when PyTorch and ONNX
    are actually installed.
    """
    model_path = Path(model_path)
    output_path = Path(output_path)

    if not model_path.exists():
        return {
            "status": "failed",
            "stage": "onnx",
            "message": f"Model not found: {model_path}",
        }

    if not package_available("torch"):
        return {
            "status": "unavailable",
            "stage": "onnx",
            "message": "PyTorch is not installed.",
            "mode": "SIMULATED",
        }

    if not package_available("onnx"):
        return {
            "status": "unavailable",
            "stage": "onnx",
            "message": "ONNX is not installed.",
            "mode": "SIMULATED",
        }

    try:
        import torch

        model = torch.load(
            model_path,
            map_location="cpu",
            weights_only=False,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        torch.onnx.export(
            model,
            args=(),
            f=str(output_path),
            opset_version=17,
        )

        return {
            "status": "compiled",
            "stage": "onnx",
            "output": str(output_path),
            "mode": "REAL",
        }

    except Exception as exc:
        return {
            "status": "failed",
            "stage": "onnx",
            "message": str(exc),
        }


def compile_to_tensorrt(
    onnx_path: str | Path,
    engine_path: str | Path,
) -> dict:
    """
    Convert an ONNX model to a TensorRT engine.

    Actual compilation is performed only when TensorRT and NVIDIA
    GPU support are available.
    """
    onnx_path = Path(onnx_path)
    engine_path = Path(engine_path)

    capability = compilation_capability()

    if not onnx_path.exists():
        return {
            "status": "failed",
            "stage": "tensorrt",
            "message": f"ONNX model not found: {onnx_path}",
        }

    if not capability["ready"]:
        return {
            "status": "unavailable",
            "stage": "tensorrt",
            "mode": "SIMULATED",
            "missing_components": capability["missing_components"],
            "message": (
                "Real TensorRT compilation requires the NVIDIA/CUDA "
                "environment and TensorRT dependencies."
            ),
        }

    try:
        import tensorrt as trt

        logger = trt.Logger(trt.Logger.WARNING)

        builder = trt.Builder(logger)
        network = builder.create_network(
            1 << int(
                trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH
            )
        )

        parser = trt.OnnxParser(network, logger)

        with open(onnx_path, "rb") as model_file:
            parsed = parser.parse(model_file.read())

        if not parsed:
            errors = []

            for index in range(parser.num_errors):
                errors.append(str(parser.get_error(index)))

            return {
                "status": "failed",
                "stage": "tensorrt",
                "message": "ONNX parsing failed.",
                "errors": errors,
            }

        config = builder.create_builder_config()

        serialized_engine = builder.build_serialized_network(
            network,
            config,
        )

        if serialized_engine is None:
            return {
                "status": "failed",
                "stage": "tensorrt",
                "message": "TensorRT failed to build the engine.",
            }

        engine_path.parent.mkdir(parents=True, exist_ok=True)

        with open(engine_path, "wb") as engine_file:
            engine_file.write(serialized_engine)

        return {
            "status": "compiled",
            "stage": "tensorrt",
            "output": str(engine_path),
            "mode": "REAL_TENSORRT",
        }

    except Exception as exc:
        return {
            "status": "failed",
            "stage": "tensorrt",
            "message": str(exc),
        }


def compile_model(
    model_path: str | Path,
    onnx_path: str | Path,
    engine_path: str | Path,
) -> dict:
    """
    Complete PyTorch -> ONNX -> TensorRT compilation workflow.
    """
    capability = compilation_capability()

    if not capability["ready"]:
        return {
            "status": "unavailable",
            "mode": "SIMULATED",
            "hardware": get_hardware_status(),
            "nvidia": get_nvidia_info(),
            "missing_components": capability["missing_components"],
            "message": (
                "Compilation pipeline is configured, but real GPU "
                "compilation is unavailable on this machine."
            ),
        }

    onnx_result = compile_to_onnx(
        model_path=model_path,
        output_path=onnx_path,
    )

    if onnx_result["status"] != "compiled":
        return onnx_result

    return compile_to_tensorrt(
        onnx_path=onnx_path,
        engine_path=engine_path,
    )


if __name__ == "__main__":
    print("VisionEdge Model Compiler")
    print("=" * 30)

    capability = compilation_capability()

    print("Hardware/software status:")
    for key, value in get_hardware_status().items():
        print(f"  {key}: {value}")

    print()
    print(f"Compilation mode: {capability['mode']}")

    if capability["missing_components"]:
        print("Missing components:")
        for component in capability["missing_components"]:
            print(f"  - {component}")
    else:
        print("All required components are available.")