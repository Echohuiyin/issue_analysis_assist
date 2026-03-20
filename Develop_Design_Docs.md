# Problem AI - Linux内核问题自动分析系统 开发设计文档

## 0. 当前实现对齐说明（2026-03）

本文件包含目标态架构设计（微服务/FastAPI/Chroma 等）。当前仓库可运行实现采用 Django 单体形态，并按优先级先完成第一/第二部分闭环。请以以下边界作为当前代码事实：

- 当前优先级：
  - P0：案例获取与解析（Part 1）
  - P0：案例存储与向量化（Part 2）
  - P1：SKILL训练与自动分析（Part 3/4，接口保留，暂不实现）
- 当前默认数据库：SQLite（`USE_POSTGRES=0`）；PostgreSQL 为可选后置路径。
- 当前向量方案：本地轻量向量存储（JSON 持久化）+ 余弦检索。
- 当前采集编排链路：`fetch -> parse -> clean -> classify -> validate -> store`。

### 0.1 第三/四部分接口保留策略

- `cases/analysis/interfaces.py` 提供 `SKILLStorage` / `SKILLTrainer` / `IssueAnalyzer` 占位类。
- `cases/analysis/__init__.py` 仅导出占位接口，运行时抛出 `NotImplementedError`。
- 旧实现文件与对应测试已清理，避免误导当前交付范围。

## 1. 系统架构设计

### 1.1 整体架构
采用微服务架构，各模块独立运行，通过API交互。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Web 前端 (Vue.js)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                API 网关 (FastAPI)                            │
├──────────────┬──────────────┬──────────────┬──────────────────────────────┤
│  案例获取模块  │   数据存储    │  SKILL提取    │     问题分析模块             │
│   (爬虫服务)   │    服务       │    服务       │      (LLM分析)              │
├──────────────┼──────────────┼──────────────┼──────────────────────────────┤
│  • 爬虫调度器  │  • PostgreSQL │  • SKILL生成  │  • RAG检索                   │
│  • 网页解析器  │  • 向量数据库  │  • 技能存储   │  • SKILL加载                 │
│  • 数据清洗器  │  • 缓存服务   │  • 版本管理   │  • LLM调用                   │
└──────────────┴──────────────┴──────────────┴──────────────────────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
   技术社区网站       PostgreSQL          本地代码仓库
                     + Chroma/Milvus
