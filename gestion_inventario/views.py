from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import RegistroUsuarioForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import F, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from .models import Producto, Categoria, Proveedor, MovimientoInventario, Factura, Cliente


# ---------------------------
# Autenticación
# ---------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('gestion_inventario:dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')

    return render(request, 'gestion_inventario/login.html')


def logout_view(request):
    logout(request)
    return redirect('gestion_inventario:login')


def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('gestion_inventario:dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'gestion_inventario/registrar_usuario.html', {'form': form})


# ---------------------------
# Función para verificar rol
# ---------------------------
def es_administrador(user):
    return user.is_staff


# ---------------------------
# Dashboard principal
# ---------------------------
@login_required
def dashboard(request):
    periodo = request.GET.get('periodo', 'diario')
    movimientos = MovimientoInventario.objects.all()

    if periodo == 'diario':
        stats = movimientos.annotate(periodo=TruncDay('fecha')).values('periodo').annotate(total=Sum('cantidad'))
    elif periodo == 'mensual':
        stats = movimientos.annotate(periodo=TruncMonth('fecha')).values('periodo').annotate(total=Sum('cantidad'))
    elif periodo == 'anual':
        stats = movimientos.annotate(periodo=TruncYear('fecha')).values('periodo').annotate(total=Sum('cantidad'))
    else:
        stats = []

    total_productos = Producto.objects.count()
    productos_bajo_stock = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).count()
    movimientos_recientes = MovimientoInventario.objects.order_by('-fecha')[:5]

    proveedores = Proveedor.objects.all()
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()

    filtros = [
        {'name': 'proveedor', 'items': proveedores},
        {'name': 'producto', 'items': productos},
        {'name': 'categoria', 'items': categorias},
    ]

    context = {
        'stats': stats,
        'periodo': periodo,
        'total_productos': total_productos,
        'productos_bajo_stock': productos_bajo_stock,
        'movimientos_recientes': movimientos_recientes,
        'filtros': filtros,
        'request': request,
    }
    return render(request, 'gestion_inventario/dashboard.html', context)


# ---------------------------
# Lista de productos
# ---------------------------
@login_required
def lista_productos(request):
    productos = Producto.objects.all()
    categorias = Categoria.objects.all()

    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    search = request.GET.get('search')
    if search:
        productos = productos.filter(nombre__icontains=search)

    context = {
        'productos': productos,
        'categorias': categorias,
    }
    return render(request, 'gestion_inventario/lista_productos.html', context)


# ---------------------------
# Registro de productos
# ---------------------------
@login_required
@user_passes_test(es_administrador)
def registrar_producto(request):
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        try:
            Producto.objects.create(
                codigo=request.POST['codigo'],
                nombre=request.POST['nombre'],
                categoria_id=request.POST['categoria'],
                proveedor_id=request.POST['proveedor'],
                precio=request.POST['precio'],
                stock_actual=request.POST['stock_actual'],
                stock_minimo=request.POST['stock_minimo'],
                activo='activo' in request.POST
            )
            messages.success(request, 'Producto registrado correctamente.')
            return redirect('gestion_inventario:lista_productos')
        except Exception as e:
            messages.error(request, f'Error al registrar producto: {e}')

    return render(request, 'gestion_inventario/registrar_producto.html', {
        'categorias': categorias,
        'proveedores': proveedores
    })


# ---------------------------
# Registro de movimientos
# ---------------------------
@login_required
def registrar_movimiento(request):
    productos = Producto.objects.all()
    clientes = Cliente.objects.all()

    if request.method == 'POST':
        try:
            producto_id = request.POST['producto']
            tipo = request.POST['tipo']
            cantidad = int(request.POST['cantidad'])
            motivo = request.POST['motivo']
            cliente_id = request.POST.get('cliente')

            producto = Producto.objects.get(id=producto_id)

            if tipo == 'ENTRADA':
                producto.stock_actual += cantidad
            elif tipo == 'SALIDA':
                if producto.stock_actual >= cantidad:
                    producto.stock_actual -= cantidad
                else:
                    messages.error(request, 'No hay suficiente stock para realizar la salida.')
                    return redirect('gestion_inventario:registrar_movimiento')

            producto.save()

            MovimientoInventario.objects.create(
                producto=producto,
                tipo=tipo,
                cantidad=cantidad,
                motivo=motivo,
                usuario=request.user,
                cliente=Cliente.objects.get(id=cliente_id) if cliente_id else None
            )

            messages.success(request, 'Movimiento registrado correctamente.')
            return redirect('gestion_inventario:dashboard')

        except Exception as e:
            messages.error(request, f'Error al registrar movimiento: {e}')

    return render(request, 'gestion_inventario/movimientos.html', {
        'productos': productos,
        'clientes': clientes
    })


# ---------------------------
# Historial de movimientos
# ---------------------------
@login_required
def lista_movimientos(request):
    movimientos = MovimientoInventario.objects.all().order_by('-fecha')
    productos = Producto.objects.all()

    producto_id = request.GET.get('producto')
    if producto_id:
        movimientos = movimientos.filter(producto_id=producto_id)

    tipo = request.GET.get('tipo')
    if tipo:
        movimientos = movimientos.filter(tipo=tipo)

    fecha = request.GET.get('fecha')
    if fecha:
        movimientos = movimientos.filter(fecha__date=fecha)

    context = {
        'movimientos': movimientos,
        'productos': productos,
    }
    return render(request, 'gestion_inventario/lista_movimientos.html', context)


# ---------------------------
# Proveedores
# ---------------------------
@login_required
def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'gestion_inventario/lista_proveedores.html', {
        'proveedores': proveedores
    })


@login_required
@user_passes_test(es_administrador)
def registrar_proveedor(request):
    if request.method == 'POST':
        try:
            Proveedor.objects.create(
                nombre=request.POST['nombre'],
                contacto=request.POST['contacto'],
                telefono=request.POST['telefono'],
                email=request.POST['email']
            )
            messages.success(request, 'Proveedor registrado correctamente.')
            return redirect('gestion_inventario:lista_proveedores')
        except Exception as e:
            messages.error(request, f'Error al registrar proveedor: {e}')

    return render(request, 'gestion_inventario/registrar_proveedor.html')


# ---------------------------
# Ver factura
# ---------------------------
@login_required
def ver_factura(request, factura_id):
    factura = Factura.objects.get(id=factura_id)
    return render(request, 'factura.html', {'factura': factura})

# ---------------------------
# Clientes
# ---------------------------
@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'gestion_inventario/lista_clientes.html', {'clientes': clientes})

@login_required
@user_passes_test(es_administrador)
def registrar_cliente(request):
    if request.method == 'POST':
        try:
            Cliente.objects.create(
                nombre=request.POST['nombre'],
                email=request.POST.get('email')
            )
            messages.success(request, 'Cliente registrado correctamente.')
            return redirect('gestion_inventario:lista_clientes')
        except Exception as e:
            messages.error(request, f'Error al registrar cliente: {e}')
    return render(request, 'gestion_inventario/registrar_cliente.html')


# ---------------------------
# Facturas
# ---------------------------
@login_required
def lista_facturas(request):
    facturas = Factura.objects.all().order_by('-fecha')
    return render(request, 'gestion_inventario/lista_facturas.html', {'facturas': facturas})

@login_required
def ver_factura(request, factura_id):
    factura = Factura.objects.get(id=factura_id)
    return render(request, 'gestion_inventario/ver_factura.html', {'factura': factura})