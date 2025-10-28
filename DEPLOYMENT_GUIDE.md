# Guía de Despliegue en Render - Paso a Paso

Esta guía te llevará desde cero hasta tener tu API de notificaciones funcionando en Render 100% GRATIS.

⏱️ **Tiempo estimado:** 25-35 minutos (¡Más rápido que Firebase!)  
📋 **Requisitos Previos:**
- ✅ Cuenta de GitHub
- ✅ Tu código en un repositorio de GitHub

---

## 🔔 PASO 1: Configurar OneSignal (10 min)

OneSignal es **MÁS FÁCIL** que Firebase y completamente **GRATUITO** para notificaciones ilimitadas.

### 1.1 Crear Cuenta en OneSignal
1. Ve a [app.onesignal.com](https://app.onesignal.com)
2. Click en **"Sign Up"** (o "Get Started")
3. Regístrate con Google o Email
4. **¡Listo!** (más fácil que Firebase)

### 1.2 Crear Nueva App
1. En el Dashboard, click **"New App/Website"**
2. Configuración:
   - **App Name:** `Rapido Ochoa`
   - **Platform:** Selecciona tu plataforma (Android, iOS, Web, etc.)
3. Click **"Next"**

### 1.3 Configurar SDK (Según tu plataforma)

**Para Android:**
- Descarga el archivo `google-services.json` si usas Firebase SDK
- O sigue las instrucciones de OneSignal SDK
- Click **"Save and Continue"**

**Para iOS:**
- Sube tu certificado .p12 o usa Push Certificate
- Click **"Save and Continue"**

**Para Web:**
- Solo necesitas agregar el SDK a tu sitio
- Click **"Save and Continue"**

### 1.4 Obtener API Keys ⭐ (LO MÁS IMPORTANTE)

1. Ve a **Settings** → **Keys & IDs**
2. Encontrarás 2 valores importantes:

   **📋 COPIA ESTOS DOS:**
   - **OneSignal App ID:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - **REST API Key:** `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

   Ejemplo:
```
   App ID: 12345678-1234-1234-1234-123456789012
   REST API Key: YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=
```

✅ **OneSignal configurado!** (¡Mucho más rápido que Firebase!)

---

## 🐘 PASO 2: Crear Base de Datos PostgreSQL en Render (5 min)

### 2.1 Crear Cuenta en Render
1. Ve a [render.com](https://render.com)
2. Click **"Get Started"**
3. Regístrate con **GitHub** (recomendado)

### 2.2 Crear PostgreSQL
1. En el Dashboard, click **"New +"** → **"PostgreSQL"**
2. Configuración:
   - **Name:** `rapido-ochoa-db`
   - **Database:** `rastreo_notificaciones`
   - **User:** `rastreo_user`
   - **Region:** `Oregon (US West)` - La más cercana a Colombia
   - **PostgreSQL Version:** `16`
   - **Plan:** ✅ **Free**
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

⚠️ **IMPORTANTE:** Usa la **Internal URL**, NO la External URL

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
git commit -m "Migrate to OneSignal - Initial deploy"
git remote add origin https://github.com/TU_USUARIO/rapido-ochoa-notificaciones.git
git push -u origin main
```

### 3.2 Conectar Repositorio en Render
1. En Render Dashboard, click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"**
3. Autoriza a Render a acceder a tu GitHub
4. Selecciona el repositorio `rapido-ochoa-notificaciones`

### 3.3 Configurar Web Service
- **Name:** `rapido-ochoa-notificaciones`
- **Region:** `Oregon (US West)`
- **Branch:** `main`
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Plan:** ✅ **Free**

### 3.4 Variables de Entorno ⭐ (MUY IMPORTANTE)

Scroll down a **"Environment Variables"** y agrega:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.0` |
| `DATABASE_URL` | (Pega la **Internal Database URL** del Paso 2.3) |
| `ONESIGNAL_API_KEY` | (Pega el **REST API Key** del Paso 1.4) |
| `ONESIGNAL_APP_ID` | (Pega el **App ID** del Paso 1.4) |
| `RASTREO_API_URL` | `https://rapido-ochoa-api.onrender.com/api/rastreo` |

**Ejemplo real:**
```
PYTHON_VERSION = 3.11.0
DATABASE_URL = postgresql://rastreo_user:abc123@dpg-xyz.oregon-postgres.render.com/rastreo_notificaciones
ONESIGNAL_API_KEY = YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo=
ONESIGNAL_APP_ID = 12345678-1234-1234-1234-123456789012
RASTREO_API_URL = https://rapido-ochoa-api.onrender.com/api/rastreo
```

### 3.5 Desplegar
1. Click **"Create Web Service"**
2. Render empezará a construir tu aplicación
3. Verás logs en tiempo real
4. Espera a ver: ✅ **Build successful!** y ✅ **Deploy live**

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
   - **Name:** `rapido-ochoa-verificador`
   - **Region:** `Oregon (US West)`
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Schedule:** `0 */2 * * *` (cada 2 horas)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -c "import requests; requests.post('https://rapido-ochoa-notificaciones.onrender.com/api/verificar')"`
   - **Plan:** ✅ **Free**

⚠️ **IMPORTANTE:** Reemplaza `rapido-ochoa-notificaciones` con el nombre exacto de tu Web Service si lo cambiaste.

### 4.2 Entender el Schedule
El schedule `0 */2 * * *` significa:
- `0` = minuto 0
- `*/2` = cada 2 horas
- `* * *` = todos los días, meses, días de la semana

Ejemplos de otros schedules:
- `0 * * * *` = cada hora
- `0 0 * * *` = una vez al día a medianoche
- `*/30 * * * *` = cada 30 minutos

### 4.3 Variables de Entorno (Opcional)
Si tu Cron Job necesita las mismas variables, agrégalas aquí también.

### 4.4 Guardar
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
6. Deberías ver respuesta **200** con los datos de la suscripción

### 5.2 Verificar Base de Datos
1. Ve a tu PostgreSQL en Render
2. Click en **"Connect"** → **"External Connection"**
3. Usa un cliente como TablePlus o DBeaver
4. Conecta con las credenciales mostradas
5. Deberías ver las tablas:
   - `suscripciones`
   - `historial_verificaciones`
   - `configuracion_ciudades`

### 5.3 Ver Logs
1. En tu Web Service, click en **"Logs"** (esquina superior derecha)
2. Verás logs en tiempo real de todas las operaciones

✅ **Todo funcionando correctamente!**

---

## 📱 PASO 6: Integrar con Tu App Móvil

### 6.1 Flutter + OneSignal Example

**Instalar SDK:**
```yaml
# pubspec.yaml
dependencies:
  onesignal_flutter: ^5.0.0
  http: ^1.1.0
```

**Código:**
```dart
import 'package:http/http.dart' as http;
import 'package:onesignal_flutter/onesignal_flutter.dart';
import 'dart:convert';

class RapidoOchoaAPI {
  static const String baseUrl = 'https://TU_SERVICIO.onrender.com';
  
  // Inicializar OneSignal
  static Future initOneSignal() async {
    OneSignal.initialize("TU_ONESIGNAL_APP_ID");
    await OneSignal.Notifications.requestPermission(true);
  }
  
  // Suscribirse a notificaciones
  Future suscribirseANotificaciones(String numeroGuia) async {
    // Obtener Player ID de OneSignal
    String? playerId = OneSignal.User.pushSubscription.id;
    
    if (playerId == null) {
      print('❌ No se pudo obtener Player ID de OneSignal');
      return false;
    }
    
    // Suscribirse en tu API
    final response = await http.post(
      Uri.parse('$baseUrl/api/suscribir'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'numero_guia': numeroGuia,
        'token_fcm': playerId,  // Usar Player ID de OneSignal
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

### 6.2 React Native + OneSignal Example

**Instalar SDK:**
```bash
npm install react-native-onesignal
# o
yarn add react-native-onesignal
```

**Código:**
```javascript
import OneSignal from 'react-native-onesignal';
import axios from 'axios';

// Inicializar OneSignal
OneSignal.setAppId('TU_ONESIGNAL_APP_ID');

const suscribirseANotificaciones = async (numeroGuia) => {
  try {
    // Obtener Player ID
    const deviceState = await OneSignal.getDeviceState();
    const playerId = deviceState.userId;
    
    if (!playerId) {
      console.error('❌ No se pudo obtener Player ID');
      return false;
    }
    
    // Suscribirse en tu API
    const response = await axios.post(
      'https://TU_SERVICIO.onrender.com/api/suscribir',
      {
        numero_guia: numeroGuia,
        token_fcm: playerId,  // Usar Player ID de OneSignal
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
**Solución:** Asegúrate de que `requirements.txt` esté en la raíz del repositorio.

### Problema: "Database connection failed"
**Solución:**
- Verifica que copiaste la **Internal Database URL** (no la External)
- Asegúrate de que empiece con `postgresql://` (no `postgres://`)

### Problema: "OneSignal push not sending"
**Solución:**
- Verifica el **REST API Key** y **App ID** en variables de entorno
- Asegúrate de que el Player ID del cliente sea válido
- Revisa los logs de OneSignal Dashboard para ver errores

### Problema: "Service keeps sleeping"
**Respuesta:** Es normal en el plan Free. El Cron Job lo despierta cada 2 horas automáticamente.

### Problema: "Cannot import module 'psycopg2'"
**Solución:** En `requirements.txt`, asegúrate de usar `psycopg2-binary` (no solo `psycopg2`)

---

## 🎓 Recursos Adicionales

- [Documentación de Render](https://render.com/docs)
- [OneSignal Docs](https://documentation.onesignal.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)

---

## ✅ Checklist Final

- [ ] OneSignal configurado y API Keys copiadas
- [ ] PostgreSQL creado en Render
- [ ] API desplegada y respondiendo
- [ ] Cron Job programado
- [ ] Pruebas exitosas con Swagger
- [ ] App móvil integrada con OneSignal SDK
- [ ] Logs monitoreados

---

## 🎉 ¡Felicidades!

Tu sistema de notificaciones inteligentes está funcionando al 100% con:
- ✅ OneSignal (más fácil que Firebase)
- ✅ PostgreSQL gratis en Render
- ✅ Verificación automática cada 2 horas
- ✅ Notificaciones push cuando las guías lleguen

**Todo GRATIS y funcionando 24/7** 🚀

## 🎉 ¡Felicidades!

Tu sistema de notificaciones inteligentes está funcionando. Ahora tus usuarios recibirán notificaciones push automáticas cuando sus encomiendas lleguen a destino, sin desperdiciar recursos en verificaciones innecesarias.

**¿Preguntas?** Abre un issue en GitHub.

---

**Última actualización**: Octubre 2025