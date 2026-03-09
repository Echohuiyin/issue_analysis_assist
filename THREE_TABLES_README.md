# 三表结构说明

## 数据库设计

本系统采用三表结构来管理内核案例数据：

### 1. RawCase（原始案例表）
存储从各数据源获取的原始内容。

**字段说明：**
- `raw_id`: 原始案例ID（主键）
- `source`: 数据源（stackoverflow, csdn, zhihu, juejin）
- `source_id`: 源网站的文章/问题ID
- `url`: 原始URL
- `raw_title`: 原始标题
- `raw_content`: 原始内容（纯文本）
- `raw_html`: 原始HTML内容
- `fetch_time`: 获取时间
- `status`: 处理状态（pending, processing, processed, failed, low_quality）
- `process_time`: 处理时间
- `process_error`: 处理错误信息
- `content_hash`: 内容哈希（用于去重）

**状态流转：**
```
pending → processing → processed
                    → low_quality
                    → failed
```

### 2. TrainingCase（训练数据表）
存储高质量的结构化案例，用于训练。

**字段说明：**
- `case_id`: 案例ID（唯一）
- `raw_case`: 关联的原始案例（外键）
- `title`: 标题
- `phenomenon`: 问题现象
- `key_logs`: 关键日志
- `environment`: 环境信息
- `root_cause`: 根本原因
- `analysis_process`: 分析过程
- `troubleshooting_steps`: 排查步骤（JSON数组）
- `solution`: 解决方案
- `prevention`: 预防措施
- `kernel_version`: 内核版本
- `affected_components`: 受影响组件
- `module`: 内核模块分类
- `severity`: 严重程度
- `source`: 数据源
- `source_id`: 源ID
- `url`: 原始URL
- `tags`: 标签（JSON数组）
- `votes`: 投票数
- `answers_count`: 回答数
- `quality_score`: 质量分数（0-100）
- `confidence`: 置信度（0-1）
- `embedding`: 向量嵌入（用于RAG）
- `content_hash`: 内容哈希
- `created_date`: 创建时间
- `updated_date`: 更新时间

### 3. TestCase（测试数据表）
存储高质量的结构化案例，用于测试。字段与TrainingCase完全相同。

## 工作流程

### 步骤1: 获取原始案例

使用 `fetch_raw_cases.py` 从各数据源获取原始案例：

```bash
# 基本用法：获取10个案例
python3 fetch_raw_cases.py --count 10

# 指定数据源
python3 fetch_raw_cases.py --count 10 --sources stackoverflow csdn

# 指定关键词
python3 fetch_raw_cases.py --keywords "kernel panic" "kernel oops" --count 5

# 持续运行（每30分钟一轮）
python3 fetch_raw_cases.py --continuous --interval 30
```

**延迟机制：**
- 正常请求延迟：2-5秒（随机）
- 批次间延迟：10秒
- 切换数据源延迟：30秒
- CSDN特殊延迟：3-6秒（更严格）

### 步骤2: 处理原始案例

使用 `process_raw_cases.py` 处理原始案例：

```bash
# 处理一批（10个）
python3 process_raw_cases.py --batch-size 10

# 处理所有待处理案例
python3 process_raw_cases.py --all

# 指定LLM模型
python3 process_raw_cases.py --llm-type ollama --model qwen:1.8b
```

**处理流程：**
1. 从RawCase表读取status='pending'的案例
2. 使用本地LLM解析成结构化格式
3. 验证质量分数（阈值：70分）
4. 生成向量嵌入
5. 随机分配到训练集（80%）或测试集（20%）
6. 保存到TrainingCase或TestCase表

### 步骤3: 查看结果

```bash
# 查看统计信息
python3 test_three_tables.py

# Django管理界面
python3 manage.py createsuperuser
python3 manage.py runserver
# 访问 http://localhost:8000/admin/
```

## 质量控制

### 质量评分标准

**高质量案例标准：**
1. 问题现象描述清晰准确（包含具体症状、错误信息）
2. 有描述问题现象的关键日志提供
3. 提供了问题分析思路或较为详细的问题分析过程

**评分维度：**
- 标题（10%）
- 问题现象（25%）
- 关键日志（20%）
- 分析过程（20%）
- 根本原因（15%）
- 解决方案（10%）

**阈值设置：**
- 最低质量分数：70分
- 最低置信度：0.7

## 数据统计

查看当前数据统计：

```python
from cases.models import RawCase, TrainingCase, TestCase

# 原始案例统计
print(f"原始案例总数: {RawCase.objects.count()}")
print(f"待处理: {RawCase.objects.filter(status='pending').count()}")
print(f"已处理: {RawCase.objects.filter(status='processed').count()}")
print(f"低质量: {RawCase.objects.filter(status='low_quality').count()}")
print(f"失败: {RawCase.objects.filter(status='failed').count()}")

# 训练/测试数据统计
print(f"训练案例: {TrainingCase.objects.count()}")
print(f"测试案例: {TestCase.objects.count()}")
```

## 配置说明

### 延迟配置（fetch_raw_cases.py）

```python
DELAY_CONFIG = {
    'min_delay': 2,      # 最小延迟（秒）
    'max_delay': 5,      # 最大延迟（秒）
    'batch_delay': 10,   # 批次间延迟（秒）
    'source_delay': 30,  # 切换数据源延迟（秒）
}
```

### 质量阈值配置（process_raw_cases.py）

```python
QUALITY_THRESHOLD = 70.0      # 最低质量分数
CONFIDENCE_THRESHOLD = 0.7     # 最低置信度
TRAINING_RATIO = 0.8           # 训练集比例（80%）
```

## 最佳实践

1. **分批获取**：建议每次获取10-20个案例，避免被网站拒绝访问
2. **持续运行**：使用`--continuous`参数持续获取，设置合理的间隔时间
3. **质量优先**：宁可少获取高质量案例，不要大量获取低质量案例
4. **定期清理**：定期清理失败的原始案例，重新处理
5. **监控统计**：定期查看统计信息，了解数据质量

## 故障排查

### 问题1: 获取案例失败
- 检查网络连接
- 增加延迟时间
- 更换数据源

### 问题2: LLM处理超时
- 增加超时时间（vector_service.py中的timeout参数）
- 使用更快的模型（如qwen:0.5b）
- 减少批处理大小

### 问题3: 质量分数过低
- 检查原始内容质量
- 优化LLM提示词
- 调整质量阈值

## 文件说明

- `cases/models.py` - 数据模型定义
- `cases/admin.py` - Django管理界面配置
- `fetch_raw_cases.py` - 原始案例获取程序
- `process_raw_cases.py` - 原始案例处理程序
- `test_three_tables.py` - 测试脚本