from django.contrib import admin
from .models import RawCase, TrainingCase, TestCase, KernelCase


@admin.register(RawCase)
class RawCaseAdmin(admin.ModelAdmin):
    """原始案例管理"""
    list_display = ['raw_id', 'source', 'raw_title', 'status', 'fetch_time']
    list_filter = ['source', 'status', 'fetch_time']
    search_fields = ['raw_title', 'raw_content', 'url']
    readonly_fields = ['fetch_time', 'process_time']
    ordering = ['-fetch_time']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('source', 'source_id', 'url', 'content_hash')
        }),
        ('原始内容', {
            'fields': ('raw_title', 'raw_content', 'raw_html')
        }),
        ('处理状态', {
            'fields': ('status', 'fetch_time', 'process_time', 'process_error')
        }),
    )


@admin.register(TrainingCase)
class TrainingCaseAdmin(admin.ModelAdmin):
    """训练案例管理"""
    list_display = ['case_id', 'title', 'module', 'severity', 'quality_score', 'created_date']
    list_filter = ['module', 'severity', 'source', 'created_date']
    search_fields = ['case_id', 'title', 'phenomenon', 'root_cause', 'solution']
    readonly_fields = ['created_date', 'updated_date']
    ordering = ['-quality_score', '-created_date']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('case_id', 'raw_case', 'title', 'source', 'source_id', 'url')
        }),
        ('问题描述', {
            'fields': ('phenomenon', 'key_logs', 'environment')
        }),
        ('分析内容', {
            'fields': ('root_cause', 'analysis_process', 'troubleshooting_steps')
        }),
        ('解决方案', {
            'fields': ('solution', 'prevention')
        }),
        ('分类信息', {
            'fields': ('kernel_version', 'affected_components', 'module', 'severity', 'tags')
        }),
        ('质量评估', {
            'fields': ('quality_score', 'confidence', 'votes', 'answers_count')
        }),
        ('技术信息', {
            'fields': ('embedding', 'content_hash', 'created_date', 'updated_date')
        }),
    )


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    """测试案例管理"""
    list_display = ['case_id', 'title', 'module', 'severity', 'quality_score', 'created_date']
    list_filter = ['module', 'severity', 'source', 'created_date']
    search_fields = ['case_id', 'title', 'phenomenon', 'root_cause', 'solution']
    readonly_fields = ['created_date', 'updated_date']
    ordering = ['-quality_score', '-created_date']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('case_id', 'raw_case', 'title', 'source', 'source_id', 'url')
        }),
        ('问题描述', {
            'fields': ('phenomenon', 'key_logs', 'environment')
        }),
        ('分析内容', {
            'fields': ('root_cause', 'analysis_process', 'troubleshooting_steps')
        }),
        ('解决方案', {
            'fields': ('solution', 'prevention')
        }),
        ('分类信息', {
            'fields': ('kernel_version', 'affected_components', 'module', 'severity', 'tags')
        }),
        ('质量评估', {
            'fields': ('quality_score', 'confidence', 'votes', 'answers_count')
        }),
        ('技术信息', {
            'fields': ('embedding', 'content_hash', 'created_date', 'updated_date')
        }),
    )


# 保留旧模型的注册（兼容性）
admin.site.register(KernelCase)