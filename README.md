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

### 4. Docker configurations

1. Create a network

```bash
docker network create chatbot-network
```

2. Create a Docker volume

```bash
docker volume create chatbot-pgdata
```

3. Run the pgvector container

```bash
docker run -d `
>>   --name chatbotdb `
>>   --network chatbot-network `
>>   --restart unless-stopped `
>>   --env-file .env `
>>   -p 5432:5432 `
>>   -v chatbot-pgdata:/var/lib/postgresql `
>>   pgvector/pgvector:0.8.2-pg18-trixie
```
