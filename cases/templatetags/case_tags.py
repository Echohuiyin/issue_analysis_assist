from django import template

register = template.Library()

@register.filter
def severity_class(severity):
    """
    Returns the corresponding CSS class based on severity level
    """
    severity_mapping = {
        'Critical': 'bg-danger',
        'High': 'bg-warning',
        'Medium': 'bg-info',
        'Low': 'bg-secondary'
    }
    return severity_mapping.get(severity, 'bg-secondary')

@register.filter
def severity_display(severity):
    """
    Returns the display text based on severity level
    """
    severity_mapping = {
        'Critical': 'Critical',
        'High': 'High',
        'Medium': 'Medium',
        'Low': 'Low'
    }
    return severity_mapping.get(severity, severity)