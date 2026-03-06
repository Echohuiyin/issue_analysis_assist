# Problem AI - Linux内核问题自动分析系统 测试设计文档

## 1. 测试策略

### 1.1 测试目标
- 验证四个模块功能满足需求规格
- 确保爬虫、数据存储、SKILL提取、问题分析各环节正确运作
- 保障系统性能符合预期
- 验证RAG检索和LLM分析的效果

### 1.2 测试类型

| 测试类型 | 占比 | 说明 |
|----------|------|------|
| 单元测试 | 40% | 各模块核心功能测试 |
| 集成测试 | 30% | 模块间交互测试 |
| 端到端测试 | 20% | 完整业务流程测试 |
| 性能测试 | 10% | 系统性能指标验证 |

### 1.3 测试环境

| 环境 | 用途 |
|------|------|
| 开发环境 | 本地开发调试 |
| 测试环境 | 功能测试、集成测试 |
| 预发布环境 | 性能测试、最终验收 |

---

## 2. 测试范围

### 2.1 模块一：案例获取模块（爬虫系统）

#### 2.1.1 爬虫功能测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| Stack Overflow爬虫 | 搜索问题、解析详情 | P0 |
| CSDN爬虫 | 搜索文章、解析内容 | P1 |
| 知乎爬虫 | 搜索问答、解析回答 | P2 |
| 多源爬取 | 同时爬取多个数据源 | P2 |

#### 2.1.2 内容处理测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| HTML解析 | 正确提取标题、内容、答案 | P0 |
| 代码块提取 | 保留代码格式 | P1 |
| 内容清洗 | 去除广告、噪音 | P1 |
| 去重检测 | 基于哈希去重 | P0 |

#### 2.1.3 爬虫调度测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| 任务添加 | 正确创建爬取任务 | P0 |
| 任务执行 | 正确执行爬取 | P0 |
| 增量爬取 | 只获取新内容 | P1 |
| 异常处理 | 网络异常处理 | P1 |

### 2.2 模块二：数据存储系统

#### 2.2.1 PostgreSQL测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| 案例CRUD | 创建、读取、更新、删除 | P0 |
| 案例查询 | 按模块、标签、时间筛选 | P0 |
| 向量存储 | 正确存储向量 | P0 |
| 索引性能 | 查询性能 | P1 |

#### 2.2.2 RAG向量库测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| 向量生成 | 正确生成embedding | P0 |
| 向量索引 | 正确建立索引 | P0 |
| 相似检索 | 返回相似案例 | P0 |
| Top-K检索 | 返回指定数量 | P1 |
| 模块过滤 | 按模块筛选 | P1 |

### 2.3 模块三：SKILL提取模块

#### 2.3.1 提取功能测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| 模块SKILL提取 | 按模块提取技能 | P0 |
| 总SKILL生成 | 整合生成总技能 | P0 |
| 案例分析 | 分析案例提取要点 | P0 |
| LLM提炼 | 调用LLM提炼SKILL | P1 |

#### 2.3.2 版本管理测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| 版本创建 | 创建新版本 | P0 |
| 版本获取 | 获取指定版本 | P0 |
| 版本列表 | 列出所有版本 | P1 |
| 版本回滚 | 回滚到指定版本 | P2 |

### 2.4 模块四：问题分析模块

#### 2.4.1 分析功能测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| 模块判断 | 判断问题所属模块 | P0 |
| RAG检索 | 检索相似案例 | P0 |
| SKILL加载 | 加载对应模块SKILL | P0 |
| LLM分析 | 调用LLM分析 | P0 |
| 结果解析 | 解析LLM输出 | P0 |

#### 2.4.2 完整流程测试
| 测试项 | 测试内容 | 优先级 |
|--------|----------|--------|
| 端到端分析 | 完整分析流程 | P0 |
| 多种输入 | 文本、日志、混合 | P0 |
| 结果验证 | 根因、方案完整性 | P1 |

---

## 3. 测试用例设计

### 3.1 爬虫系统测试用例

