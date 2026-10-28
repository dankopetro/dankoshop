python3 -c "
import requests
from datetime import datetime

order = {
    'id': f'TEST-{datetime.now().strftime(\"%Y%m%d%H%M%S\")}',
    'fecha': datetime.now().strftime('%d/%m/%Y %H:%M'),
    'estado': 'pendiente',
    'metodo_pago': 'transferencia',
    'cliente': {
        'nombre': 'Prueba Telegram',
        'email': 'prueba@dankoshop.com.ar',
        'telefono': '221-0000000',
        'dni': '00000000',
        'direccion': 'Calle de Prueba 123',
        'ciudad': 'La Plata',
        'provincia': 'Buenos Aires',
        'metodo_envio': 'envio',
        'zona_envio': 'laplata',
        'velocidad_envio': 'estandar',
    },
    'items': [
        {'sku': '4853', 'name': 'Tostadora Vitta Verde Doble', 'price': 21588, 'quantity': 1, 'price_lista': 23465},
    ],
    'subtotal': 21588,
    'envio': 0,
    'total': 21588,
}

r = requests.post('https://dankoshop.com.ar/api/ordenes',
                   json={'order': order},
                   headers={'Content-Type': 'application/json'},
                   timeout=30)
print(f'Status: {r.status_code} | id: {order[\"id\"]}')
"

