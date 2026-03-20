# 🚀 RAG系统快速启动指南

## 📋 系统要求

### 必需环境
- Python 3.8+
- Django 4.2+
- Ollama (本地LLM服务)
- qwen2.5:0.5b 模型

### 可选环境
- Redis (缓存，可选)
- Nginx (生产部署，可选)

---

## ⚡ 快速启动

### 1. 安装依赖

```bash
cd /home/lmr/project/issue_analysis_assist
pip install -r requirements.txt
```

### 2. 安装 Ollama

```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# 下载模型
ollama pull qwen2.5:0.5b
```

### 3. 初始化数据库

```bash
python manage.py migrate
```

### 4. 启动服务器

```bash
python manage.py runserver
```

### 5. 访问系统

打开浏览器访问：
- **Web界面**: http://localhost:8000/cases/rag/
- **API文档**: 查看 [RAG_API_DOCUMENTATION.md](file:///home/lmr/project/issue_analysis_assist/RAG_API_DOCUMENTATION.md)

---

## 💡 使用方式

### 方式1: Web界面（推荐）

#### 仪表板
```
http://localhost:8000/cases/rag/
```
- 查看系统统计
- 功能入口导航

#### 案例检索
```
http://localhost:8000/cases/rag/search/
```
1. 输入查询内容
2. 调整参数（Top-K、阈值）
3. 点击"开始检索"
4. 查看相似案例

#### 智能问答
```
http://localhost:8000/cases/rag/qa/
```
1. 输入问题
2. 点击"提交问题"
3. 查看答案和引用案例

#### 问题分析
```
http://localhost:8000/cases/rag/analyze/
```
1. 输入问题描述
2. 上传日志（可选）
3. 点击"开始分析"
4. 查看分析结果

---

### 方式2: REST API

#### 案例检索
```bash
curl -X POST http://localhost:8000/cases/api/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "kernel panic 内存崩溃",
    "top_k": 5,
    "threshold": 0.5
  }'
```

#### 智能问答
```bash
curl -X POST http://localhost:8000/cases/api/qa/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何排查内核内存泄漏？",
    "top_k": 3
  }'
```

#### 问题分析
```bash
curl -X POST http://localhost:8000/cases/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "issue_description": "系统运行一段时间后出现kernel panic",
    "logs": "kernel: BUG: unable to handle kernel NULL pointer dereference"
  }'
```

---

### 方式3: CLI工具

#### 检索案例
```bash
python rag_cli.py search "kernel panic" --top-k 5
```

#### 智能问答
```bash
python rag_cli.py qa "如何排查内核内存泄漏？"
```

#### 问题分析
```bash
python rag_cli.py analyze \
  --description "系统崩溃" \
  --logs "kernel panic log"
```

#### 保存结果
```bash
python rag_cli.py qa "如何排查内存泄漏？" --output result.json
```

---

### 方式4: Python代码

```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()

from cases.models import TrainingCase
from cases.rag import get_qa_engine

# 获取案例
cases = list(TrainingCase.objects.exclude(
    embedding__isnull=True
).values(
    'case_id', 'title', 'phenomenon', 'root_cause', 'solution',
    'module', 'source', 'quality_score', 'embedding'
))

# 智能问答
qa_engine = get_qa_engine()
result = qa_engine.answer(
    "如何排查内核内存泄漏？",
    cases,
    top_k=3
)

print(f"答案: {result['answer']}")
print(f"置信度: {result['confidence']:.2%}")
print(f"引用案例: {len(result['cases'])}个")
```

---

## 📊 系统状态检查

### 检查数据
```bash
python check_rag_readiness.py
```

### 测试API
```bash
python test_rag_api.py
```

### 测试Web界面
```bash
python test_rag_web.py
```

---

## 🔧 常见问题

### Q1: Ollama连接失败
**解决方案**：
```bash
# 检查Ollama服务
ollama list

# 重启Ollama
ollama serve

# 重新下载模型
ollama pull qwen2.5:0.5b
```

### Q2: 向量维度不匹配
**解决方案**：
```bash
# 检查向量维度
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()
from cases.models import TrainingCase
case = TrainingCase.objects.first()
print(f'向量维度: {len(case.embedding) if case.embedding else 0}')
"
```

### Q3: 数据库为空
**解决方案**：
```bash
# 检查案例数量
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kernel_cases.settings')
import django
django.setup()
from cases.models import TrainingCase
print(f'训练案例: {TrainingCase.objects.count()}个')
"
```

### Q4: Web界面加载慢
**解决方案**：
- 检查Ollama响应速度
- 减少top_k参数值
- 使用更快的模型（如qwen2.5:0.5b）

---

## 📈 性能优化建议

### 1. 使用缓存
```python
# 在settings.py中添加
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 2. 批量处理
- 使用异步任务处理大量请求
- 实现请求队列机制

### 3. 模型优化
- 使用更快的模型（qwen2.5:0.5b）
- 考虑使用GPU加速

---

## 📚 更多文档

- [API文档](file:///home/lmr/project/issue_analysis_assist/RAG_API_DOCUMENTATION.md)
- [系统状态](file:///home/lmr/project/issue_analysis_assist/RAG_SYSTEM_STATUS.md)
- [完成报告](file:///home/lmr/project/issue_analysis_assist/RAG_PROJECT_COMPLETE_REPORT.md)
- [进度跟踪](file:///home/lmr/project/issue_analysis_assist/PROGRESS_TRACKING.md)

---

## 🎯 快速测试

### 测试案例检索
```bash
# Web界面
访问: http://localhost:8000/cases/rag/search/
输入: kernel panic
点击: 开始检索

# CLI工具
python rag_cli.py search "kernel panic" --top-k 3

# API
curl -X POST http://localhost:8000/cases/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "kernel panic", "top_k": 3}'
```

### 测试智能问答
```bash
# Web界面
访问: http://localhost:8000/cases/rag/qa/
输入: 如何排查内核内存泄漏？
点击: 提交问题

# CLI工具
python rag_cli.py qa "如何排查内核内存泄漏？"

# API
curl -X POST http://localhost:8000/cases/api/qa/ \
  -H "Content-Type: application/json" \
  -d '{"question": "如何排查内核内存泄漏？"}'
```

---

## ✅ 检查清单

启动前检查：
- [ ] Python 3.8+ 已安装
- [ ] Django 4.2+ 已安装
- [ ] Ollama 已安装并运行
- [ ] qwen2.5:0.5b 模型已下载
- [ ] 数据库已迁移
- [ ] 训练案例已导入（至少160个）
- [ ] 向量嵌入已生成（100%完成）

功能测试：
- [ ] Web界面可以访问
- [ ] 案例检索功能正常
- [ ] 智能问答功能正常
- [ ] 问题分析功能正常
- [ ] API接口响应正常
- [ ] CLI工具运行正常

---

**祝您使用愉快！** 🎉

如有问题，请查看详细文档或联系开发团队。