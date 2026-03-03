from django import forms
from .models import KernelCase

class KernelCaseForm(forms.ModelForm):
    """Kernel case form"""
    class Meta:
        model = KernelCase
        exclude = ['created_date', 'updated_date']  # Exclude auto-managed date fields
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'symptoms': forms.Textarea(attrs={'rows': 4}),
            'root_cause': forms.Textarea(attrs={'rows': 4}),
            'solution': forms.Textarea(attrs={'rows': 4}),
        }