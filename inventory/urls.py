from django.urls import path, include
from rest_framework.routers import DefaultRouter    # builds URLs automatically from a ViewSet

from .views import ProductViewSet, StockEntryViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")   # /products/
router.register("entries", StockEntryViewSet, basename="entry")   # /entries/

urlpatterns = [
    path("", include(router.urls)),                                # all router URLs
]