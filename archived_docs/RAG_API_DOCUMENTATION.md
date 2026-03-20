# RAG系统API文档

## 📋 概述

RAG系统提供REST API接口，支持案例检索、推荐、智能问答和问题分析功能。

**基础URL**: `http://localhost:8000/cases/api/`

**认证**: 当前无需认证（开发环境）

**响应格式**: JSON

---

## 🔌 API端点

### 1. 健康检查

**端点**: `GET /api/health/`

**描述**: 检查API服务状态

**请求示例**:
```bash
curl http://localhost:8000/cases/api/health/
```

**响应示例**:
```json
{
    "status": "ok",
    "service": "RAG API",
    "version": "1.0",
    "training_cases": 160
}
```

---

### 2. 案例检索

**端点**: `POST /api/search/`

**描述**: 基于语义相似度检索相关案例

**请求参数**:
```json
{
    "query": "问题描述",
    "top_k": 5,
    "threshold": 0.5
}
```

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| query | string | 是 | - | 查询内容 |
| top_k | integer | 否 | 5 | 返回案例数量 |
| threshold | float | 否 | 0.5 | 相似度阈值（0-1） |

**请求示例**:
```bash
curl -X POST http://localhost:8000/cases/api/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "kernel panic 内存崩溃",
    "top_k": 3,
    "threshold": 0.5
  }'
```

**响应示例**:
```json
{
    "success": true,
    "cases": [
        {
            "case_id": "TC_001",
            "title": "Linux内核问题分析报告",
            "phenomenon": "系统运行时出现kernel panic...",
            "root_cause": "内存分配失败导致...",
            "solution": "优化内存管理策略...",
            "module": "memory",
            "source": "github",
            "quality_score": 65.0,
            "similarity": 0.8878
        }
    ],
    "count": 3,
    "query": "kernel panic 内存崩溃"
}
```

---

### 3. 案例推荐

**端点**: `POST /api/recommend/`

**描述**: 基于问题描述推荐相关案例

**请求参数**:
```json
{
    "problem_description": "问题描述",
    "top_k": 5,
    "min_similarity": 0.5
}
```

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| problem_description | string | 是 | - | 问题描述 |
| top_k | integer | 否 | 5 | 返回案例数量 |
| min_similarity | float | 否 | 0.5 | 最小相似度阈值 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/cases/api/recommend/ \
  -H "Content-Type: application/json" \
  -d '{
    "problem_description": "系统出现内存泄漏问题",
    "top_k": 3,
    "min_similarity": 0.5
  }'
```

**响应示例**:
```json
{
    "success": true,
    "recommendations": [
        {
            "case_id": "TC_002",
            "title": "内核内存泄漏排查案例",
            "similarity": 0.8940,
            "confidence": 0.7889,
            "recommendation_reason": "该案例涉及内存泄漏问题..."
        }
    ],
    "count": 3,
    "problem_description": "系统出现内存泄漏问题"
}
```

---

### 4. 智能问答

**端点**: `POST /api/qa/`

**描述**: 基于检索结果生成智能答案

**请求参数**:
```json
{
    "question": "问题",
    "top_k": 3,
    "min_similarity": 0.5
}
```

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| question | string | 是 | - | 用户问题 |
| top_k | integer | 否 | 3 | 引用案例数量 |
| min_similarity | float | 否 | 0.5 | 最小相似度阈值 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/cases/api/qa/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "系统出现kernel panic怎么办？",
    "top_k": 3,
    "min_similarity": 0.5
  }'
```

**响应示例**:
```json
{
    "success": true,
    "answer": "kernel panic是Linux内核的严重错误...",
    "confidence": 0.8491,
    "cases": [
        {
            "case_id": "TC_001",
            "title": "Linux内核问题分析报告",
            "similarity": 0.8878
        }
    ],
    "sources": [
        {
            "case_id": "TC_001",
            "title": "Linux内核问题分析报告",
            "source": "github",
            "similarity": 0.8878
        }
    ],
    "question": "系统出现kernel panic怎么办？"
}
```

---

### 5. 多轮对话

**端点**: `POST /api/chat/`

**描述**: 支持多轮对话的智能问答

