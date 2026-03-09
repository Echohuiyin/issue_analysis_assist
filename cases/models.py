from django.db import models
from django.utils import timezone


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
        db_table = 'raw_cases'
        verbose_name = '原始案例'
        verbose_name_plural = '原始案例'
        ordering = ['-fetch_time']
        indexes = [
            models.Index(fields=['source', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"[{self.get_source_display()}] {self.raw_title[:50]}"


class TrainingCase(models.Model):
    """训练数据表 - 存储高质量的结构化案例"""
    
    SEVERITY_CHOICES = [
        ('Low', '低'),
        ('Medium', '中'),
        ('High', '高'),
        ('Critical', '严重'),
    ]
    
    MODULE_CHOICES = [
        ('memory', '内存管理'),
        ('network', '网络'),
        ('scheduler', '调度器'),
        ('lock', '锁/同步'),
        ('timer', '定时器'),
        ('storage', '存储/文件系统'),
        ('irq', '中断'),
        ('driver', '设备驱动'),
        ('other', '其他'),
    ]
    
    case_id = models.CharField(max_length=50, unique=True, verbose_name='案例ID', db_index=True)
    raw_case = models.ForeignKey(RawCase, on_delete=models.SET_NULL, null=True, blank=True, 
                                  verbose_name='原始案例', related_name='training_cases')
    
    title = models.CharField(max_length=200, verbose_name='标题')
    phenomenon = models.TextField(verbose_name='问题现象')
    key_logs = models.TextField(verbose_name='关键日志', blank=True, default='')
    environment = models.TextField(verbose_name='环境信息', blank=True, default='')
    root_cause = models.TextField(verbose_name='根本原因')
    analysis_process = models.TextField(verbose_name='分析过程', blank=True, default='')
    troubleshooting_steps = models.JSONField(verbose_name='排查步骤', default=list, blank=True)
    solution = models.TextField(verbose_name='解决方案')
    prevention = models.TextField(verbose_name='预防措施', blank=True, default='')
    
    kernel_version = models.CharField(max_length=50, verbose_name='内核版本', blank=True, default='')
    affected_components = models.CharField(max_length=200, verbose_name='受影响组件', blank=True, default='')
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name='内核模块', default='other')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name='严重程度', default='Medium')
    
    source = models.CharField(max_length=50, verbose_name='数据源', blank=True, default='')
    source_id = models.CharField(max_length=100, verbose_name='源ID', blank=True, default='')
    url = models.URLField(verbose_name='原始URL', max_length=500, blank=True, default='')
    
    tags = models.JSONField(verbose_name='标签', default=list, blank=True)
    votes = models.IntegerField(verbose_name='投票数', default=0)
    answers_count = models.IntegerField(verbose_name='回答数', default=0)
    
    quality_score = models.FloatField(verbose_name='质量分数', default=0.0)
    confidence = models.FloatField(verbose_name='置信度', default=0.0)
    
    embedding = models.JSONField(verbose_name='向量嵌入', default=list, blank=True, 
                                  help_text='用于RAG的向量表示')
    content_hash = models.CharField(max_length=64, verbose_name='内容哈希', unique=True, db_index=True)
    
    created_date = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'training_cases'
        verbose_name = '训练案例'
        verbose_name_plural = '训练案例'
        ordering = ['-quality_score', '-created_date']
        indexes = [
            models.Index(fields=['module', 'severity']),
            models.Index(fields=['quality_score']),
        ]
    
    def __str__(self):
        return f"{self.case_id}: {self.title}"


class TestCase(models.Model):
    """测试数据表 - 存储高质量的结构化案例（格式与训练数据相同）"""
    
    SEVERITY_CHOICES = [
        ('Low', '低'),
        ('Medium', '中'),
        ('High', '高'),
        ('Critical', '严重'),
    ]
    
    MODULE_CHOICES = [
        ('memory', '内存管理'),
        ('network', '网络'),
        ('scheduler', '调度器'),
        ('lock', '锁/同步'),
        ('timer', '定时器'),
        ('storage', '存储/文件系统'),
        ('irq', '中断'),
        ('driver', '设备驱动'),
        ('other', '其他'),
    ]
    
    case_id = models.CharField(max_length=50, unique=True, verbose_name='案例ID', db_index=True)
    raw_case = models.ForeignKey(RawCase, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name='原始案例', related_name='test_cases')
    
    title = models.CharField(max_length=200, verbose_name='标题')
    phenomenon = models.TextField(verbose_name='问题现象')
    key_logs = models.TextField(verbose_name='关键日志', blank=True, default='')
    environment = models.TextField(verbose_name='环境信息', blank=True, default='')
    root_cause = models.TextField(verbose_name='根本原因')
    analysis_process = models.TextField(verbose_name='分析过程', blank=True, default='')
    troubleshooting_steps = models.JSONField(verbose_name='排查步骤', default=list, blank=True)
    solution = models.TextField(verbose_name='解决方案')
    prevention = models.TextField(verbose_name='预防措施', blank=True, default='')
    
    kernel_version = models.CharField(max_length=50, verbose_name='内核版本', blank=True, default='')
    affected_components = models.CharField(max_length=200, verbose_name='受影响组件', blank=True, default='')
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name='内核模块', default='other')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name='严重程度', default='Medium')
    
    source = models.CharField(max_length=50, verbose_name='数据源', blank=True, default='')
    source_id = models.CharField(max_length=100, verbose_name='源ID', blank=True, default='')
    url = models.URLField(verbose_name='原始URL', max_length=500, blank=True, default='')
    
    tags = models.JSONField(verbose_name='标签', default=list, blank=True)
    votes = models.IntegerField(verbose_name='投票数', default=0)
    answers_count = models.IntegerField(verbose_name='回答数', default=0)
    
    quality_score = models.FloatField(verbose_name='质量分数', default=0.0)
    confidence = models.FloatField(verbose_name='置信度', default=0.0)
    
    embedding = models.JSONField(verbose_name='向量嵌入', default=list, blank=True,
                                  help_text='用于RAG的向量表示')
    content_hash = models.CharField(max_length=64, verbose_name='内容哈希', unique=True, db_index=True)
    
    created_date = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'test_cases'
        verbose_name = '测试案例'
        verbose_name_plural = '测试案例'
        ordering = ['-quality_score', '-created_date']
        indexes = [
            models.Index(fields=['module', 'severity']),
            models.Index(fields=['quality_score']),
        ]
    
    def __str__(self):
        return f"{self.case_id}: {self.title}"


