# 📦 Guía de Despliegue en Render - Paso a Paso

Esta guía te llevará desde cero hasta tener tu API de notificaciones funcionando en Render **100% GRATIS**.

## ⏱️ Tiempo estimado: 30-45 minutos

---

## 📋 Requisitos Previos

- [ ] Cuenta de GitHub
- [ ] Cuenta de Google (para Firebase)
- [ ] Tu código en un repositorio de GitHub

---

## 🔥 PASO 1: Configurar Firebase Cloud Messaging (15 min)

Firebase es completamente gratuito para notificaciones push ilimitadas.

### 1.1 Crear Proyecto en Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com)
2. Click en **"Agregar proyecto"**
3. Nombre del proyecto: `rapido-ochoa-notif`
4. Desactiva Google Analytics (no lo necesitas)
5. Click **"Crear proyecto"**

### 1.2 Agregar Aplicación

1. En la página principal del proyecto, click en **ícono de Android** (o iOS/Web según tu app)
2. Sigue el asistente:
   - Package name: `com.tuempresa.rapidoochoa`
   - App nickname: `Rapido Ochoa`
3. Descarga el archivo `google-services.json` (guárdalo para tu app móvil)
4. Click **"Continuar"** hasta terminar

### 1.3 Obtener Server Key

1. En Firebase Console, click en el **⚙️ (engranaje)** → **"Configuración del proyecto"**
2. Ve a la pestaña **"Cloud Messaging"**
3. En la sección **"API de Cloud Messaging (heredada)"**, verás el **Server key**
4. 📋 **COPIA ESTE KEY** - Lo necesitarás en el Paso 3

Ejemplo:
```
AAAAxxxxxxx:APA91bHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

✅ **Firebase configurado!**

---

## 🐘 PASO 2: Crear Base de Datos PostgreSQL en Render (5 min)

### 2.1 Crear Cuenta en Render

1. Ve a [render.com](https://render.com)
2. Click **"Get Started"**
3. Regístrate con GitHub (recomendado)

### 2.2 Crear PostgreSQL

1. En el Dashboard, click **"New +"** → **"PostgreSQL"**
2. Configuración:
```
   Name: rapido-ochoa-db
   Database: rastreo_notificaciones
   User: rastreo_user
   Region: Oregon (US West) - La más cercana a Colombia
   PostgreSQL Version: 16
   Plan: Free
```
3. Click **"Create Database"**
4. Espera 2-3 minutos mientras se crea

### 2.3 Copiar Connection String

1. Una vez creada, verás la página de la base de datos
2. En la sección **"Connections"**, busca **"Internal Database URL"**
3. 📋 **COPIA ESTA URL COMPLETA** - La necesitarás en el siguiente paso

Ejemplo:
```
postgresql://rastreo_user:xxxxx@dpg-xxxxx.oregon-postgres.render.com/rastreo_notificaciones
```

⚠️ **IMPORTANTE**: Usa la **Internal URL**, NO la External URL

✅ **Base de datos creada!**

---

## 🚀 PASO 3: Desplegar API Principal (10 min)

### 3.1 Subir Código a GitHub

Si aún no lo has hecho:
```bash
# En tu carpeta del proyecto
cd pushrapido8a
git init
git add .
git commit -m "Initial commit - API de notificaciones"
git remote add origin https://github.com/TU_USUARIO/rapido-ochoa-notificaciones.git
git push -u origin main
```

### 3.2 Conectar Repositorio en Render

1. En Render Dashboard, click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"**
3. Autoriza a Render a acceder a tu GitHub
4. Selecciona el repositorio `rapido-ochoa-notificaciones`

### 3.3 Configurar Web Service
```
Name: rapido-ochoa-notificaciones
Region: Oregon (US West)
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Plan: Free
```

### 3.4 Variables de Entorno

Scroll down a **"Environment Variables"** y agrega:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.0` |
| `DATABASE_URL` | *(Pega la Internal Database URL del Paso 2.3)* |
| `FIREBASE_SERVER_KEY` | *(Pega el Server Key del Paso 1.3)* |
| `RASTREO_API_URL` | `https://rapido-ochoa-api.onrender.com/api/rastreo` |

### 3.5 Desplegar

1. Click **"Create Web Service"**
2. Render empezará a construir tu aplicación
3. Verás logs en tiempo real
4. Espera a ver: `✅ Build successful!` y `✅ Deploy live`

### 3.6 Verificar Funcionamiento

Una vez desplegado, abre:
```
https://rapido-ochoa-notificaciones.onrender.com/docs
```

Deberías ver la documentación interactiva de FastAPI (Swagger UI).

✅ **API desplegada y funcionando!**

---

## ⏰ PASO 4: Crear Cron Job (Verificador Automático) (5 min)

Este job verificará las guías cada 2 horas automáticamente.

### 4.1 Crear Cron Job

1. En Render Dashboard, click **"New +"** → **"Cron Job"**
2. Conecta el mismo repositorio de GitHub
3. Configuración:
```
   Name: rapido-ochoa-verificador
   Region: Oregon (US West)
   Branch: main
   Runtime: Python 3
   Schedule: 0 */2 * * *
   Build Command: pip install -r requirements.txt
   Start Command: python -c "import requests; requests.post('https://rapido-ochoa-notificaciones.onrender.com/api/verificar')"
   Plan: Free
```

⚠️ **IMPORTANTE**: Reemplaza `rapido-ochoa-notificaciones` con el nombre exacto de tu Web Service si lo cambiaste.

### 4.2 Entender el Schedule

