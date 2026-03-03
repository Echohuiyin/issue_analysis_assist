from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import KernelCase
from .forms import KernelCaseForm

class CaseListView(ListView):
    """Case list view"""
    model = KernelCase
    template_name = 'cases/index.html'
    context_object_name = 'cases'
    paginate_by = 20
    ordering = ['-created_date']

class CaseDetailView(DetailView):
    """Case detail view"""
    model = KernelCase
    template_name = 'cases/case_detail.html'
    context_object_name = 'case'
    pk_url_kwarg = 'case_id'

class CaseCreateView(CreateView):
    """Add new case view"""
    model = KernelCase
    form_class = KernelCaseForm
    template_name = 'cases/add_case.html'
    success_url = reverse_lazy('index')
    
    def form_valid(self, form):
        """Handle form validation"""
        messages.success(self.request, 'Case added successfully!')
        return super().form_valid(form)

class SearchView(ListView):
    """Search cases view"""
    model = KernelCase
    template_name = 'cases/index.html'
    context_object_name = 'cases'
    paginate_by = 20
    ordering = ['-created_date']

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        if query:
            return KernelCase.search(query)
        return KernelCase.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('query', '')
        return context

class StatsView(View):
    """Statistics view"""
    template_name = 'cases/stats.html'

    def get(self, request, *args, **kwargs):
        total_cases = KernelCase.objects.count()
        severity_stats = KernelCase.get_severity_stats()
        
        context = {
            'total_cases': total_cases,
            'severity_stats': severity_stats
        }
        return render(request, self.template_name, context)