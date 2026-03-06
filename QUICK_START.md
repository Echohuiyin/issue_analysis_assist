# 快速开始指南

## 5分钟快速上手

### 第一步：安装依赖

```bash
# 安装基础依赖
pip install -r requirements.txt

# 初始化数据库
python manage.py migrate
```

### 第二步：安装本地LLM模型（推荐）

#### 方式一：使用Ollama（最简单，推荐）

```bash
# 1. 访问 https://ollama.ai/ 下载安装Ollama

# 2. 下载Qwen 1.8B模型（仅需1.5GB显存）
ollama pull qwen:1.8b

# 3. 启动Ollama服务
ollama serve
```

#### 方式二：使用Transformers

```bash
# 安装依赖
pip install transformers torch accelerate

# 首次运行时会自动下载模型
```

### 第三步：测试系统

```bash
# 测试本地LLM模型
python test_local_llm.py

# 测试案例获取功能
python verify_phase1.py
```

### 第四步：开始使用

#### 1. 获取案例

```python
from cases.acquisition.main import CaseAcquisition

# 创建案例获取实例
ca = CaseAcquisition()

# 从StackOverflow获取案例
ca.acquire_from_stackoverflow(keyword="kernel panic", count=5)

# 从CSDN获取案例
ca.acquire_from_csdn(keyword="内核 panic", count=5)
```

#### 2. 使用LLM解析案例

```python
from cases.acquisition.llm_parser import LLMParser
from cases.acquisition.validators import CaseValidator

# 创建解析器（自动选择本地模型）
parser = LLMParser(llm_type="auto")

# 解析内容
content = """
Linux内核panic问题分析
问题现象：系统出现kernel panic...
根本原因：空指针解引用...
解决方案：添加NULL检查...
"""

case_data = parser.parse(content, use_llm=True)

# 验证质量
validator = CaseValidator()
result = validator.validate(case_data)

print(f"质量分数: {result['quality_score']:.1f}/100")
print(f"高质量案例: {result.get('is_high_quality', False)}")
```

#### 3. 查看案例

```bash
# 启动Django开发服务器
python manage.py runserver

# 访问 http://localhost:8000/admin 查看案例
```

## 常见使用场景

### 场景1：批量获取案例

```python
from cases.acquisition.main import CaseAcquisition

ca = CaseAcquisition()

# 批量获取不同主题的案例
keywords = [
    "kernel panic",
    "memory leak",
    "deadlock",
    "OOM",
    "soft lockup"
]

for keyword in keywords:
    print(f"正在获取: {keyword}")
    ca.acquire_from_stackoverflow(keyword=keyword, count=10)
    ca.acquire_from_csdn(keyword=keyword, count=10)
```

### 场景2：使用LLM优化已有案例

```python
from cases.acquisition.llm_parser import LLMParser
from cases.models import KernelCase

# 获取所有低质量案例
low_quality_cases = KernelCase.objects.filter(
    # 假设我们添加了quality_score字段
)

parser = LLMParser(llm_type="auto")

for case in low_quality_cases:
    # 重新解析
    case_data = parser.parse(case.phenomenon, use_llm=True)
    
    # 更新案例
    if case_data:
        case.phenomenon = case_data.get('phenomenon', case.phenomenon)
        case.root_cause = case_data.get('root_cause', case.root_cause)
        case.solution = case_data.get('solution', case.solution)
        case.save()
```

### 场景3：自定义数据源

```python
from cases.acquisition.fetchers import HTTPFetcher
from cases.acquisition.parsers import BlogParser
from cases.acquisition.storage import CaseStorage

# 自定义爬虫
class MyFetcher(HTTPFetcher):
    def search(self, keyword, count=10):
        # 实现自定义搜索逻辑
        urls = []
        # ...
        return urls

# 使用自定义爬虫
fetcher = MyFetcher()
parser = BlogParser()
storage = CaseStorage()

urls = fetcher.search("kernel panic", count=5)
for url in urls:
    content = fetcher.fetch(url)
    case_data = parser.parse(content)
    if case_data:
        storage.store(case_data)
```

## 性能优化建议

### 1. 使用合适的模型

- **快速测试**：使用Qwen 1.8B（速度快）
- **生产环境**：使用Qwen 7B（准确率高）
- **大量处理**：使用Ollama（稳定性好）

### 2. 批量处理

```python
# 批量处理案例，减少模型加载时间
parser = LLMParser(llm_type="ollama", model="qwen:1.8b")

cases = []
for content in raw_contents:
    case_data = parser.parse(content, use_llm=True)
    if case_data:
        cases.append(case_data)
```

### 3. 质量过滤

```python
# 只保留高质量案例
CONFIDENCE_THRESHOLD = 0.7
QUALITY_SCORE_THRESHOLD = 70

case_data = parser.parse(content, use_llm=True)
validation = validator.validate(case_data)

if (case_data.get('confidence', 0) >= CONFIDENCE_THRESHOLD and
    validation.get('quality_score', 0) >= QUALITY_SCORE_THRESHOLD):
    # 存储高质量案例
    storage.store(case_data)
```

## 故障排查

### 问题1：Ollama连接失败

```bash
# 检查Ollama服务是否运行
curl http://localhost:11434/api/tags

# 如果没有运行，启动服务
ollama serve
```

### 问题2：模型下载慢

```bash
# 使用国内镜像（如果可用）
export OLLAMA_MIRROR=https://your-mirror-url

# 或手动下载模型文件
```

### 问题3：显存不足

```bash
# 使用CPU模式
OLLAMA_GPU=0 ollama run qwen:1.8b

# 或使用更小的模型
ollama pull qwen:1.8b  # 而不是 qwen:7b
```

## 下一步

- 查看 [本地模型部署指南](./LOCAL_LLM_DEPLOYMENT.md) 了解详细安装步骤
- 查看 [LLM解析器使用指南](./LLM_PARSER_GUIDE.md) 了解高级用法
- 查看 [项目进度文档](./PROGRESS_TRACKING.md) 了解完整功能列表

## 获取帮助

- 查看项目文档：`docs/` 目录
- 运行测试脚本：`python test_local_llm.py`
- 查看日志：检查控制台输出