El schedule `0 */2 * * *` significa:
- `0` = minuto 0
- `*/2` = cada 2 horas
- `* * *` = todos los días, meses, días de la semana

Ejemplos de otros schedules:
- `0 * * * *` = cada hora
- `0 0 * * *` = una vez al día a medianoche
- `*/30 * * * *` = cada 30 minutos

### 4.3 Guardar

Click **"Create Cron Job"**

✅ **Cron Job configurado!**

---

## 🧪 PASO 5: Probar el Sistema (5 min)

### 5.1 Usando Swagger UI

1. Abre `https://TU_SERVICIO.onrender.com/docs`
2. Expande **POST /api/suscribir**
3. Click **"Try it out"**
4. Pega este JSON:
```json
   {
     "numero_guia": "E121101188",
     "token_fcm": "token_prueba_12345",
     "telefono": "+573001234567"
   }
```
5. Click **"Execute"**
6. Deberías ver respuesta 200 con los datos de la suscripción

### 5.2 Verificar Base de Datos

1. Ve a tu PostgreSQL en Render
2. Click en **"Connect"** → **"External Connection"**
3. Usa un cliente como [TablePlus](https://tableplus.com) o [DBeaver](https://dbeaver.io)
4. Conecta con las credenciales mostradas
5. Deberías ver las tablas: `suscripciones`, `historial_verificaciones`, `configuracion_ciudades`

### 5.3 Ver Logs

1. En tu Web Service, click en **"Logs"** (esquina superior derecha)
2. Verás logs en tiempo real de todas las operaciones

✅ **Todo funcionando correctamente!**

---

## 📱 PASO 6: Integrar con Tu App Móvil

### 6.1 Flutter Example
```dart
import 'package:http/http.dart' as http;
import 'package:firebase_messaging/firebase_messaging.dart';
import 'dart:convert';

class RapidoOchoaAPI {
  static const String baseUrl = 'https://TU_SERVICIO.onrender.com';
  
  Future<bool> suscribirseANotificaciones(String numeroGuia) async {
    // Obtener token FCM
    String? token = await FirebaseMessaging.instance.getToken();
    
    if (token == null) {
      print('❌ No se pudo obtener token FCM');
      return false;
    }
    
    // Suscribirse
    final response = await http.post(
      Uri.parse('$baseUrl/api/suscribir'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'numero_guia': numeroGuia,
        'token_fcm': token,
      }),
    );
    
    if (response.statusCode == 200) {
      print('✅ Suscrito a notificaciones');
      return true;
    } else {
      print('❌ Error: ${response.body}');
      return false;
    }
  }
}
```

### 6.2 React Native Example
```javascript
import messaging from '@react-native-firebase/messaging';
import axios from 'axios';

const suscribirseANotificaciones = async (numeroGuia) => {
  try {
    // Obtener token
    const token = await messaging().getToken();
    
    // Suscribirse
    const response = await axios.post(
      'https://TU_SERVICIO.onrender.com/api/suscribir',
      {
        numero_guia: numeroGuia,
        token_fcm: token,
      }
    );
    
    console.log('✅ Suscrito:', response.data);
    return true;
  } catch (error) {
    console.error('❌ Error:', error);
    return false;
  }
};
```

---

## 🔍 PASO 7: Monitoreo y Mantenimiento

### 7.1 Ver Estadísticas
```bash
curl https://TU_SERVICIO.onrender.com/api/stats
```

### 7.2 Verificar Cron Job

1. En tu Cron Job en Render, ve a **"Logs"**
2. Deberías ver ejecuciones cada 2 horas con mensajes como:
```
   ✅ Verificación completada:
      - Verificadas: 15
      - Notificaciones enviadas: 3
```

### 7.3 Alertas por Email

Render puede enviarte alertas automáticas:
1. Ve a tu Web Service → **"Settings"**
2. Scroll a **"Deploy Notifications"**
3. Activa notificaciones por email

---

## ⚠️ Solución de Problemas Comunes

### Problema: "Build failed - requirements.txt not found"

**Solución**: Asegúrate de que `requirements.txt` esté en la raíz del repositorio.

### Problema: "Database connection failed"

**Solución**: 
1. Verifica que copiaste la **Internal Database URL** (no la External)
2. Asegúrate de que empiece con `postgresql://` (no `postgres://`)

### Problema: "Firebase push not sending"

**Solución**:
1. Verifica el Server Key en variables de entorno
2. Asegúrate de que el token FCM del cliente sea válido y actual

### Problema: "Service keeps sleeping"

**Respuesta**: Es normal en el plan Free. El Cron Job lo despierta cada 2 horas automáticamente.

### Problema: "Cannot import module 'psycopg2'"

**Solución**: En `requirements.txt`, asegúrate de usar `psycopg2-binary` (no solo `psycopg2`)

---

## 🎓 Recursos Adicionales

- [Documentación de Render](https://render.com/docs)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)

---

## ✅ Checklist Final

- [ ] Firebase configurado y Server Key copiado
- [ ] PostgreSQL creado en Render
- [ ] API desplegada y respondiendo
- [ ] Cron Job programado
- [ ] Pruebas exitosas con Swagger
- [ ] App móvil integrada
- [ ] Logs monitoreados

---

## 🎉 ¡Felicidades!

Tu sistema de notificaciones inteligentes está funcionando. Ahora tus usuarios recibirán notificaciones push automáticas cuando sus encomiendas lleguen a destino, sin desperdiciar recursos en verificaciones innecesarias.

**¿Preguntas?** Abre un issue en GitHub.

---

**Última actualización**: Octubre 2025