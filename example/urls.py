from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers

from .app.api import views

api_router = routers.DefaultRouter()
api_router.register(
    "model-api",
    views.ModelWithFilesViewSet,
    basename="model-api",
)

urlpatterns = [
    *api_router.urls,
    path(
        "s3/",
        include("saritasa_s3_tools.django.urls"),
        name="saritasa-s3-tools",
    ),
    *static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    ),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