```

### 1.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | FastAPI | 高性能异步API框架 |
| 爬虫框架 | Playwright + Scrapy | 网页解析和数据采集 |
| 数据库 | PostgreSQL 15 | 案例和元数据存储 |
| 向量库 | ChromaDB | 轻量级向量数据库 |
| LLM | OpenAI API / 本地模型 | 问题分析 |
| Embedding | OpenAI text-embedding-3-small | 文本向量化 |
| 前端 | Vue 3 + Element Plus | UI框架 |
| 任务队列 | Celery + Redis | 异步任务处理 |
| 部署 | Docker + Docker Compose | 容器化部署 |

### 1.3 目录结构

```
problem-ai/
├── api/                          # 后端API服务
│   ├── app/
│   │   ├── api/                  # API路由
│   │   │   ├── v1/
│   │   │   │   ├── cases.py      # 案例管理
│   │   │   │   ├── skill.py      # SKILL管理
│   │   │   │   ├── analyze.py    # 问题分析
│   │   │   │   └── crawl.py      # 爬虫控制
│   │   │   └── deps.py           # 依赖注入
│   │   ├── core/                 # 核心配置
│   │   │   ├── config.py         # 配置管理
│   │   │   ├── database.py       # 数据库连接
│   │   │   └── security.py       # 安全工具
│   │   ├── models/               # 数据模型
│   │   │   ├── sqlmodels.py      # SQLAlchemy模型
│   │   │   └── schemas.py        # Pydantic模型
│   │   ├── services/             # 业务服务
│   │   │   ├── case_service.py   # 案例服务
│   │   │   ├── skill_service.py  # SKILL服务
│   │   │   ├── rag_service.py     # RAG服务
│   │   │   └── analyze_service.py # 分析服务
│   │   └── utils/                # 工具函数
│   ├── requirements.txt
│   └── Dockerfile
├── crawler/                      # 爬虫服务
│   ├── spiders/
│   │   ├── stackoverflow.py     # Stack Overflow爬虫
│   │   ├── csdn.py               # CSDN爬虫
│   │   └── zhihu.py              # 知乎爬虫
│   ├── parsers/
│   │   ├── html_parser.py        # HTML解析
│   │   └── content_cleaner.py    # 内容清洗
│   ├── scheduler/
│   │   └── task_scheduler.py     # 爬虫调度
│   ├── requirements.txt
│   └── Dockerfile
├── skill_extractor/              # SKILL提取服务
│   ├── extractor.py              # 提取器
│   ├── skill_template.py         # 技能模板
│   ├── requirements.txt
│   └── Dockerfile
├── web/                          # 前端应用
│   ├── src/
│   │   ├── views/               # 页面视图
│   │   ├── components/           # 组件
│   │   ├── api/                 # API调用
│   │   └── stores/               # 状态管理
│   ├── package.json
│   └── Dockerfile
├── vector_db/                    # 向量数据库配置
├── data/                         # 本地数据
│   └── kernel_code/             # Linux内核代码仓库
├── docker-compose.yml
└── README.md
```

---

## 2. 模块一：案例获取模块（爬虫系统）

### 2.1 模块职责
负责从技术社区网站自动爬取Linux内核相关问题案例，包括网页抓取、内容解析、数据清洗和质量过滤。

### 2.2 核心组件设计

#### 2.2.1 爬虫调度器 (CrawlScheduler)
```python
class CrawlScheduler:
    """爬虫任务调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, CrawlTask] = {}
        self.lock = asyncio.Lock()
    
    async def add_task(self, source: str, config: CrawlConfig) -> str:
        """添加爬取任务"""
        # 生成任务ID
        # 配置爬取参数
        # 加入调度队列
    
    async def execute_task(self, task_id: str) -> CrawlResult:
        """执行爬取任务"""
        # 获取任务配置
        # 调度对应爬虫
        # 采集数据
        # 清洗和去重
        # 返回结果
    
    async def schedule_periodic(self, source: str, interval: int):
        """定时执行爬取"""
```

#### 2.2.2 基础爬虫 (BaseSpider)
```python
class BaseSpider(ABC):
    """爬虫基类"""
    
    source_name: str = ""
    base_url: str = ""
    
    async def fetch_page(self, url: str) -> str:
        """获取页面内容"""
    
    async def parse_list(self, html: str) -> List[CaseInfo]:
        """解析列表页"""
    
    async def parse_detail(self, html: str) -> CaseDetail:
        """解析详情页"""
    
    async def extract_cases(self) -> List[RawCase]:
        """提取案例"""
    
    async def filter_by_keywords(self, case: RawCase) -> bool:
        """关键词过滤"""
```

#### 2.2.3 Stack Overflow爬虫
```python
class StackOverflowSpider(BaseSpider):
    """Stack Overflow爬虫"""
    
    source_name = "stackoverflow"
    base_url = "https://stackoverflow.com"
    
    # 搜索关键词配置
    SEARCH_KEYWORDS = [
        "linux kernel",
        "kernel panic",
        "linux memory",
        "kernel deadlock",
        "linux scheduler",
        "kernel network",
        "spinlock",
        "linux interrupt"
    ]
    
    async def search_questions(self, keyword: str, page: int = 1) -> List[QuestionInfo]:
        """搜索问题"""
        # 调用Stack Overflow API或解析搜索页
        # 返回问题基本信息
    
    async def get_question_detail(self, question_id: str) -> QuestionDetail:
        """获取问题详情"""
        # 获取问题正文、答案、评论
        # 提取代码片段
    
    async def parse_to_case(self, detail: QuestionDetail) -> CaseDetail:
        """转换为案例格式"""
        # 提取问题描述
        # 提取答案中的解决方案
        # 分类到内核模块
```

#### 2.2.4 CSDN爬虫
```python
class CSDNSpider(BaseSpider):
    """CSDN爬虫"""
    
    source_name = "csdn"
    base_url = "https://blog.csdn.net"
    
    async def search_articles(self, keyword: str, page: int = 1) -> List[ArticleInfo]:
        """搜索文章"""
    
    async def get_article_detail(self, article_id: str) -> ArticleDetail:
        """获取文章详情"""
        # 解析文章内容
        # 提取代码块
        # 解析评论中的问答
```

#### 2.2.5 内容清洗器 (ContentCleaner)
```python
class ContentCleaner:
    """内容清洗器"""
    
    def clean_html(self, html: str) -> str:
        """清除HTML标签"""
        # 使用BeautifulSoup解析
        # 保留代码块
        # 清除脚本和样式
    
    def remove_noise(self, text: str) -> str:
        """去除噪音内容"""
        # 去除广告
        # 去除水印
        # 去除无关链接
    
    def extract_code_blocks(self, html: str) -> List[str]:
        """提取代码块"""
        # 识别<pre><code>标签
        # 保留代码格式
    
    def normalize_whitespace(self, text: str) -> str:
        """规范化空白字符"""
```

#### 2.2.6 去重处理器 (Deduplicator)
```python
class Deduplicator:
    """去重处理器"""
    
    async def compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        # 使用MD5或SHA256
    
    async def is_duplicate(self, content_hash: str) -> bool:
        """检查是否重复"""
        # 查询数据库
    
    async def add_to_set(self, content_hash: str):
        """添加到去重集合"""
```

### 2.3 数据模型

#### 2.3.1 原始案例模型
```python
class RawCase(BaseModel):
    """原始案例"""
    source: str
    source_id: str
    url: str
    title: str
    content: str
    answers: List[str]
    tags: List[str]
    votes: int
    created_at: datetime
    crawled_at: datetime
```

#### 2.3.2 处理后案例模型
```python
class ProcessedCase(BaseModel):
    """处理后案例"""
    id: UUID
    source: str
    source_id: str
    title: str
    problem_description: str      # 问题描述
    problem_analysis: str         # 问题分析思路和过程
    conclusion: str               # 问题分析结论
    solution: str                  # 解决方案
    module: str                    # 所属内核模块
    tags: List[str]
    votes: int
    answers_count: int
    created_at: datetime
    crawled_at: datetime
    embedding: List[float]         # 向量特征
```

### 2.4 API接口设计

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/v1/crawl/start | POST | 启动爬取任务 |
| /api/v1/crawl/stop | POST | 停止爬取任务 |
| /api/v1/crawl/status | GET | 获取爬取状态 |
| /api/v1/crawl/config | PUT | 更新爬取配置 |

### 2.5 爬取流程

```
1. 调度器启动
     │
     ▼
2. 获取搜索关键词列表
     │
     ▼
3. 遍历关键词搜索
     │
     ├── 搜索页面获取
     │
     ▼
4. 解析列表页获取问题ID
     │
     ▼
5. 遍历问题ID获取详情
     │
     ├── 获取问题内容
     ├── 获取答案内容
     │
     ▼
6. 内容清洗和去重
     │
     ▼
7. 转换为标准案例格式
     │
     ▼
8. 分类到内核模块
     │
     ▼
9. 生成向量特征
     │
     ▼
10. 存储到数据库和向量库
```

---

## 3. 模块二：数据存储系统

### 3.1 模块职责
负责存储案例数据、管理向量库，为其他模块提供数据服务。

### 3.2 三表结构设计（V3.0 已实现）

#### 3.2.0 三表架构概述

系统采用三表分离架构，将原始数据、训练数据、测试数据分开存储，实现数据流程的清晰管理。

**架构图**：
```
┌─────────────────────────────────────────────────────────────────┐
│                        数据获取层                                │
│  StackOverflow / CSDN / 知乎 / 掘金                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │ fetch_raw_cases.py
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RawCase 表（原始案例表）                       │
│  • 存储原始内容（标题、HTML、纯文本）                             │
│  • 状态管理：pending → processing → processed/failed/low_quality │
│  • 去重机制：content_hash                                        │
│  • 当前数据：76条                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ process_raw_cases.py (LLM处理)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    质量评估与验证                                 │
│  • 质量分数 ≥ 70                                                 │
│  • 置信度 ≥ 0.7                                                  │
│  • 必填字段完整性检查                                            │
└──────────────┬──────────────────────────┬───────────────────────┘
               │ 80%                      │ 20%
               ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────┐
│   TrainingCase 表        │   │   TestCase 表            │
│   （训练数据表）          │   │   （测试数据表）          │
│  • 结构化案例数据         │   │  • 结构化案例数据         │
│  • 向量嵌入               │   │  • 向量嵌入               │
│  • 质量评分               │   │  • 质量评分               │
│  • 用于SKILL训练          │   │  • 用于系统测试           │
└──────────────────────────┘   └──────────────────────────┘
```

**实现文件**：
- `cases/models.py` - 三表模型定义
- `fetch_raw_cases.py` - 原始案例获取程序
- `process_raw_cases.py` - 案例处理程序
- `test_three_tables.py` - 测试脚本

**数据流程**：
1. **获取阶段**：从多个数据源获取原始内容，存储到RawCase表
2. **处理阶段**：使用LLM解析原始内容，生成结构化数据
3. **验证阶段**：评估案例质量，过滤低质量案例
4. **分配阶段**：80%分配到TrainingCase，20%分配到TestCase

**关键特性**：
- ✅ 支持多数据源（StackOverflow、CSDN、知乎、掘金）
- ✅ 智能延迟避免被封禁
- ✅ HTML解析和内容提取
- ✅ 去重机制
- ✅ 质量评估
- ✅ 自动训练/测试集划分
- ✅ 向量嵌入生成

#### 3.2.1 RawCase表（原始案例表）- Django实现

```python
class RawCase(models.Model):
    """原始案例表 - 存储从各数据源获取的原始内容"""
    
    SOURCE_CHOICES = [
        ('stackoverflow', 'StackOverflow'),
        ('csdn', 'CSDN'),
        ('zhihu', '知乎'),
        ('juejin', '掘金'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('processed', '已处理'),
        ('failed', '处理失败'),
        ('low_quality', '质量不合格'),
    ]
    
    raw_id = models.AutoField(primary_key=True, verbose_name='原始案例ID')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, verbose_name='数据源')
    source_id = models.CharField(max_length=100, verbose_name='源ID', blank=True, default='')
    url = models.URLField(verbose_name='原始URL', max_length=500, blank=True, default='')
    
    raw_title = models.CharField(max_length=500, verbose_name='原始标题', blank=True, default='')
    raw_content = models.TextField(verbose_name='原始内容')
    raw_html = models.TextField(verbose_name='原始HTML', blank=True, default='')
    
    fetch_time = models.DateTimeField(default=timezone.now, verbose_name='获取时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='处理状态')
    process_time = models.DateTimeField(verbose_name='处理时间', null=True, blank=True)
    process_error = models.TextField(verbose_name='处理错误信息', blank=True, default='')
    
    content_hash = models.CharField(max_length=64, verbose_name='内容哈希', unique=True, db_index=True)
    
    class Meta:
        db_table = 'cases_rawcase'
        verbose_name = '原始案例'
        verbose_name_plural = '原始案例'
        indexes = [
            models.Index(fields=['source', 'status']),
            models.Index(fields=['status']),
        ]
```

#### 3.2.2 TrainingCase表（训练数据表）- Django实现

```python
class TrainingCase(models.Model):
    """训练数据表 - 存储高质量的结构化案例"""
    
    case_id = models.CharField(max_length=50, primary_key=True, verbose_name='案例ID')
    raw_case = models.ForeignKey(RawCase, on_delete=models.SET_NULL, null=True, blank=True, 
                                  verbose_name='原始案例', related_name='training_cases')
    
    title = models.CharField(max_length=200, verbose_name='案例标题')
    phenomenon = models.TextField(verbose_name='问题现象')
    logs = models.TextField(verbose_name='相关日志', blank=True, default='')
    environment = models.TextField(verbose_name='环境信息', blank=True, default='')
    root_cause = models.TextField(verbose_name='根本原因')
    analysis_process = models.TextField(verbose_name='分析过程', blank=True, default='')
    solution = models.TextField(verbose_name='解决方案')
    prevention = models.TextField(verbose_name='预防措施', blank=True, default='')
    
    kernel_module = models.CharField(max_length=50, verbose_name='内核模块', blank=True, default='')
    severity = models.CharField(max_length=20, verbose_name='严重程度', blank=True, default='')
    
    quality_score = models.FloatField(verbose_name='质量分数', default=0.0)
    confidence = models.FloatField(verbose_name='置信度', default=0.0)
    embedding = models.BinaryField(verbose_name='向量嵌入', null=True, blank=True)
    
    created_date = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'cases_trainingcase'
        verbose_name = '训练案例'
        verbose_name_plural = '训练案例'
        indexes = [
            models.Index(fields=['kernel_module', 'severity']),
            models.Index(fields=['quality_score']),
        ]
```

#### 3.2.3 TestCase表（测试数据表）

与TrainingCase结构完全相同，用于存储测试数据。

### 3.3 PostgreSQL表结构设计（原设计）

#### 3.2.1 案例表 (cases)
```sql
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    source_id VARCHAR(100),
    url TEXT,
    title TEXT NOT NULL,
    problem_description TEXT,
    problem_analysis TEXT,
    conclusion TEXT,
    solution TEXT,
    module VARCHAR(50),  -- memory, network, scheduler, lock, timer, storage, irq, driver, other
    tags JSONB DEFAULT '[]',
    votes INTEGER DEFAULT 0,
    answers_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    content_hash VARCHAR(64),  -- 用于去重
    embedding vector(1536),   -- 向量特征
    is_valid BOOLEAN DEFAULT true,
    
    INDEX idx_source (source),
    INDEX idx_module (module),
    INDEX idx_crawled_at (crawled_at),
    INDEX idx_content_hash (content_hash)
);
```

#### 3.2.2 SKILL表 (skills)
```sql
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module VARCHAR(50) NOT NULL,  -- 内核模块
    version INTEGER NOT NULL,
    skill_data JSONB NOT NULL,   -- 技能数据
    case_count INTEGER DEFAULT 0, -- 使用的案例数
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(module, version)
);

CREATE INDEX idx_skill_module ON skills(module);
```

#### 3.2.3 爬取任务表 (crawl_tasks)
```sql
CREATE TABLE crawl_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- pending, running, completed, failed
    total_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    
    INDEX idx_status (status),
    INDEX idx_source (source)
);
```

#### 3.2.4 分析历史表 (analysis_history)
```sql
CREATE TABLE analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_input TEXT NOT NULL,
    logs TEXT,
    module VARCHAR(50),
    analysis_result JSONB,
    used_cases JSONB,  -- 引用的案例
    used_skills JSONB, -- 使用的技能
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_created_at (created_at)
);
```

### 3.3 向量数据库设计 (ChromaDB)

#### 3.3.1 集合设计
```python
# 案例向量集合
CASE_COLLECTION = "kernel_cases"

# 向量配置
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
```

#### 3.3.2 元数据字段
```python
{
    "case_id": "uuid",
    "source": "stackoverflow",
    "module": "memory",
    "title": "问题标题",
    "votes": 10,
    "crawled_at": "2024-01-01T00:00:00"
}
```

### 3.4 服务设计

#### 3.4.1 案例服务 (CaseService)
```python
class CaseService:
    """案例服务"""
    
    async def create_case(self, case: CreateCaseSchema) -> Case:
        """创建案例"""
    
    async def get_case(self, case_id: UUID) -> Case:
        """获取案例"""
    
    async def list_cases(self, filters: CaseFilter, pagination: Pagination) -> List[Case]:
        """列表查询"""
    
    async def update_case(self, case_id: UUID, data: UpdateCaseSchema) -> Case:
        """更新案例"""
    
    async def delete_case(self, case_id: UUID):
        """删除案例"""
    
    async def get_cases_by_module(self, module: str, limit: int = 100) -> List[Case]:
        """按模块获取案例"""
```

#### 3.4.2 向量服务 (VectorService)
```python
class VectorService:
    """向量服务"""
    
    async def create_embedding(self, text: str) -> List[float]:
        """生成向量"""
    
    async def index_case(self, case_id: UUID, text: str, metadata: dict):
        """索引案例"""
    
    async def search_similar(self, query: str, module: str = None, top_k: int = 5) -> List[SimilarCase]:
        """相似检索"""
    
    async def delete_from_index(self, case_id: UUID):
        """删除索引"""
    
    async def rebuild_index(self):
        """重建索引"""
```

---

## 4. 模块三：SKILL提取模块

### 4.1 模块职责
从案例数据库中提取Linux内核各模块的问题分析SKILL，包括分析方法、调试工具、关键参数、常见根因和解决方案。

### 4.2 SKILL结构设计

#### 4.2.1 模块级SKILL
```python
class ModuleSkill(BaseModel):
    """模块级技能"""
    module: str                    # 模块名
    analysis_method: List[str]   # 分析方法
    debug_tools: List[str]        # 调试工具
    key_parameters: List[str]     # 关键参数
    common_root_causes: List[str] # 常见根因
    solutions: List[str]           # 解决方案
    reference_cases: List[UUID]    # 参考案例ID
```

#### 4.2.2 总SKILL
```python
class TotalSkill(BaseModel):
    """总技能"""
    module_skills: Dict[str, ModuleSkill]  # 各模块技能
    general_methodology: str               # 通用方法论
    skill_usage_guide: str                  # 技能使用指南
```

#### 4.2.3 SKILL模板示例
```python
# Memory模块SKILL
MEMORY_SKILL_TEMPLATE = {
    "module": "memory",
    "analysis_method": [
        "分析vmstat输出，观察si/so（swap in/out）",
        "检查slabtop输出，分析slab分配器状态",
        "查看/proc/meminfo，分析内存使用情况",
        "分析dmesg中的OOM killer日志",
        "使用kmemleak检测内存泄漏"
    ],
    "debug_tools": [
        "vmstat",
        "slabtop", 
        "pmap",
        "kmemleak",
        "perf",
        "ftrace",
        "cat /proc/meminfo"
    ],
    "key_parameters": [
        "vm.swappiness",
        "vm.dirty_ratio",
        "vm.dirty_background_ratio",
        "kmalloc",
        "slab",
        "page cache"
    ],
    "common_root_causes": [
        "内存泄漏（kernel memory leak）",
        "页错误风暴（page fault storm）",
        "OOM（Out of Memory）",
        "内存碎片化",
        "swap风暴"
    ],
    "solutions": [
        "释放page cache: echo 3 > /proc/sys/vm/drop_caches",
        "调整vm.swappiness参数",
        "使用kmemleak定位泄漏",
        "优化内存分配策略"
    ]
}
```

### 4.3 SKILL提取流程

#### 4.3.1 提取器设计
```python
class SkillExtractor:
    """SKILL提取器"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    async def extract_module_skill(self, module: str, cases: List[Case]) -> ModuleSkill:
        """
        从案例中提取模块SKILL
        1. 收集该模块所有案例
        2. 分析案例的问题分析方法
        3. 提取调试工具和参数
        4. 总结常见根因和解决方案
        """
        # 分析案例
        # 调用LLM提炼
        # 结构化输出
    
    async def extract_total_skill(self, all_skills: Dict[str, ModuleSkill]) -> TotalSkill:
        """
        生成总SKILL
        整合各模块SKILL
        生成通用方法论
        """
    
    async def update_skills(self, module: str = None):
        """
        更新SKILL
        指定模块：增量更新
        不指定：全量更新
        """
