from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CalculateView, SavedScenarioViewSet

router = DefaultRouter()
router.register('scenarios', SavedScenarioViewSet, basename='scenario')

urlpatterns = [
    path('calculate/', CalculateView.as_view(), name='mortgage-calculate'),
    path('', include(router.urls)),
]