#### 3.1.1 Stack Overflow爬虫测试
```python
class TestStackOverflowSpider:
    @pytest.mark.asyncio
    async def test_search_questions(self):
        """测试搜索问题功能"""
        # 输入: 关键词"linux kernel panic"
        # 预期: 返回问题列表，包含id、title、votes
        
    @pytest.mark.asyncio
    async def test_parse_question_detail(self):
        """测试问题详情解析"""
        # 输入: 问题ID
        # 预期: 返回问题正文、答案列表、标签
        
    @pytest.mark.asyncio
    async def test_convert_to_case(self):
        """测试转换为案例格式"""
        # 输入: 问题详情
        # 预期: 返回标准案例格式
        
    @pytest.mark.asyncio
    async def test_filter_by_keywords(self):
        """测试关键词过滤"""
        # 输入: 包含linux内核关键词的内容
        # 预期: 返回True
        
    @pytest.mark.asyncio
    async def test_filter_out_irrelevant(self):
        """测试过滤不相关内容"""
        # 输入: 不相关的内容
        # 预期: 返回False
```

#### 3.1.2 内容清洗测试
```python
class TestContentCleaner:
    def test_clean_html(self):
        """测试HTML清洗"""
        # 输入: 包含HTML标签的内容
        # 预期: 清除标签，保留文本
        
    def test_extract_code_blocks(self):
        """测试代码块提取"""
        # 输入: 包含<pre><code>的HTML
        # 预期: 提取代码块内容
        
    def test_remove_noise(self):
        """测试噪音去除"""
        # 输入: 包含广告、水印的内容
        # 预期: 清除噪音内容
        
    def test_normalize_whitespace(self):
        """测试空白字符规范化"""
        # 输入: 包含多余空白的文本
        # 预期: 规范化空白
```

#### 3.1.3 去重测试
```python
class TestDeduplicator:
    async def test_compute_hash(self):
        """测试哈希计算"""
        # 输入: 文本内容
        # 预期: 返回哈希值
        
    async def test_detect_duplicate(self):
        """测试重复检测"""
        # 输入: 已存在的内容哈希
        # 预期: 返回True
        
    async def test_new_content(self):
        """测试新内容"""
        # 输入: 新内容
        # 预期: 返回False
```

### 3.2 数据存储系统测试用例

#### 3.2.1 案例CRUD测试
```python
class TestCaseService:
    async def test_create_case(self):
        """测试创建案例"""
        # 创建案例
        # 验证数据库记录
        
    async def test_get_case(self):
        """测试获取案例"""
        # 输入: 案例ID
        # 预期: 返回案例详情
        
    async def test_list_cases_by_module(self):
        """测试按模块查询"""
        # 输入: module="memory"
        # 预期: 返回memory模块案例
        
    async def test_update_case(self):
        """测试更新案例"""
        # 更新案例字段
        # 验证更新结果
        
    async def test_delete_case(self):
        """测试删除案例"""
        # 删除案例
        # 验证已删除
```

#### 3.2.2 向量检索测试
```python
class TestVectorService:
    async def test_create_embedding(self):
        """测试向量生成"""
        # 输入: 文本
        # 预期: 返回向量列表
        
    async def test_index_case(self):
        """测试案例索引"""
        # 索引新案例
        # 验证向量库记录
        
    async def test_search_similar(self):
        """测试相似检索"""
        # 输入: 查询文本
        # 预期: 返回相似案例列表
        
    async def test_search_with_module_filter(self):
        """测试带模块过滤的检索"""
        # 输入: 查询 + module
        # 预期: 只返回指定模块案例
```

### 3.3 SKILL提取测试用例

#### 3.3.1 提取器测试
```python
class TestSkillExtractor:
    async def test_extract_memory_skill(self):
        """测试memory模块SKILL提取"""
        # 输入: memory模块案例列表
        # 预期: 返回包含分析方法的SKILL
        
    async def test_extract_network_skill(self):
        """测试network模块SKILL提取"""
        # 输入: network模块案例列表
        # 预期: 返回网络相关技能
        
    async def test_extract_total_skill(self):
        """测试总SKILL生成"""
        # 输入: 各模块SKILL
        # 预期: 返回整合后的总SKILL
```

