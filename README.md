# Multi-Agent Chatbot

## Setup

### 1. Check your CUDA version

```bash
nvidia-smi
```

### 2. Update the PyTorch index in `pyproject.toml` if needed

```toml
# Change cu130 to match your CUDA version
# CUDA 13.0 → cu130
# CUDA 12.8 → cu128
# CUDA 12.1 → cu121
# CPU only  → remove [tool.uv.sources] block entirely and use torch>=2.9.1
url = "https://download.pytorch.org/whl/cu130"
```

### 3. Install

```bash
uv sync
```
