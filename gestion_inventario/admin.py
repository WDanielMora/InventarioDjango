from django.contrib import admin
from .models import Proveedor, Producto, MovimientoInventario
from .models import Cliente, Factura, ItemFactura
from django.contrib.auth.models import User

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'contacto', 'telefono', 'email']
    search_fields = ['nombre', 'contacto']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'proveedor', 'precio', 'stock_actual', 'stock_minimo', 'alerta_stock']
    search_fields = ['codigo', 'nombre']
    list_editable = ['stock_actual', 'stock_minimo']

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ['producto', 'tipo', 'cantidad', 'motivo', 'fecha', 'usuario']
    list_filter = ['tipo', 'fecha']
    date_hierarchy = 'fecha'
    
    # Esto asegura que el usuario se asigne automáticamente
    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)

admin.site.register(Cliente)
admin.site.register(Factura)
admin.site.register(ItemFactura)
