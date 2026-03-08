from django.db import models
from django.utils import timezone


class KernelCase(models.Model):
    """Kernel issue case model - 通用案例表"""
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
    
    class Meta:
        verbose_name = 'Kernel Issue Case'
        verbose_name_plural = 'Kernel Issue Cases'
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.case_id}: {self.title}"
    
    @property
    def severity_display(self):
        severity_dict = dict(self.SEVERITY_CHOICES)
        return severity_dict.get(self.severity, self.severity)
    
    @classmethod
    def search(cls, query):
        from django.db.models import Q
        
        return cls.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(symptoms__icontains=query) |
            Q(root_cause__icontains=query) |
            Q(solution__icontains=query) |
            Q(affected_components__icontains=query) |
            Q(case_id__icontains=query)
        )
    
    @classmethod
    def get_severity_stats(cls):
        from django.db.models import Count
        return cls.objects.values('severity').annotate(count=Count('severity'))


class RawCase(models.Model):
    """原始案例表 - 存放爬取到的原始内容，按顺序存放"""
    MODULE_CHOICES = KernelCase.MODULE_CHOICES
    
    id = models.BigAutoField(primary_key=True)
    raw_content = models.TextField(verbose_name='原始内容', help_text='爬取到的原始HTML或文本内容')
    source = models.CharField(max_length=50, verbose_name='来源', default='', help_text='stackoverflow, csdn, zhihu等')
    source_url = models.URLField(verbose_name='原始URL', blank=True, default='')
    source_id = models.CharField(max_length=100, verbose_name='源站ID', blank=True, default='')
    fetched_at = models.DateTimeField(auto_now_add=True, verbose_name='爬取时间')
    processed = models.BooleanField(default=False, verbose_name='是否已处理')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    
    class Meta:
        verbose_name = '原始案例'
        verbose_name_plural = '原始案例'
        ordering = ['id']
    
    def __str__(self):
        return f"RawCase-{self.id}: {self.source}"


class TrainingCase(models.Model):
    """训练集表 - 存储过滤后的高质量案例，按顺序存放"""
    MODULE_CHOICES = KernelCase.MODULE_CHOICES
    
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=500, verbose_name='标题')
    phenomenon = models.TextField(verbose_name='问题现象', default='')
    key_logs = models.TextField(verbose_name='关键日志', default='')
    environment = models.TextField(verbose_name='环境信息', default='')
    root_cause = models.TextField(verbose_name='根本原因', default='')
    analysis_process = models.TextField(verbose_name='分析过程', default='')
    solution = models.TextField(verbose_name='解决方案', default='')
    related_code = models.TextField(verbose_name='相关代码', default='', blank=True)
    fix_code = models.TextField(verbose_name='修复代码', default='', blank=True)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name='内核模块', default='other')
    tags = models.JSONField(verbose_name='标签', default=list, blank=True)
    
    source = models.CharField(max_length=50, verbose_name='来源', default='')
    source_url = models.URLField(verbose_name='原始URL', blank=True, default='')
    raw_case = models.ForeignKey(RawCase, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='原始案例')
    quality_score = models.FloatField(verbose_name='质量分数', default=0.0)
    confidence = models.FloatField(verbose_name='置信度', default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '训练集案例'
        verbose_name_plural = '训练集案例'
        ordering = ['id']
    
    def __str__(self):
        return f"TrainingCase-{self.id}: {self.title[:50]}"


class TestCase(models.Model):
    """测试集表 - 存储测试案例，按顺序存放"""
    MODULE_CHOICES = KernelCase.MODULE_CHOICES
    
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=500, verbose_name='标题')
    phenomenon = models.TextField(verbose_name='问题现象', default='')
    key_logs = models.TextField(verbose_name='关键日志', default='')
    environment = models.TextField(verbose_name='环境信息', default='')
    root_cause = models.TextField(verbose_name='根本原因', default='')
    analysis_process = models.TextField(verbose_name='分析过程', default='')
    solution = models.TextField(verbose_name='解决方案', default='')
    related_code = models.TextField(verbose_name='相关代码', default='', blank=True)
    fix_code = models.TextField(verbose_name='修复代码', default='', blank=True)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES, verbose_name='内核模块', default='other')
    tags = models.JSONField(verbose_name='标签', default=list, blank=True)
    
    source = models.CharField(max_length=50, verbose_name='来源', default='')
    source_url = models.URLField(verbose_name='原始URL', blank=True, default='')
    raw_case = models.ForeignKey(RawCase, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='原始案例')
    quality_score = models.FloatField(verbose_name='质量分数', default=0.0)
    confidence = models.FloatField(verbose_name='置信度', default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '测试集案例'
        verbose_name_plural = '测试集案例'
        ordering = ['id']
    
    def __str__(self):
        return f"TestCase-{self.id}: {self.title[:50]}"