```

#### 4.3.2 提取流程图
```
开始
  │
  ▼
获取待处理模块
  │
  ▼
读取该模块所有案例
  │
  ▼
分析案例的问题分析思路
  │
  ├── 分析问题描述
  ├── 分析解决步骤
  └── 分析结论
  │
  ▼
调用LLM提炼SKILL
  │
  ▼
结构化SKILL输出
  │
  ▼
存储到数据库
  │
  ▼
更新向量库（可选）
  │
结束
```

### 4.4 SKILL版本管理

```python
class SkillVersionManager:
    """SKILL版本管理器"""
    
    async def create_version(self, module: str, skill_data: dict) -> int:
        """创建新版本"""
        # 获取当前版本号+1
        # 插入新版本记录
    
    async def get_version(self, module: str, version: int = None) -> Skill:
        """获取指定版本"""
        # 不指定则返回最新版本
    
    async def list_versions(self, module: str) -> List[int]:
        """列出所有版本"""
    
    async def rollback(self, module: str, version: int):
        """回滚到指定版本"""
```

### 4.5 API接口设计

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/v1/skill/{module} | GET | 获取模块SKILL |
| /api/v1/skill/total | GET | 获取总SKILL |
| /api/v1/skill/extract | POST | 触发SKILL提取 |
| /api/v1/skill/version/{module} | GET | 获取版本历史 |
| /api/v1/skill/rollback | POST | 回滚版本 |

---

## 5. 模块四：问题分析模块

### 5.1 模块职责
接收用户输入的问题信息，结合RAG和SKILL，调用LLM进行问题分析，返回分析结果。

### 5.2 核心服务设计

#### 5.2.1 分析服务 (AnalysisService)
```python
class AnalysisService:
    """问题分析服务"""
    
    def __init__(
        self, 
        vector_service: VectorService,
        skill_service: SkillService,
        llm_client: LLMClient
    ):
        self.vector_service = vector_service
        self.skill_service = skill_service
        self.llm = llm_client
    
    async def analyze(
        self, 
        user_input: UserProblemInput
    ) -> AnalysisResult:
        """
        完整分析流程
        1. 判断问题所属模块
        2. RAG检索相似案例
        3. 加载对应SKILL
        4. 构建提示词
        5. 调用LLM分析
        6. 返回结果
        """
    
    async def determine_module(self, user_input: UserProblemInput) -> str:
        """判断问题所属模块"""
        # 使用关键词匹配或LLM判断
    
    async def rag_retrieve(self, user_input: UserProblemInput, module: str, top_k: int = 5) -> List[RetrievedCase]:
        """RAG检索"""
    
    async def build_prompt(
        self, 
        user_input: UserProblemInput,
        cases: List[RetrievedCase],
        skill: Union[ModuleSkill, TotalSkill]
    ) -> str:
        """构建提示词"""
    
    async def call_llm(self, prompt: str) -> LLMResponse:
        """调用LLM"""
