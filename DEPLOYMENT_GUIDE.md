# Deployment Guide - Local LLM Setup

## 📋 Overview

This guide covers the deployment of local LLM models for the Linux Kernel Issue Analysis System.

**Recommended Setup**: Ollama + Qwen 2.5 0.5B (CPU-optimized)

---

## 🚀 Quick Start

### Option 1: Ollama (Recommended for CPU)

#### 1. Install Ollama
```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from https://ollama.com/download
```

#### 2. Pull Model
```bash
# Pull Qwen 2.5 0.5B (fast, CPU-optimized)
ollama pull qwen2.5:0.5b

# Alternative models
ollama pull qwen2.5:1.5b    # Better quality, slower
ollama pull llama3.2:1b     # Alternative option
```

#### 3. Test Installation
```bash
ollama run qwen2.5:0.5b

# Test prompt
>>> 你好，请介绍一下自己
```

#### 4. Configure System
```python
# kernel_cases/settings.py
OLLAMA_BASE_URL = 'http://localhost:11434'
OLLAMA_MODEL = 'qwen2.5:0.5b'
```

---

### Option 2: vLLM (For GPU acceleration)

#### 1. Install vLLM
```bash
pip install vllm
```

#### 2. Start vLLM Server
```bash
python -m vllm.entrypoints.api_server \
    --model Qwen/Qwen2.5-0.5B \
    --host 0.0.0.0 \
    --port 8000
```

#### 3. Configure System
```python
# kernel_cases/settings.py
VLLM_BASE_URL = 'http://localhost:8000'
VLLM_MODEL = 'Qwen/Qwen2.5-0.5B'
```

---

## 📊 Model Comparison

| Model | Size | Speed | Quality | CPU Support | GPU Support |
|-------|------|-------|---------|-------------|-------------|
| qwen2.5:0.5b | 0.5B | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | ✅ Excellent | ✅ Good |
| qwen2.5:1.5b | 1.5B | ⚡⚡⚡ | ⭐⭐⭐⭐ | ✅ Good | ✅ Excellent |
| qwen2.5:7b | 7B | ⚡ | ⭐⭐⭐⭐⭐ | ⚠️ Slow | ✅ Excellent |
| llama3.2:1b | 1B | ⚡⚡⚡⚡ | ⭐⭐⭐ | ✅ Good | ✅ Good |

**Recommendation**: 
- **CPU-only**: qwen2.5:0.5b (fastest)
- **GPU available**: qwen2.5:1.5b (best balance)

---

## ⚙️ Configuration

### Ollama Configuration

#### API Endpoint
```python
# cases/acquisition/llm_integration.py
class OllamaLLM:
    def __init__(self, model='qwen2.5:0.5b', base_url='http://localhost:11434'):
        self.model = model
        self.base_url = base_url
```

#### Model Parameters
```python
# Generation parameters
params = {
    'temperature': 0.7,      # Creativity (0-1)
    'top_p': 0.9,            # Nucleus sampling
    'top_k': 40,             # Top-k sampling
    'num_predict': 2048,     # Max tokens
    'stop': ['\n\n\n'],      # Stop sequences
}
```

### vLLM Configuration

#### Server Parameters
```bash
# GPU memory utilization
--gpu-memory-utilization 0.9

# Tensor parallelism (multi-GPU)
--tensor-parallel-size 2

# Max model length
--max-model-len 4096
```

---

## 🔧 Performance Tuning

### CPU Optimization

#### 1. Thread Configuration
```bash
# Set number of threads
export OLLAMA_NUM_PARALLEL=4
export OLLAMA_MAX_LOADED_MODELS=1
```

#### 2. Memory Management
```bash
# Monitor memory usage
htop

# Check Ollama status
ollama ps
```

#### 3. Batch Processing
```python
# Process multiple cases in parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_case, cases)
```

### GPU Optimization

#### 1. CUDA Configuration
```bash
# Check GPU availability
nvidia-smi

# Set CUDA devices
export CUDA_VISIBLE_DEVICES=0,1
```

#### 2. Memory Optimization
```python
# vLLM memory settings
--gpu-memory-utilization 0.85
--max-model-len 2048
```

---

## 🧪 Testing

### Test LLM Connection
```python
# test_llm_connection.py
import requests

response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'qwen2.5:0.5b',
        'prompt': 'Hello, world!',
        'stream': False
    }
)

print(response.json())
```

### Test JSON Output
```python
# test_llm_json.py
prompt = """
请以JSON格式输出以下信息：
{
    "name": "测试",
    "value": 123
}
"""

response = llm.generate(prompt)
print(response)
```

### Performance Benchmark
```bash
# Benchmark script
python test_model_performance.py --model qwen2.5:0.5b --cases 10
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Ollama Connection Failed
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama service
ollama serve

# Check port
netstat -tulpn | grep 11434
```

#### 2. Out of Memory
```bash
# Reduce model size
ollama pull qwen2.5:0.5b

# Or use quantized model
ollama pull qwen2.5:0.5b-q4_0
```

#### 3. Slow Response
```bash
# Check CPU usage
htop

# Reduce parallel requests
export OLLAMA_NUM_PARALLEL=1

# Use smaller model
ollama pull qwen2.5:0.5b
```

#### 4. JSON Parsing Errors
```python
# Use structured prompt
prompt = """
请严格按照JSON格式输出，不要包含其他内容：
{"key": "value"}
"""
```

---

## 📊 Monitoring

### Ollama Monitoring
```bash
# List models
ollama list

# Show model info
ollama show qwen2.5:0.5b

# Monitor running models
ollama ps
```

### Performance Metrics
```python
# Track response time
import time

start = time.time()
response = llm.generate(prompt)
elapsed = time.time() - start

print(f"Response time: {elapsed:.2f}s")
```

---

## 🔄 Model Management

### Download Models
```bash
# Pull model
ollama pull qwen2.5:0.5b

# List downloaded models
ollama list
```

### Update Models
```bash
# Update to latest version
ollama pull qwen2.5:0.5b
```

### Delete Models
```bash
# Remove model
ollama rm qwen2.5:0.5b
```

---

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
# Dockerfile
FROM ollama/ollama:latest

# Pull model
RUN ollama pull qwen2.5:0.5b

# Expose port
EXPOSE 11434

# Start server
CMD ["ollama", "serve"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_NUM_PARALLEL=4

volumes:
  ollama_data:
```

### Systemd Service
```ini
# /etc/systemd/system/ollama.service
[Unit]
Description=Ollama Service
After=network.target

[Service]
Type=simple
User=ollama
ExecStart=/usr/bin/ollama serve
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📚 Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [vLLM Documentation](https://github.com/vllm-project/vllm)
- [Qwen Model Card](https://huggingface.co/Qwen)
- [Performance Benchmarks](./PERFORMANCE_BENCHMARKS.md)

---

## 🎯 Recommendations

### For Development
- **Model**: qwen2.5:0.5b
- **Engine**: Ollama
- **Configuration**: Default settings

### For Production (CPU)
- **Model**: qwen2.5:1.5b
- **Engine**: Ollama
- **Configuration**: Multi-threading enabled

### For Production (GPU)
- **Model**: qwen2.5:7b
- **Engine**: vLLM
- **Configuration**: GPU memory optimization

---

**Last Updated**: 2026-03-20  
**Tested Models**: qwen2.5:0.5b, qwen2.5:1.5b, llama3.2:1b