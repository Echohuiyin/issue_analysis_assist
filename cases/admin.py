from django.contrib import admin
from .models import KernelCase, RawCase, TrainingCase, TestCase


@admin.register(KernelCase)
class KernelCaseAdmin(admin.ModelAdmin):
    list_display = ['case_id', 'title', 'module', 'severity', 'source', 'created_date']
    list_filter = ['module', 'severity', 'source']
    search_fields = ['title', 'description', 'symptoms', 'root_cause']
    readonly_fields = ['created_date', 'updated_date']


@admin.register(RawCase)
class RawCaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'source', 'source_url', 'fetched_at', 'processed']
    list_filter = ['source', 'processed']
    search_fields = ['source_url', 'raw_content']
    readonly_fields = ['fetched_at']
    actions = ['mark_as_processed']

    def mark_as_processed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(processed=True, processed_at=timezone.now())
        self.message_user(request, f'{updated} cases marked as processed.')
    mark_as_processed.short_description = '标记为已处理'


@admin.register(TrainingCase)
class TrainingCaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'module', 'quality_score', 'source', 'created_at']
    list_filter = ['module', 'source']
    search_fields = ['title', 'phenomenon', 'root_cause', 'solution']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'module', 'quality_score', 'source', 'created_at']
    list_filter = ['module', 'source']
    search_fields = ['title', 'phenomenon', 'root_cause', 'solution']
    readonly_fields = ['created_at', 'updated_at']