```

#### 5.2.2 提示词模板
```python
ANALYZE_PROMPT_TEMPLATE = """你是一个Linux内核问题分析专家。请根据以下信息分析问题。

## 用户问题
{user_input}

## 错误日志
{logs}

## 相关案例（来自RAG）
{similar_cases}

## 分析技能（SKILL）
{skill}

## 输出要求
请按以下格式输出分析结果：
1. 问题分类：判断问题属于哪个内核模块
2. 根因分析：分析问题的根本原因
3. 影响评估：评估问题的影响范围和严重程度
4. 解决方案：给出具体的解决步骤
5. 参考案例：推荐的相关案例

请确保分析基于提供的案例和技能，结论有据可循。
"""
```

#### 5.2.3 结果模型
```python
class AnalysisResult(BaseModel):
    """分析结果"""
    id: UUID
    module: str                      # 问题所属模块
    classification: str              # 问题分类
    root_cause: str                  # 根因分析
    impact_assessment: str           # 影响评估
    solution: str                    # 解决方案
    confidence: float                 # 置信度
    reference_cases: List[ReferenceCase]  # 参考案例
    skill_used: List[str]            # 使用的技能
    created_at: datetime

class ReferenceCase(BaseModel):
    """参考案例"""
    case_id: UUID
    title: str
    similarity: float
    solution_summary: str
