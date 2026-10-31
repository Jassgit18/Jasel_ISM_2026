from rest_framework import serializers      # DRF's serializer tools
from .models import Product, StockEntry     # the tables we serialize


class ProductSerializer(serializers.ModelSerializer):   # builds fields from the Product model
    class Meta:
        model = Product                                  # which model it works with
        fields = ["id", "name", "sku", "is_active"]      # fields shown in the JSON
        read_only_fields = ["id"]                        # the database makes the id


class StockEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockEntry
        fields = [
            "id", "product", "warehouse", "to_warehouse", "supplier",
            "entry_type", "quantity", "remarks", "created_by", "created_on",
        ]
        # These are shown in responses but ignored if the client sends them.
        # created_by is filled by the server from the logged-in user
        read_only_fields = ["id", "created_by", "created_on"]

    def validate_quantity(self, value):                  # DRF calls validate_<field> automatically
        if value <= 0:                                   # 0 is not a valid movement
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value                                     # valid, so hand the value back

    def validate_product(self, value):
        if not value.is_active:                          # a disabled product cannot be moved
            raise serializers.ValidationError("This product is disabled.")
        return value

    def validate_supplier(self, value):
        if value is not None and not value.is_active:    # supplier is optional, so None is allowed
            raise serializers.ValidationError("This supplier is disabled.")
        return value

    def validate(self, data):                            # runs after the field checks, sees the whole request
        entry_type = data.get("entry_type")
        to_warehouse = data.get("to_warehouse")

        if entry_type == "TRANSFER":
            if to_warehouse is None:                     # a transfer needs a destination
                raise serializers.ValidationError(
                    {"to_warehouse": "Destination warehouse is required for a transfer."}
                )
            if to_warehouse == data.get("warehouse"):    # source and destination must differ
                raise serializers.ValidationError(
                    {"to_warehouse": "Source and destination warehouse must be different."}
                )
        elif to_warehouse is not None:                   # IN and OUT must not have a destination
            raise serializers.ValidationError(
                {"to_warehouse": "Destination warehouse is only for a transfer."}
            )
        return data