# Ollama CPU部署指南（适用于i5-1155G7 + 16GB内存）

## 系统配置
- CPU: Intel i5-1155G7 @ 2.50GHz (4核8线程)
- RAM: 16GB
- 推理方式: CPU推理（不使用GPU）

## 第一步：手动下载Ollama

### 方法1：直接下载安装包
1. 打开浏览器，访问以下任一链接：
   - 官方：https://ollama.ai/download
   - GitHub：https://github.com/ollama/ollama/releases
   - 镜像：https://ghproxy.com/https://github.com/ollama/ollama/releases/download/v0.1.26/OllamaSetup.exe

2. 下载 `OllamaSetup.exe`（约200MB）

3. 双击安装，按提示完成安装

### 方法2：使用便携版（无需安装）
1. 下载便携版：
   - https://github.com/ollama/ollama/releases/download/v0.1.26/ollama-windows-amd64.zip

2. 解压到任意目录，如：`D:\ollama`

3. 添加到系统PATH：
   ```powershell
   # 临时添加（当前会话有效）
   $env:PATH += ";D:\ollama"
   
   # 永久添加（需要管理员权限）
   [Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";D:\ollama", "User")
   ```

## 第二步：配置CPU推理模式

### 设置环境变量
```powershell
# 强制使用CPU推理
$env:OLLAMA_GPU = "0"

# 设置模型存储路径（可选，默认在用户目录）
$env:OLLAMA_MODELS = "D:\ollama_models"

# 设置并发数（根据CPU核心数调整）
$env:OLLAMA_NUM_PARALLEL = "2"
```

### 永久设置（推荐）
创建或编辑文件 `C:\Users\你的用户名\.ollama\env`：
```
OLLAMA_GPU=0
OLLAMA_MODELS=D:\ollama_models
OLLAMA_NUM_PARALLEL=2
```

## 第三步：启动Ollama服务

### 启动服务
```powershell
# 启动Ollama服务
ollama serve
```

服务将在 http://localhost:11434 运行

### 验证服务
打开新的PowerShell窗口：
```powershell
# 检查服务状态
curl http://localhost:11434/api/tags

# 或使用浏览器访问
start http://localhost:11434
```

## 第四步：下载模型

### 下载Qwen 1.8B（推荐，适合CPU推理）
```powershell
# 下载模型（约1.5GB）
ollama pull qwen:1.8b

# 查看已下载的模型
ollama list
```

### 测试模型
```powershell
# 交互式测试
ollama run qwen:1.8b

# 输入测试问题
>>> 你好，请用一句话介绍Linux内核
```

### 下载其他模型（可选）
```powershell
# Qwen 7B（效果更好，但CPU推理较慢）
ollama pull qwen:7b

# ChatGLM3（中文效果好）
ollama pull chatglm3

# Llama2（英文效果好）
ollama pull llama2
```

## 第五步：在项目中使用

### 测试连接
```powershell
cd D:\develop\08_database
python test_local_llm.py
```

### 使用示例
```python
from cases.acquisition.llm_parser import LLMParser

# 使用Ollama CPU推理
parser = LLMParser(llm_type="ollama", model="qwen:1.8b")

# 解析案例
case_data = parser.parse(content, use_llm=True)
```

## 性能优化建议

### 1. 调整并发数
根据CPU核心数调整：
```powershell
# i5-1155G7有4核8线程，建议设置2-4
$env:OLLAMA_NUM_PARALLEL = "2"
```

### 2. 使用量化模型
```powershell
# Qwen 1.8B的量化版本（更小更快）
ollama pull qwen:1.8b-q4_0
```

### 3. 批量处理
```python
# 批量处理案例，减少模型加载时间
parser = LLMParser(llm_type="ollama", model="qwen:1.8b")

for content in contents:
    case_data = parser.parse(content, use_llm=True)
    # 处理案例...
```

## 预期性能

### Qwen 1.8B (CPU推理)
- 内存占用：约2GB
- 推理速度：约2-3秒/案例
- 准确率：约85%
- 适合场景：快速测试、大量案例处理

### Qwen 7B (CPU推理)
- 内存占用：约8GB
- 推理速度：约5-8秒/案例
- 准确率：约92%
- 适合场景：高质量要求、少量案例处理

## 故障排查

### 问题1：服务无法启动
```powershell
# 检查端口是否被占用
netstat -ano | findstr :11434

# 结束占用进程
taskkill /F /PID <进程ID>
```

### 问题2：模型下载失败
```powershell
# 使用国内镜像（如果有）
$env:OLLAMA_MIRROR = "https://your-mirror-url"

# 或手动下载模型文件
# 访问 https://ollama.ai/library/qwen:1.8b
```

### 问题3：内存不足
```powershell
# 关闭其他程序
# 或使用更小的模型
ollama pull qwen:1.8b  # 而不是 qwen:7b
```

### 问题4：推理速度慢
```powershell
# 减少并发数
$env:OLLAMA_NUM_PARALLEL = "1"

# 使用量化模型
ollama pull qwen:1.8b-q4_0
```

## 完整安装脚本

创建文件 `install_ollama.ps1`：
```powershell
# Ollama CPU部署脚本

Write-Host "开始安装Ollama..." -ForegroundColor Green

# 1. 设置环境变量
Write-Host "配置环境变量..." -ForegroundColor Yellow
$env:OLLAMA_GPU = "0"
$env:OLLAMA_MODELS = "D:\ollama_models"
$env:OLLAMA_NUM_PARALLEL = "2"

# 2. 创建模型目录
Write-Host "创建模型目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "D:\ollama_models"

# 3. 检查Ollama是否已安装
Write-Host "检查Ollama..." -ForegroundColor Yellow
try {
    $version = ollama --version
    Write-Host "Ollama已安装: $version" -ForegroundColor Green
} catch {
    Write-Host "Ollama未安装，请手动下载安装" -ForegroundColor Red
    Write-Host "下载地址: https://ollama.ai/download" -ForegroundColor Cyan
    exit 1
}

# 4. 启动服务
Write-Host "启动Ollama服务..." -ForegroundColor Yellow
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

# 5. 等待服务启动
Start-Sleep -Seconds 5

# 6. 下载模型
Write-Host "下载Qwen 1.8B模型..." -ForegroundColor Yellow
ollama pull qwen:1.8b

# 7. 验证安装
Write-Host "验证安装..." -ForegroundColor Yellow
ollama list

Write-Host "安装完成！" -ForegroundColor Green
Write-Host "运行测试: python test_local_llm.py" -ForegroundColor Cyan
```

运行脚本：
```powershell
powershell -ExecutionPolicy Bypass -File install_ollama.ps1
```

## 下一步

1. 安装完成后，运行测试：
   ```powershell
   python test_local_llm.py
   ```

2. 开始使用：
   ```powershell
   python verify_phase1.py
   ```

3. 查看更多文档：
   - [快速开始指南](./QUICK_START.md)
   - [本地模型部署指南](./LOCAL_LLM_DEPLOYMENT.md)