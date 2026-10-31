from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser, UserManager # base classes for custom user                                       # tools to define tables
from django.db.models import Q # used to write conditions for constraints


class Role(models.Model):    # one row per role: Manager, Storekeeper
    roleid = models.AutoField(primary_key=True)   # auto-numbered id (1, 2, 3...)
    title = models.CharField(max_length=50, unique=True) # role name; unique = no duplicate roles

    def __str__(self):    # text shown in the admin site
        return self.title 


class StaffManager(UserManager):   # controls how users are created
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # get_or_create = find the "Manager" role, or create it if missing
        role, _ = Role.objects.get_or_create(title="Manager")

        extra_fields["roleid"] = role                      # every superuser gets the Manager role
        extra_fields.setdefault("is_staff", True)          # can open the admin site
        extra_fields.setdefault("is_superuser", True)      # has all permissions

        return super().create_superuser(                   # let Django finish creating the user
            username=username, email=email, password=password, **extra_fields
        )



class Staff(AbstractUser):                                 # AbstractUser already has username, password, email
    first_name = None                                      # remove Django's first_name (we use full_name)
    last_name = None                                       # remove Django's last_name

    roleid = models.ForeignKey(                            # each staff member has exactly one role
        Role,
        on_delete=models.PROTECT,                          # a role that is in use cannot be deleted
        related_name="staff",                              # role.staff gives all staff of that role
    )
    full_name = models.CharField(max_length=20)           # the person's name
    phone = models.CharField(max_length=15)                # contact number

    REQUIRED_FIELDS = ["email", "full_name", "phone"]      # fields asked by "createsuperuser"
    objects = StaffManager()                               # use our manager defined above

    def __str__(self):
        return self.full_name



class Supplier(models.Model):                              # company that sends us goods
    name = models.CharField(max_length=50)                # supplier name
    phone = models.CharField(max_length=15, blank=True)    # blank=True = this field is optional
    is_active = models.BooleanField(default=True)          # soft delete flag (False = hidden)

    def __str__(self):
        return self.name


class Product(models.Model):                               # an item we store
    name = models.CharField(max_length=50)                # product name
    sku = models.CharField(max_length=30, unique=True)     # product code; unique = no two share a code
    is_active = models.BooleanField(default=True)          # soft delete flag

    def __str__(self):
        return f"{self.sku} - {self.name}"                 # example: "PEN01 - Blue Pen"


class Warehouse(models.Model):                             # a place where stock is kept
    name = models.CharField(max_length=50, unique=True)   # warehouse name must be unique
    location = models.CharField(max_length=50, blank=True)  # optional address

    def __str__(self):
        return self.name


class StockEntry(models.Model):   # one row per stock movement
    ENTRY_TYPES = [
        ("IN", "Stock In"), # goods arrive
        ("OUT", "Stock Out"),  # goods leave
        ("TRANSFER", "Transfer"), # goods move between warehouses
    ]

    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="entries"
    )    # which product moved; PROTECT keeps history safe

    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="entries"
    )   # IN/OUT: the warehouse affected. TRANSFER: the SOURCE

    to_warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="incoming_transfers",
        null=True, blank=True,  # only used by TRANSFER, so it may be empty
    )   # TRANSFER: the DESTINATION warehouse

    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="entries",
        null=True, blank=True,  # only used by IN, so it may be empty
    )

    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)   # IN, OUT or TRANSFER
    quantity = models.PositiveIntegerField()               # never accepts a negative number
    remarks = models.CharField(max_length=200, blank=True) # optional note

    created_by = models.ForeignKey(
        Staff, on_delete=models.PROTECT, related_name="stock_entries"
    )                                                      # which staff member made the entry
    created_on = models.DateTimeField(auto_now_add=True)   # filled automatically when the row is created

    class Meta:
        indexes = [
            # Makes searching by product and warehouse faster (used by balance and ledger)
            models.Index(fields=["product", "warehouse"], name="idx_entry_product_wh"),
            models.Index(fields=["created_on"], name="idx_entry_created_on"),
        ]
        constraints = [
            # Database rule: quantity must be greater than 0
            # (quantity__gt=0 means "quantity greater than 0")
            models.CheckConstraint(
                condition=Q(quantity__gt=0), name="chk_entry_qty_positive"
            ),
        ]

    def __str__(self):
        return f"{self.entry_type} {self.quantity} x {self.product.sku}"