from django.urls import path
from .views import CaseListView, CaseDetailView, CaseCreateView, SearchView, StatsView

urlpatterns = [
    path('', CaseListView.as_view(), name='index'),
    path('case/<int:case_id>/', CaseDetailView.as_view(), name='case_detail'),
    path('add/', CaseCreateView.as_view(), name='add_case'),
    path('search/', SearchView.as_view(), name='search'),
    path('stats/', StatsView.as_view(), name='stats'),
]