#### 3.3.2 版本管理测试
```python
class TestSkillVersionManager:
    async def test_create_version(self):
        """测试"""
        # 创建创建版本新版本
        # 验证版本号递增
        
    async def test_get_latest_version(self):
        """测试获取最新版本"""
        # 获取最新版本
        # 验证版本号正确
        
    async def test_rollback(self):
        """测试版本回滚"""
        # 回滚到指定版本
        # 验证数据正确
```

### 3.4 问题分析测试用例

#### 3.4.1 模块判断测试
```python
class TestModuleDetermination:
    async def test_determine_memory_module(self):
        """测试内存模块判断"""
        # 输入: "系统内存泄漏，OOM"
        # 预期: module="memory"
        
    async def test_determine_network_module(self):
        """测试网络模块判断"""
        # 输入: "TCP连接超时"
        # 预期: module="network"
        
    async def test_determine_lock_module(self):
        """测试锁模块判断"""
        # 输入: "进程死锁"
        # 预期: module="lock"
```

#### 3.4.2 完整分析流程测试
```python
class TestAnalysisFlow:
    async def test_full_analysis_flow(self):
        """测试完整分析流程"""
        # 1. 提交问题
        # 2. 判断模块
        # 3. RAG检索
        # 4. 加载SKILL
        # 5. LLM分析
        # 6. 验证返回结果
        
    async def test_analysis_with_log(self):
        """测试带日志的分析"""
        # 输入: 问题描述 + dmesg日志
        # 预期: 分析结果包含日志分析
        
    async def test_analysis_result_structure(self):
        """测试结果结构"""
        # 验证结果包含: 分类、根因、影响、方案、参考案例
```

### 3.5 集成测试用例

#### 3.5.1 爬取到分析完整流程
```python
class TestEndToEndFlow:
    async def test_crawl_to_analyze(self):
        """端到端测试: 爬取到分析"""
        # 1. 启动爬虫
        # 2. 等待案例入库
        # 3. 触发SKILL提取
        # 4. 提交问题分析
        # 5. 验证分析结果
```

---

## 4. 性能测试设计

### 4.1 性能测试指标

| 指标 | 目标值 | 阈值 |
|------|--------|------|
| 爬虫吞吐量 | >= 50案例/小时 | >= 20案例/小时 |
| 案例入库速度 | >= 30案例/分钟 | >= 10案例/分钟 |
| RAG检索延迟 | < 1秒 | < 2秒 |
| SKILL提取速度 | < 60秒/模块 | < 120秒/模块 |
| 问题分析响应 | < 30秒 | < 60秒 |

### 4.2 性能测试场景

#### 4.2.1 爬虫性能测试
```python
class TestCrawlerPerformance:
    async def test_concurrent_crawl(self):
        """测试并发爬取"""
        # 10个并发爬取任务
        # 验证吞吐量
        
    async def test_large_scale_crawl(self):
        """测试大规模爬取"""
        # 爬取1000个案例
        # 验证完成时间
```

#### 4.2.2 RAG性能测试
```python
class TestRAGPerformance:
    async def test_search_latency(self):
        """测试检索延迟"""
        # 100次检索请求
        # 验证P99延迟
        
    async def test_large_dataset_search(self):
        """测试大数据集检索"""
        # 10000条案例向量
        # 验证检索准确性
```

#### 4.2.3 分析性能测试
```python
class TestAnalysisPerformance:
    async def test_concurrent_analysis(self):
        """测试并发分析"""
        # 5个并发分析请求
        # 验证响应时间
```

---

## 5. 效果评估测试

### 5.1 RAG效果评估

| 指标 | 计算方式 | 目标值 |
|------|----------|--------|
| 召回率 | 检索结果与相关案例的比例 | >= 80% |
| 精确率 | 返回案例中实际相关的比例 | >= 70% |
| MRR | 平均倒数排名 | >= 0.8 |

```python
class TestRAGEffectiveness:
    async def test_recall_rate(self):
        """测试召回率"""
        # 准备测试集
        # 执行检索
        # 计算召回率
        
    async def test_precision_rate(self):
        """测试精确率"""
        # 准备测试集
        # 执行检索
        # 计算精确率
```

### 5.2 LLM分析效果评估

