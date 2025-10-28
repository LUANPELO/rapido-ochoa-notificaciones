# 📦 API de Rastreo Rápido Ochoa - Sistema de Notificaciones

API REST ultra rápida para notificaciones push de trazabilidad de Rápido Ochoa. Sistema inteligente que optimiza verificaciones según distancia entre ciudades.

## 🚀 Características

- ✅ **Verificación Inteligente**: Calcula cuándo verificar según distancia (ahorra 75% de recursos)
- ⚡ **PostgreSQL Persistente**: Datos que nunca se pierden
- 🔔 **Firebase Push Notifications**: Notificaciones ilimitadas GRATIS
- 📊 **100+ Rutas**: Solo ciudades que opera Rápido Ochoa
- 🧹 **Auto-limpieza**: Elimina registros antiguos automáticamente
- 💰 **100% Gratis**: Soporta hasta 800-1,000 requests/día sin pagar

## 📋 Requisitos

- Python 3.11.0
- PostgreSQL
- Firebase Cloud Messaging

## 🛠️ Instalación Local

### 1. Clonar repositorio
```bash
git clone https://github.com/TU_USUARIO/rapido-ochoa-notificaciones.git
cd rapido-ochoa-notificaciones
```

### 2. Crear entorno virtual
```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno

Copia `.env.example` a `.env` y completa los valores:
```bash
cp .env.example .env
# Edita .env con tus credenciales
```

### 6. Iniciar servidor
```bash
python main.py
```

El servidor estará disponible en: `http://127.0.0.1:8000`

### 7. Documentación interactiva

Abre tu navegador en: `http://127.0.0.1:8000/docs`

## 🌐 Despliegue en Render

Sigue la guía paso a paso en **DEPLOYMENT_GUIDE.md**

Tiempo estimado: 30-40 minutos

## 📡 Endpoints

### 1. Suscribir a notificaciones
```http
POST /api/suscribir
Content-Type: application/json

{
  "numero_guia": "E121101188",
  "token_fcm": "token_firebase_del_dispositivo",
  "telefono": "+573001234567"
}
```

**Respuesta:**
```json
{
  "id": 1,
  "numero_guia": "E121101188",
  "estado_actual": "GUIA ELABORADA",
  "origen": "MEDELLIN (ANTIOQUIA)",
  "destino": "BARRANQUILLA (ATLANTICO)",
  "fecha_creacion": "2025-10-25T10:30:00",
  "activo": true,
  "proxima_verificacion": "2025-10-25T22:30:00"
}
```

### 2. Consultar estado de suscripción
```http
GET /api/suscripcion/{numero_guia}
```

### 3. Cancelar suscripción
```http
DELETE /api/suscripcion/{numero_guia}
```

### 4. Ver estadísticas
```http
GET /api/stats
```

### 5. Health check
```http
GET /api/health
```

## 🧠 Sistema de Verificación Inteligente

### ❌ Sin Optimización
```
Guía: Medellín → Barranquilla (16 horas)
Verificaciones: Cada 1 hora = 16 requests
```

### ✅ Con Optimización
```
Guía: Medellín → Barranquilla (16 horas)

1. Espera detectar "DESPACHO DE BUSES"
2. Primera verificación: 12.8 horas después (80% del tiempo)
3. Luego cada 2 horas hasta "RECLAME EN OFICINA"
4. Total: 3-4 verificaciones

AHORRO: 75% menos requests ⚡
```

## 🗺️ Ciudades Cubiertas

### Costa Atlántica
Barranquilla, Cartagena, Santa Marta, Sincelejo, Montería, Valledupar, Riohacha, Maicao, Tolú, Coveñas

### Antioquia
Medellín, Caucasia, Puerto Berrío, Jardín, Urrao, Giraldo, Betulia, Arboletes

### Centro
Bogotá, Bucaramanga, Pereira, Aguachica

### Pacífico
Cali, Quibdó

**Total: 60+ rutas con tiempos reales**

## 🧪 Pruebas

Ejecuta el script de pruebas:
```bash
python test_api.py
```

## 📊 Capacidad

Con **400 requests/día** en Render Free:

| Recurso | Uso | Límite | Estado |
|---------|-----|--------|--------|
| Horas activas | 420h/mes | 750h/mes | ✅ 56% |
| Bandwidth | 12 MB/mes | 100 GB/mes | ✅ 0.012% |
| Base de datos | 8 MB | 500 MB | ✅ 1.6% |

**Veredicto: PERFECTO para Render Free** 🎉

## 📱 Integración con App Móvil

### Flutter Example
```dart
import 'package:http/http.dart' as http;
import 'package:firebase_messaging/firebase_messaging.dart';
import 'dart:convert';

Future<void> suscribirseANotificaciones(String numeroGuia) async {
  // Obtener token de Firebase
  String? token = await FirebaseMessaging.instance.getToken();
  
  // Suscribirse a la API
  final response = await http.post(
    Uri.parse('https://tu-api.onrender.com/api/suscribir'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'numero_guia': numeroGuia,
      'token_fcm': token,
    }),
  );
  
  if (response.statusCode == 200) {
    print('✅ Suscrito exitosamente');
  }
}
```

### React Native Example
```javascript
import messaging from '@react-native-firebase/messaging';
import axios from 'axios';

const suscribirse = async (numeroGuia) => {
  const token = await messaging().getToken();
  
  await axios.post('https://tu-api.onrender.com/api/suscribir', {
    numero_guia: numeroGuia,
    token_fcm: token,
  });
};
```

## 🔧 Configuración

### Variables de Entorno
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
FIREBASE_SERVER_KEY=AAAAxxxxxxx:APA91bHxxxxxxx
RASTREO_API_URL=https://rapido-ochoa-api.onrender.com/api/rastreo
```

### Tiempos de Verificación

Puedes ajustar en `config.py`:
```python
HORAS_ANTES_LLEGADA = 3  # Primera verificación
HORAS_ENTRE_VERIFICACIONES = 2  # Verificaciones subsiguientes
HORAS_LIMPIEZA_DESPUES_ENTREGA = 48  # Limpieza automática
```

## 🐛 Solución de Problemas

### Error: "Connection to database failed"
- Verifica que `DATABASE_URL` esté configurado correctamente
- Usa la **Internal Database URL** de Render (no la External)

### Error: "Firebase push failed"
- Verifica `FIREBASE_SERVER_KEY` en variables de entorno
- Confirma que el token FCM del cliente sea válido

### Servicio se queda "dormido"
- Es normal en Render Free
- El Cron Job lo despierta automáticamente cada 2 horas

## 💰 Costos

| Servicio | Plan | Costo |
|----------|------|-------|
| Render Web Service | Free | $0 |
| PostgreSQL | Free | $0 |
| Cron Jobs | Free | $0 |
| Firebase FCM | Free | $0 |
| **TOTAL** | | **$0/mes** |

## 📄 Documentación Adicional

- **DEPLOYMENT_GUIDE.md**: Guía paso a paso para desplegar en Render
- **RESUMEN_COMPLETO.md**: Guía rápida del proyecto
- **CALCULOS_TECNICOS.md**: Análisis detallado de capacidad

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - Puedes usar este código libremente

## 📞 Soporte

- Issues: [GitHub Issues](https://github.com/TU_USUARIO/rapido-ochoa-notificaciones/issues)
- Email: tu_email@example.com

---

**Desarrollado con ❤️ para optimizar el rastreo de Rápido Ochoa**