```

### 5.3 分析流程

```
用户输入问题
     │
     ▼
┌──────────────┐
│ 判断所属模块  │──> 关键词匹配 / LLM判断
└──────────────┘
     │
     ▼
┌──────────────┐
│  RAG检索     │──> 向量相似度检索
│  相似案例    │──> 返回Top-K案例
└──────────────┘
     │
     ▼
┌──────────────┐
│  加载SKILL   │──> 根据模块加载对应技能
│              │──> 或加载总SKILL
└──────────────┘
     │
     ▼
┌──────────────┐
│  构建提示词   │──> 整合用户输入+RAG+SKILL
└──────────────┘
     │
     ▼
┌──────────────┐
│  调用LLM     │──> GPT-4 / 本地模型
└──────────────┘
     │
     ▼
┌──────────────┐
│  解析结果    │──> 结构化输出
└──────────────┘
     │
     ▼
   返回结果
```

### 5.4 模块判断逻辑

```python
MODULE_KEYWORDS = {
    "memory": ["memory", "oom", "kmalloc", "slab", "page fault", "内存", "泄漏"],
    "network": ["network", "tcp", "udp", "socket", "网卡", "协议栈"],
    "scheduler": ["schedule", "process", "task", "调度", "进程", "cfs"],
    "lock": ["lock", "mutex", "spinlock", "rcu", "deadlock", "锁"],
    "timer": ["timer", "hrtimer", "tick", "定时器", "超时"],
    "storage": ["disk", "io", "block", "filesystem", "存储", "读写"],
    "irq": ["interrupt", "irq", "中断", "软中断"],
    "driver": ["driver", "device", "驱动", "硬件"]
}