**请求参数**:
```json
{
    "conversation_history": [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "new_question": "新问题",
    "top_k": 3
}
```

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| conversation_history | array | 否 | [] | 对话历史 |
| new_question | string | 是 | - | 新问题 |
| top_k | integer | 否 | 3 | 引用案例数量 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/cases/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_history": [
        {"role": "user", "content": "我的系统出现了kernel panic"},
        {"role": "assistant", "content": "kernel panic是Linux内核的严重错误。请问您有具体的错误日志吗？"}
    ],
    "new_question": "日志显示是内存分配失败导致的",
    "top_k": 3
  }'
```

**响应示例**:
```json
{
    "success": true,
    "answer": "用户提到的内存分配失败...",
    "confidence": 0.7542,
    "cases": [...],
    "new_question": "日志显示是内存分配失败导致的"
}
```

---

### 6. 问题分析

**端点**: `POST /api/analyze/`

**描述**: 综合分析内核问题

**请求参数**:
```json
{
    "issue_description": "问题描述",
    "logs": "日志内容（可选）"
}
```

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| issue_description | string | 是 | - | 问题描述 |
| logs | string | 否 | null | 相关日志 |

**请求示例**:
```bash
curl -X POST http://localhost:8000/cases/api/analyze/ \
  -H "Content-Type: application/json" \
  -d '{
    "issue_description": "系统运行一段时间后出现kernel panic",
    "logs": "kernel: BUG: unable to handle kernel NULL pointer dereference"
  }'
```

**响应示例**:
```json
{
    "success": true,
    "analysis": {
        "issue_description": "系统运行一段时间后出现kernel panic",
        "relevant_skills_used": ["kernel_panic"],
        "confidence_score": 0.75,
        "similar_cases": [
            {
                "case_id": "TC_001",
                "title": "Linux内核问题分析报告",
                "similarity": 0.5214
            }
        ],
        "summary": "## Kernel Issue Analysis Summary\n..."
    }
}
```

---

## 🛠️ 错误响应

所有API在发生错误时返回统一格式：

```json
{
    "success": false,
    "error": "错误描述"
}
```

**常见错误码**:
- `400 Bad Request` - 请求参数错误
- `500 Internal Server Error` - 服务器内部错误

---

## 💻 CLI工具使用

### 安装
```bash
cd /home/lmr/project/issue_analysis_assist
chmod +x rag_cli.py
```

### 命令示例

#### 1. 检索相似案例
```bash
python rag_cli.py search "kernel panic 内存崩溃" --top-k 5 --threshold 0.5
```

#### 2. 推荐案例
```bash
python rag_cli.py recommend "系统出现内存泄漏问题" --top-k 5
```

#### 3. 智能问答
```bash
python rag_cli.py qa "如何排查内核死锁问题？" --output result.json
```

#### 4. 问题分析
```bash
python rag_cli.py analyze \
  --description "系统崩溃" \
  --logs "kernel panic log" \
  --output analysis.json
```

---

## 📊 性能指标

| API端点 | 平均响应时间 | 备注 |
|---------|-------------|------|
| 健康检查 | < 10ms | 无LLM调用 |
| 案例检索 | < 1秒 | 向量计算 |
| 案例推荐 | < 1秒 | 向量计算 |
| 智能问答 | 2-3秒 | 包含LLM推理 |
| 多轮对话 | 2-3秒 | 包含LLM推理 |
| 问题分析 | 2-3秒 | 包含LLM推理 |

---

## 🔧 开发指南

### 启动服务器
```bash
cd /home/lmr/project/issue_analysis_assist
python manage.py runserver
```

### 测试API
```bash
python test_rag_api.py
```

### 使用Python requests
```python
import requests

# 检索案例
response = requests.post(
    'http://localhost:8000/cases/api/search/',
    json={
        'query': 'kernel panic',
        'top_k': 5
    }
)
print(response.json())
```

---

## 📝 注意事项

1. **模型要求**: 确保Ollama服务正在运行，且已下载qwen2.5:0.5b模型
2. **数据要求**: 确保数据库中有训练案例数据（至少160个）
3. **性能优化**: 对于生产环境，建议添加缓存和认证机制
4. **并发限制**: 当前版本不支持高并发，建议添加任务队列

---

## 🚀 后续优化

1. **认证机制**: 添加API Key认证
2. **速率限制**: 实现请求频率限制
3. **缓存优化**: 添加Redis缓存
4. **异步处理**: 使用Celery处理长时间任务
5. **批量接口**: 支持批量查询
6. **WebSocket**: 支持实时对话

---

**版本**: 1.0  
**更新时间**: 2026-03-17