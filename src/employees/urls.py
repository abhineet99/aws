from django.urls import path, include
from .views import dashboard

from rest_framework.routers import DefaultRouter
from .api import RoleViewSet
router = DefaultRouter()
router.register(r'role', RoleViewSet)


urlpatterns = [
	# path('dashboard/', dashboard, name='dashboard'),
	path('api/', include(router.urls)),
]