from django.urls import path
from . import views

app_name = 'gestion_inventario'

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registrar/', views.registrar_usuario, name='registrar_usuario'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Productos
    path('productos/', views.lista_productos, name='lista_productos'),
    path('registrar-producto/', views.registrar_producto, name='registrar_producto'),

    # Movimientos
    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('registrar-movimiento/', views.registrar_movimiento, name='registrar_movimiento'),

    # Proveedores
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('registrar-proveedor/', views.registrar_proveedor, name='registrar_proveedor'),

    # Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('registrar-cliente/', views.registrar_cliente, name='registrar_cliente'),

    # Facturas
    path('facturas/', views.lista_facturas, name='lista_facturas'),
    path('factura/<int:factura_id>/', views.ver_factura, name='ver_factura'),
]