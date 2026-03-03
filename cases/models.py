from django.db import models
from django.utils import timezone

class KernelCase(models.Model):
    """Kernel issue case model"""
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    case_id = models.CharField(max_length=50, unique=True, verbose_name='Case ID')
    title = models.CharField(max_length=200, verbose_name='Title')
    description = models.TextField(verbose_name='Description')
    symptoms = models.TextField(verbose_name='Symptoms')
    root_cause = models.TextField(verbose_name='Root Cause')
    solution = models.TextField(verbose_name='Solution')
    kernel_version = models.CharField(max_length=50, verbose_name='Kernel Version')
    affected_components = models.CharField(max_length=200, verbose_name='Affected Components')
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, verbose_name='Severity')
    created_date = models.DateTimeField(default=timezone.now, verbose_name='Created Date')
    updated_date = models.DateTimeField(auto_now=True, verbose_name='Updated Date')
    
    class Meta:
        verbose_name = 'Kernel Issue Case'
        verbose_name_plural = 'Kernel Issue Cases'
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.case_id}: {self.title}"
    
    @property
    def severity_display(self):
        """Returns the display text for severity level"""
        severity_dict = dict(self.SEVERITY_CHOICES)
        return severity_dict.get(self.severity, self.severity)
    
    @classmethod
    def search(cls, query):
        """Performs multi-field search based on keywords"""
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
        """Gets statistics grouped by severity level"""
        from django.db.models import Count
        return cls.objects.values('severity').annotate(count=Count('severity'))