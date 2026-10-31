from django.core.management.base import BaseCommand   # base class for every custom command
from inventory.models import Role, Staff, Supplier, Product, Warehouse


def make_staff(username, role, full_name, phone, is_admin=False):
    # If this username already exists, return it instead of creating a duplicate
    if Staff.objects.filter(username=username).exists():
        return Staff.objects.get(username=username)

    # create_user hashes the password for us, so it is never saved as plain text
    return Staff.objects.create_user(
        username=username,
        password="Test@1234",              # same test password for everyone
        email=f"{username}@inventory.com", # example: manager1@inventory.com
        roleid=role,                       # the Role object we pass in
        full_name=full_name,
        phone=phone,
        is_staff=is_admin,                 # True = can log in to the admin website
        is_superuser=is_admin,             # True = has all permissions there
    )


class Command(BaseCommand):                # Django runs the handle() method below
    help = "Create dummy roles, staff, products, warehouses and suppliers"

    def handle(self, *args, **options):
        # Roles: get_or_create finds the row, or creates it if missing
        manager_role, _ = Role.objects.get_or_create(title="Manager")
        store_role, _ = Role.objects.get_or_create(title="Storekeeper")

        # Staff: one manager (also admin-site user) and one storekeeper
        make_staff("manager1", manager_role, "Meera Manager", "9000000001", is_admin=True)
        make_staff("store1", store_role, "Sam Storekeeper", "9000000002")

        # Warehouses
        Warehouse.objects.get_or_create(name="Main Warehouse", defaults={"location": "Kochi"})
        Warehouse.objects.get_or_create(name="Second Warehouse", defaults={"location": "Trivandrum"})

        # Products: the sku must be unique
        Product.objects.get_or_create(sku="PEN01", defaults={"name": "Blue Pen"})
        Product.objects.get_or_create(sku="BOOK01", defaults={"name": "Notebook"})
        Product.objects.get_or_create(sku="BAG01", defaults={"name": "School Bag"})

        # Suppliers
        Supplier.objects.get_or_create(name="ABC Traders", defaults={"phone": "9111111111"})

        # Prints a green success message in the terminal
        self.stdout.write(self.style.SUCCESS("Dummy data ready. Password for all: Test@1234"))