async def determine_module(user_input: str) -> str:
    """判断问题所属模块"""
    input_lower = user_input.lower()
    
    for module, keywords in MODULE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in input_lower:
                return module
    
    # 未匹配到，使用LLM判断
    return await llm_judge_module(user_input)
```

### 5.5 API接口设计

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/v1/analyze | POST | 提交问题分析 |
| /api/v1/analyze/history | GET | 分析历史记录 |
| /api/v1/analyze/{id} | GET | 获取分析结果详情 |

---

## 6. 模块五：RAG系统（已实现）

### 6.1 模块职责
实现基于检索增强生成（RAG）的智能问答系统，提供向量检索、案例推荐、智能问答等功能。

### 6.2 核心组件设计

#### 6.2.1 向量检索器 (VectorRetriever)
```python
class VectorRetriever:
    """向量检索器"""
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """向量相似度检索"""
    
    def search_by_module(self, query: str, module: str, top_k: int = 5) -> List[Dict]:
        """按模块检索"""
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """混合检索（向量+关键词）"""
```

**性能指标**:
- 检索延迟: < 1秒
- 相似度: 85-90%
- 支持模块过滤

#### 6.2.2 案例推荐引擎 (CaseRecommender)
```python
class CaseRecommender:
    """案例推荐引擎"""
    
    def recommend(self, case_id: str, top_k: int = 5) -> List[Dict]:
        """基于案例推荐相似案例"""
    
    def recommend_by_symptoms(self, symptoms: str, top_k: int = 5) -> List[Dict]:
        """基于症状推荐"""