| 指标 | 说明 | 目标值 |
|------|------|--------|
| 模块判断准确率 | 正确判断问题模块 | >= 85% |
| 根因分析准确率 | 根因分析正确性(人工评估) | >= 80% |
| 解决方案有效率 | 方案可执行且有效(人工评估) | >= 75% |

```python
class TestLLMAnalysisEffectiveness:
    async def test_module_classification_accuracy(self):
        """测试模块分类准确率"""
        # 准备标注数据集
        # 执行分析
        # 对比结果计算准确率
        
    async def test_root_cause_quality(self):
        """测试根因分析质量"""
        # 人工评估分析结果
        # 统计质量评分
```

### 5.3 SKILL效果评估

| 指标 | 说明 | 目标值 |
|------|------|--------|
| SKILL覆盖率 | 覆盖的内核模块 | >= 8个模块 |
| 技能完整性 | 每个模块的技能字段完整度 | >= 90% |
| 更新及时性 | 新案例入库到SKILL更新的时间 | <= 24小时 |

---

## 6. 安全测试设计

### 6.1 安全测试用例

| 测试项 | 测试内容 | 预期结果 |
|--------|----------|----------|
| SQL注入 | 输入特殊SQL字符 | 被拦截或安全处理 |
| XSS攻击 | 输入脚本标签 | 被转义或拦截 |
| 未授权访问 | 直接访问API | 返回401 |
| 爬虫限制 | 超过频率限制 | 请求被限流 |
| LLM注入 | 恶意提示词注入 | 被过滤 |

---

## 7. 测试数据管理

### 7.1 测试数据集

#### 7.1.1 案例测试数据
| 类型 | 描述 | 数量 |
|------|------|------|
| 正常案例 | 完整的Linux内核问题案例 | 100条 |
| 边界案例 | 部分字段缺失的案例 | 20条 |
| 异常案例 | 格式错误、无内容 | 10条 |

#### 7.1.2 问题测试数据
| 类型 | 描述 |
|------|------|
| memory类型 | 内存泄漏、OOM等问题描述+日志 |
| network类型 | 网络超时、连接失败等问题 |
| scheduler类型 | 进程调度、实时性等问题 |
| lock类型 | 死锁、锁竞争等问题 |

### 7.2 Mock数据
```python
# 测试用的Mock LLM响应
MOCK_LLM_RESPONSE = {
    "module": "memory",
    "classification": "内存泄漏",
    "root_cause": "kmalloc未释放导致内存泄漏",
    "impact": "长期运行可能导致OOM",
    "solution": "使用kmemleak定位泄漏点并修复"
}
```

---

## 8. 测试执行计划

### 8.1 测试阶段

| 阶段 | 时间 | 内容 |
|------|------|------|
| 单元测试 | 开发过程中 | 各模块单元测试 |
| 集成测试 | 每周 | 模块集成测试 |
| 效果评估 | 模块完成后 | RAG和LLM效果评估 |
| 系统测试 | Sprint结束 | 完整系统测试 |
| 验收测试 | 上线前 | 用户验收测试 |

### 8.2 测试工具

| 工具 | 用途 |
|------|------|
| pytest | Python单元测试 |
| pytest-asyncio | 异步测试 |
| pytest-cov | 代码覆盖率 |
| Locust | 性能测试 |
| httpx | API测试 |

### 8.3 通过标准

| 指标 | 标准 |
|------|------|
| 代码覆盖率 | >= 60% |
| 单元测试通过率 | 100% |
| 集成测试通过率 | 100% |
| 模块判断准确率 | >= 85% |
| RAG检索召回率 | >= 80% |
| 性能测试达标 | 全部指标达标 |

---

## 9. 缺陷管理

### 9.1 缺陷等级

| 等级 | 定义 | 处理时限 |
|------|------|----------|
| P0 | 系统崩溃、爬虫完全失效 | 立即修复 |
| P1 | 核心功能失效（分析、检索） | 24小时内 |
| P2 | 次要功能问题 | 3天内 |
| P3 | 效果不佳、优化项 | 下个版本 |

### 9.2 缺陷报告模板

```
缺陷ID: 
标题: 
模块: 
严重等级: 
优先级: 
复现步骤: 
预期结果: 
实际结果: 
日志/截图: 
影响评估: 
```
