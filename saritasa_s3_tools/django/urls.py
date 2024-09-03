from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(
    prefix="",
    viewset=views.S3GetParamsView,
    basename="s3",
)
urlpatterns = router.urls
