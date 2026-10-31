from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action              # for our own extra endpoints
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from . import services
from .auth import Roles
from .models import Product, StockEntry
from .serializers import ProductSerializer, StockEntrySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).order_by("id")
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "balance"):    # reading: both roles
            return [Roles("Manager", "Storekeeper")()]
        return [Roles("Manager")()]    # create, update, delete, low_stock: Manager only

    @action(detail=True, methods=["get"])                     # URL: /products/<id>/balance/
    def balance(self, request, pk=None):
        product = self.get_object()                           # finds the product from the id in the URL
        return Response(services.product_balance(product))

    @action(detail=False, methods=["get"], url_path="low-stock")   # URL: /products/low-stock/
    def low_stock(self, request):
        threshold = request.query_params.get("threshold", "10")    # ?threshold=10, default 10
        if not threshold.isdigit():
            raise ValidationError({"threshold": "Must be a whole number."})
        return Response(services.low_stock(int(threshold)))


class StockEntryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StockEntrySerializer
    queryset = StockEntry.objects.select_related(
        "product", "warehouse", "to_warehouse"
    ).order_by("-id")

    def get_permissions(self):
        if self.action == "create":
            return [Roles("Storekeeper")()]
        return [Roles("Manager", "Storekeeper")()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry = services.create_entry(request.user, **serializer.validated_data)
        return Response(self.get_serializer(entry).data, status=status.HTTP_201_CREATED)