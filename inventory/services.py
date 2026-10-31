from django.db import transaction                    # transaction.atomic = all-or-nothing saves
from django.db.models import Sum, Q                  # Sum adds numbers, Q builds OR conditions
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
# NotFound -> 404, PermissionDenied -> 403, ValidationError -> 400

from .models import Product, StockEntry,Warehouse


def _require_role(user, *roles):                     # leading _ means "helper, used only in this file"
    role = getattr(user, "roleid", None)             # get the user's role, or None if missing
    if not user.is_authenticated or role is None or role.title not in roles:
        raise PermissionDenied(f"Not allowed. Required role: {', '.join(roles)}.")   # second role check


def get_balance(product_id, warehouse_id):
    """Current stock of one product in one warehouse, worked out from the entries."""

    # Stock that came IN: stock-in entries here + transfers that arrived here
    incoming = StockEntry.objects.filter(product_id=product_id).filter(
        Q(entry_type="IN", warehouse_id=warehouse_id)
        | Q(entry_type="TRANSFER", to_warehouse_id=warehouse_id)
    ).aggregate(total=Sum("quantity"))["total"] or 0      # "or 0" when there are no rows (None)

    # Stock that went OUT: stock-out entries here + transfers that left from here
    outgoing = StockEntry.objects.filter(product_id=product_id).filter(
        Q(entry_type="OUT", warehouse_id=warehouse_id)
        | Q(entry_type="TRANSFER", warehouse_id=warehouse_id)
    ).aggregate(total=Sum("quantity"))["total"] or 0

    return incoming - outgoing                            # balance = in minus out


def create_entry(user, *, product, warehouse, entry_type, quantity,
                to_warehouse=None, supplier=None, remarks=""):
    # The * means everything after it MUST be passed by name, so values can't get mixed up
    _require_role(user, "Storekeeper")                    # rule 1: only a storekeeper

    with transaction.atomic():                            # rule 2: all or nothing, an error undoes the save

        # Lock the product row until this transaction ends.
        # If two people move the same product at the same time, the second waits,
        # so both can never use the same stock
        try:
            Product.objects.select_for_update().get(pk=product.pk, is_active=True)
        except Product.DoesNotExist:
            raise NotFound("Active product not found.")

        # OUT and TRANSFER take stock out of the source warehouse, so check it first
        if entry_type in ("OUT", "TRANSFER"):
            available = get_balance(product.pk, warehouse.pk)
            if quantity > available:                      # would make the stock negative
                raise ValidationError({
                    "quantity": "Not enough stock.",
                    "available_stock": available,
                    "required_quantity": quantity,
                })

        # One row is enough for a transfer: source = warehouse, destination = to_warehouse.
        # That is why a transfer is one atomic operation: nothing can be saved half-way
        entry = StockEntry.objects.create(
            product=product,
            warehouse=warehouse,
            to_warehouse=to_warehouse,
            supplier=supplier,
            entry_type=entry_type,
            quantity=quantity,
            remarks=remarks,
            created_by=user,                              # the logged-in staff member
        )
    return entry # give the saved entry back to the view

def total_balance(product_id):
    """Total stock of a product across ALL warehouses."""
    entries = StockEntry.objects.filter(product_id=product_id)
    stock_in = entries.filter(entry_type="IN").aggregate(total=Sum("quantity"))["total"] or 0
    stock_out = entries.filter(entry_type="OUT").aggregate(total=Sum("quantity"))["total"] or 0
    # A transfer only moves stock between warehouses, so the total does not change
    return stock_in - stock_out


def product_balance(product):
    """Balance per warehouse plus the total (for /products/<id>/balance/)."""
    rows = []
    total = 0
    for warehouse in Warehouse.objects.all().order_by("id"):
        balance = get_balance(product.pk, warehouse.pk)      # function from Step 5
        rows.append({
            "warehouse_id": warehouse.pk,
            "warehouse": warehouse.name,
            "balance": balance,
        })
        total += balance
    return {
        "product_id": product.pk,
        "sku": product.sku,
        "name": product.name,
        "warehouses": rows,
        "total": total,
    }


def low_stock(threshold):
    """Active products whose total stock is at or below the threshold."""
    result = []
    for product in Product.objects.filter(is_active=True).order_by("id"):
        total = total_balance(product.pk)
        if total <= threshold:
            result.append({
                "product_id": product.pk,
                "sku": product.sku,
                "name": product.name,
                "total_stock": total,
            })
    return result