```

#### 6.2.3 智能问答引擎 (QAEngine)
```python
class QAEngine:
    """智能问答引擎"""
    
    def answer(self, question: str, cases: List[Dict]) -> Dict:
        """生成答案"""
    
    def multi_turn_chat(self, question: str, history: List[Dict]) -> Dict:
        """多轮对话"""
    
    def analyze_issue(self, description: str, logs: str) -> Dict:
        """问题分析"""
```

**性能指标**:
- 响应时间: 2-3秒
- 置信度: 75-85%
- 支持多轮对话

### 6.3 API接口设计

| 接口 | 方法 | 描述 |
|------|------|------|
| /api/search | POST | 向量检索 |
| /api/recommend | POST | 案例推荐 |
| /api/qa | POST | 智能问答 |
| /api/analyze | POST | 问题分析 |
| /api/health | GET | 健康检查 |

### 6.4 Web界面设计

**页面列表**:
1. **Dashboard** - 系统概览和统计
2. **Search** - 向量检索界面
3. **Q&A** - 智能问答界面
4. **Analyze** - 问题分析界面

**技术栈**:
- Bootstrap 5 - 响应式设计
- JavaScript (Fetch API) - 异步交互
- Django Templates - 服务端渲染

### 6.5 实现文件
- `cases/rag/vector_retriever.py` - 向量检索器
- `cases/rag/case_recommender.py` - 案例推荐引擎
- `cases/rag/qa_engine.py` - 智能问答引擎
- `cases/api_views.py` - REST API视图
- `cases/rag_views.py` - Web界面视图
- `rag_cli.py` - 命令行工具

---

## 7. 模块六：高质量案例收集（进行中）

### 7.1 模块职责
从权威数据源收集高质量Linux内核问题案例，确保案例的真实性、完整性和技术准确性。

### 7.2 数据源设计

#### 7.2.1 Git Fix Commits
- **来源**: Linux内核Git仓库
- **内容**: 实际bug修复提交
- **质量**: 高（包含详细commit message）
- **数量**: 30 cases/cycle

#### 7.2.2 CVE Database
- **来源**: CVE漏洞数据库
- **内容**: 安全漏洞案例
- **质量**: 高（官方验证）
- **数量**: 30 cases/cycle

#### 7.2.3 Kernel Documentation
- **来源**: Linux内核官方文档
- **内容**: 故障排查指南
- **质量**: 高（官方文档）
- **数量**: 30 cases/cycle

#### 7.2.4 LKML (Linux Kernel Mailing List)
- **来源**: 内核邮件列表
- **内容**: 开发者讨论和问题分析
- **质量**: 高（专家见解）
- **数量**: 10 cases/cycle

#### 7.2.5 Kernel Bugzilla
- **来源**: 官方Bug跟踪系统
- **内容**: 结构化bug报告
- **质量**: 高（可复现）
- **数量**: 10 cases/cycle

### 7.3 收集流程

```
启动收集器
    │
    ▼
收集周期开始
    │
    ├─> Git Fixes (30 cases)
    ├─> CVE Database (30 cases)
    ├─> Kernel Docs (30 cases)
    ├─> LKML (10 cases)
    └─> Bugzilla (10 cases)
    │
    ▼
质量过滤 (quality_score >= 80)
    │
    ▼
去重检查 (content_hash)
    │
    ▼
保存到数据库 (80% Training, 20% Test)
    │
    ▼
检查目标 (1000+ cases)
    │
    ├─> 未达到: 等待5分钟，继续下一周期
    └─> 已达到: 停止收集
```

### 7.4 质量保证机制

#### 7.4.1 唯一性保证
```python
def _generate_content_hash(case_data):
    """生成内容哈希"""
    content = f"{case_data['title']}|{case_data['phenomenon']}|{case_data['root_cause']}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()