class KernelCase(models.Model):
    """兼容旧版本的案例模型（已弃用，保留用于数据迁移）"""
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    MODULE_CHOICES = [
        ('memory', 'Memory Management'),
        ('network', 'Network'),
        ('scheduler', 'Scheduler'),
        ('lock', 'Lock/Synchronization'),
        ('timer', 'Timer'),
        ('storage', 'Storage/Filesystem'),
        ('irq', 'Interrupt'),
        ('driver', 'Device Driver'),
        ('other', 'Other'),
    ]

    case_id = models.CharField(max_length=50, unique=True, verbose_name='Case ID')
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(verbose_name='Description')
    symptoms = models.TextField(verbose_name='Symptoms')
    root_cause = models.TextField(verbose_name='Root Cause')
    solution = models.TextField(verbose_name='Solution')
    kernel_version = models.CharField(max_length=50, verbose_name='Kernel Version', blank=True, default='')
    affected_components = models.CharField(max_length=200, verbose_name='Affected Components', blank=True, default='')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name='Severity', default='Medium')
    created_date = models.DateTimeField(default=timezone.now, verbose_name='Created Date')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='Updated Date')

    source = models.CharField(max_length=50, verbose_name='Source', blank=True, default='', help_text='e.g. stackoverflow, csdn, zhihu')
    source_id = models.CharField(max_length=100, verbose_name='Source ID', blank=True, default='')
    url = models.URLField(verbose_name='Original URL', blank=True, default='')
    problem_analysis = models.TextField(verbose_name='Problem Analysis', blank=True, default='')
    conclusion = models.TextField(verbose_name='Conclusion', blank=True, default='')
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name='Kernel Module', blank=True, default='other')
    tags = models.JSONField(verbose_name='Tags', default=list, blank=True)
    votes = models.IntegerField(verbose_name='Votes', default=0)
    answers_count = models.IntegerField(verbose_name='Answers Count', default=0)
    content_hash = models.CharField(max_length=64, verbose_name='Content Hash', blank=True, null=True, unique=True)
    embedding = models.JSONField(verbose_name='Embedding', default=list, blank=True, help_text='Vector representation for RAG')
    
    class Meta:
        db_table = 'kernel_cases'
        verbose_name = 'Kernel Issue Case (Legacy)'
        verbose_name_plural = 'Kernel Issue Cases (Legacy)'
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.case_id}: {self.title}"