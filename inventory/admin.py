from django.contrib import admin

# Register your models here.
from django.contrib import admin      # Django's built-in admin site tools
from .models import Role, Staff, Supplier, Product, Warehouse, StockEntry
# the dot in ".models" means "the models.py in this same folder"

# register() puts each table on the admin website so we can view and edit rows
admin.site.register(Role)
admin.site.register(Staff)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(Warehouse)
admin.site.register(StockEntry)