```

#### 7.4.2 标题唯一性
- 每个案例具有描述性标题
- 标题反映具体问题内容
- 避免通用标题重复

#### 7.4.3 质量评分
- **最低阈值**: 80分
- **评估维度**: 完整性、准确性、可复现性
- **自动过滤**: 低质量案例自动跳过

### 7.5 后台收集器设计

```python
class BackgroundCollector:
    """后台收集器"""
    
    def __init__(self):
        self.log_file = '/var/log/collector.log'
        self.target = 1000
    
    def run(self):
        """主循环"""
        while not self.target_reached():
            self.run_collection_cycle()
            time.sleep(300)  # 5分钟间隔
    
    def run_collection_cycle(self):
        """执行收集周期"""
        # 收集案例
        # 质量过滤
        # 保存数据库
        # 记录日志
```

### 7.6 监控和管理

#### 7.6.1 监控脚本
```bash
# 查看收集器状态
./monitor_collector.sh

# 查看实时日志
tail -f /var/log/collector.log

# 检查数据库进度
python3 -c "from cases.models import TrainingCase, TestCase; ..."
```

#### 7.6.2 管理命令
```bash
# 停止收集器
kill $(cat /tmp/collector.pid)

# 重启收集器
nohup python3 run_background_collector.py &
```

### 7.7 实现文件
- `collect_high_quality_cases.py` - 高质量案例收集器
- `collect_real_cases.py` - 真实案例收集器
- `cases/acquisition/lkml_fetcher.py` - LKML收集器
- `cases/acquisition/bugzilla_fetcher.py` - Bugzilla收集器
- `run_background_collector.py` - 后台收集运行器
- `monitor_collector.sh` - 监控脚本
- `COLLECTOR_STATUS.md` - 状态文档

### 7.8 当前进度 (2026-03-20)
- **Training cases**: 203
- **Test cases**: 57
- **Total**: 260/1000 (26.0%)
- **Status**: 后台收集器运行中
- **PID**: 3243205
- **Estimated completion**: 1-2小时

---

## 8. 数据流转设计

### 8.1 案例数据流转
```
技术社区 ──爬虫──> 原始数据 ──清洗──> 案例数据
                                         │
                                         ▼
                              PostgreSQL (结构化存储)
                                         │
                                         ▼
                              ChromaDB (向量索引)
```

### 6.2 SKILL数据流转
```
案例库 ──读取──> SKILL提取器 ──LLM提炼──> SKILL库
                                                    │
                                         PostgreSQL (版本存储)
```

### 8.3 问题分析数据流转
```
用户输入 ──> 预处理 ──> 模块判断 ──> RAG检索
                                         │
                                         ▼
                              相似案例 + SKILL + 输入
                                         │
                                         ▼
                                    LLM分析
                                         │
                                         ▼
返回分析结果 ──> 存储历史 ──> 展示给用户
```

---

## 7. 配置设计

### 7.1 环境配置
```python
# config.py
class Settings(BaseSettings):
    # 数据库
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "problemai"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "problemai"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # LLM
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    
    # 向量
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    
    # 爬虫
    CRAWL_INTERVAL_HOURS: int = 24
    CRAWL_KEYWORDS: List[str]
    
    # 本地代码库
    KERNEL_CODE_PATH: str = "./data/kernel_code"
```

---

## 8. 部署设计

### 8.1 Docker Compose配置
```yaml
version: '3.8'

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    volumes:
      - ./data:/data

  crawler:
    build: ./crawler
    environment:
      - POSTGRES_HOST=postgres
    depends_on:
      - postgres

  skill_extractor:
    build: ./skill_extractor
    environment:
      - POSTGRES_HOST=postgres
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: problemai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: problemai
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

  chroma:
    image: chromadb/chroma:latest
    volumes:
      - chroma_data:/chroma/chroma

volumes:
  postgres_data:
  redis_data:
  chroma_data:
```

---

## 9. 开发计划

### Phase 1: 基础架构 (Week 1)
- [ ] 项目初始化
- [ ] PostgreSQL表结构设计
- [ ] FastAPI基础框架搭建
- [ ] 用户认证模块

### Phase 2: 案例获取模块 (Week 2)
- [ ] 爬虫基类设计
- [ ] Stack Overflow爬虫实现
- [ ] CSDN爬虫实现
- [ ] 内容清洗和去重
- [ ] 案例入库

### Phase 3: 数据存储和RAG (Week 2-3)
- [ ] 向量数据库集成
- [ ] Embedding生成
- [ ] RAG检索功能

### Phase 4: SKILL提取模块 (Week 3)
- [ ] SKILL结构设计
- [ ] SKILL提取器实现
- [ ] 版本管理

### Phase 5: 问题分析模块 (Week 3-4)
- [ ] 分析流程设计
- [ ] RAG + SKILL + LLM整合
- [ ] 提示词优化

### Phase 6: 前端和测试 (Week 4)
- [ ] Web界面开发
- [ ] 系统集成测试
- [ ] 部署上线