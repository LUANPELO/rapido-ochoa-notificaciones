"""
API REST para notificaciones de trazabilidad - Rápido Ochoa
Sistema inteligente de seguimiento con verificaciones optimizadas
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import os

from database import SessionLocal, init_db, Suscripcion, HistorialVerificacion
from config import TIEMPOS_VIAJE, CIUDADES_NORMALIZE
from utils import consultar_guia_rastreo, enviar_push_notification, calcular_proxima_verificacion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Notificaciones Rápido Ochoa",
    description="Sistema inteligente de notificaciones push para trazabilidad",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de Request/Response
class SuscripcionCreate(BaseModel):
    numero_guia: str
    onesignal_user_id: str
    token_fcm: Optional[str] = None
    telefono: Optional[str] = None

class SuscripcionResponse(BaseModel):
    id: int
    numero_guia: str
    estado_actual: Optional[str]
    origen: Optional[str]
    destino: Optional[str]
    fecha_creacion: datetime
    activo: bool
    proxima_verificacion: Optional[datetime]

class EstadisticasResponse(BaseModel):
    total_suscripciones: int
    activas: int
    completadas: int
    verificaciones_pendientes: int

# Inicializar BD al arrancar
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando API de Notificaciones...")
    init_db()
    logger.info("✅ Base de datos inicializada")

# ============ ENDPOINTS PRINCIPALES ============

@app.get("/")
def root():
    return {
        "servicio": "API Notificaciones Rápido Ochoa",
        "version": "1.0.0",
        "descripcion": "Sistema inteligente de notificaciones push",
        "caracteristicas": [
            "Verificación optimizada por distancia",
            "PostgreSQL persistente",
            "OneSignal Push Notifications",
            "Limpieza automática"
        ],
        "endpoints": {
            "suscribirse": "POST /api/suscribir",
            "estado": "GET /api/suscripcion/{guia}",
            "verificar": "POST /api/verificar (Cron Job)",
            "estadisticas": "GET /api/stats"
        }
    }

@app.post("/api/suscribir", response_model=SuscripcionResponse)
async def suscribir_guia(data: SuscripcionCreate, background_tasks: BackgroundTasks):
    """
    Suscribe un cliente a las notificaciones de una guía
    
    Body:
    {
        "numero_guia": "E121101188",
        "onesignal_user_id": "uuid-del-usuario-onesignal",
        "token_fcm": "token_firebase" (opcional),
        "telefono": "+573001234567" (opcional)
    }
    """
    db = SessionLocal()
    
    try:
        logger.info(f"📦 Nueva suscripción: {data.numero_guia}")
        
        # Verificar si ya existe suscripción activa para este usuario y guía
        suscripcion_existente = db.query(Suscripcion).filter(
            Suscripcion.numero_guia == data.numero_guia,
            Suscripcion.onesignal_user_id == data.onesignal_user_id,
            Suscripcion.activo == True
        ).first()
        
        if suscripcion_existente:
            logger.info(f"⚠️ Suscripción ya existe para {data.numero_guia}")
            return SuscripcionResponse(
                id=suscripcion_existente.id,
                numero_guia=suscripcion_existente.numero_guia,
                estado_actual=suscripcion_existente.estado_actual,
                origen=suscripcion_existente.origen,
                destino=suscripcion_existente.destino,
                fecha_creacion=suscripcion_existente.fecha_creacion,
                activo=suscripcion_existente.activo,
                proxima_verificacion=suscripcion_existente.proxima_verificacion
            )
        
        # Consultar información inicial de la guía
        logger.info(f"🔍 Consultando información inicial de {data.numero_guia}")
        info_guia = consultar_guia_rastreo(data.numero_guia)
        
        if not info_guia:
            raise HTTPException(status_code=404, detail=f"No se encontró la guía {data.numero_guia}")
        
        # Crear suscripción
        nueva_suscripcion = Suscripcion(
            numero_guia=data.numero_guia,
            onesignal_user_id=data.onesignal_user_id,
            token_fcm=data.token_fcm,
            telefono=data.telefono,
            origen=info_guia.get('origen'),
            destino=info_guia.get('destino'),
            estado_actual=info_guia.get('estado_actual'),
            fecha_admision=info_guia.get('fecha_admision'),
            remitente=info_guia.get('remitente_nombre'),
            destinatario=info_guia.get('destinatario_nombre')
        )
        
        # Calcular próxima verificación
        proxima = calcular_proxima_verificacion(
            estado_actual=nueva_suscripcion.estado_actual,
            origen=nueva_suscripcion.origen,
            destino=nueva_suscripcion.destino,
            fecha_admision=nueva_suscripcion.fecha_admision
        )
        nueva_suscripcion.proxima_verificacion = proxima
        
        db.add(nueva_suscripcion)
        db.commit()
        db.refresh(nueva_suscripcion)
        
        logger.info(f"✅ Suscripción creada: ID {nueva_suscripcion.id}")
        logger.info(f"📅 Próxima verificación: {proxima}")
        
        return SuscripcionResponse(
            id=nueva_suscripcion.id,
            numero_guia=nueva_suscripcion.numero_guia,
            estado_actual=nueva_suscripcion.estado_actual,
            origen=nueva_suscripcion.origen,
            destino=nueva_suscripcion.destino,
            fecha_creacion=nueva_suscripcion.fecha_creacion,
            activo=nueva_suscripcion.activo,
            proxima_verificacion=nueva_suscripcion.proxima_verificacion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando suscripción: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/suscripcion/{numero_guia}", response_model=SuscripcionResponse)
def obtener_estado_suscripcion(numero_guia: str):
    """Consulta el estado actual de una suscripción"""
    db = SessionLocal()
    
    try:
        suscripcion = db.query(Suscripcion).filter(
            Suscripcion.numero_guia == numero_guia,
            Suscripcion.activo == True
        ).first()
        
        if not suscripcion:
            raise HTTPException(status_code=404, detail="No se encontró suscripción activa para esta guía")
        
        return SuscripcionResponse(
            id=suscripcion.id,
            numero_guia=suscripcion.numero_guia,
            estado_actual=suscripcion.estado_actual,
            origen=suscripcion.origen,
            destino=suscripcion.destino,
            fecha_creacion=suscripcion.fecha_creacion,
            activo=suscripcion.activo,
            proxima_verificacion=suscripcion.proxima_verificacion
        )
        
    finally:
        db.close()

@app.delete("/api/suscripcion/{numero_guia}")
def cancelar_suscripcion(numero_guia: str):
    """Cancela una suscripción activa"""
    db = SessionLocal()
    
    try:
        suscripcion = db.query(Suscripcion).filter(
            Suscripcion.numero_guia == numero_guia,
            Suscripcion.activo == True
        ).first()
        
        if not suscripcion:
            raise HTTPException(status_code=404, detail="No se encontró suscripción activa")
        
        suscripcion.activo = False
        db.commit()
        
        logger.info(f"🗑️ Suscripción cancelada: {numero_guia}")
        
        return {"mensaje": "Suscripción cancelada exitosamente"}
        
    finally:
        db.close()

# ============ ENDPOINT PARA CRON JOB ============

@app.post("/api/verificar")
async def verificar_guias(background_tasks: BackgroundTasks):
    """
    Endpoint ejecutado por Render Cron Job cada 2 horas
    Verifica las guías que requieren actualización
    """
    db = SessionLocal()
    
    try:
        ahora = datetime.now()
        logger.info(f"⏰ Iniciando verificación de guías: {ahora}")
        
        # Obtener suscripciones que necesitan verificación
        suscripciones = db.query(Suscripcion).filter(
            Suscripcion.activo == True,
            Suscripcion.proxima_verificacion <= ahora
        ).all()
        
        logger.info(f"📋 Guías a verificar: {len(suscripciones)}")
        
        verificadas = 0
        notificaciones_enviadas = 0
        errores_timeout = 0
        
        for suscripcion in suscripciones:
            try:
                # Consultar estado actual
                info_guia = consultar_guia_rastreo(suscripcion.numero_guia)
                
                if not info_guia:
                    logger.warning(f"⚠️ No se pudo consultar guía {suscripcion.numero_guia}")
                    # ✅ Programar reintento en 1 hora
                    suscripcion.proxima_verificacion = ahora + timedelta(hours=1)
                    errores_timeout += 1
                    continue
                
                estado_anterior = suscripcion.estado_actual
                estado_nuevo = info_guia.get('estado_actual')
                
                # Registrar verificación
                historial = HistorialVerificacion(
                    suscripcion_id=suscripcion.id,
                    estado_encontrado=estado_nuevo
                )
                db.add(historial)
                
                # Actualizar estado
                suscripcion.estado_actual = estado_nuevo
                suscripcion.ultima_verificacion = ahora
                
                # ¿Llegó a RECLAME EN OFICINA?
                if "RECLAME EN OFICINA" in estado_nuevo.upper():
                    logger.info(f"🎯 ¡Guía {suscripcion.numero_guia} llegó a destino!")
                    
                    # Enviar notificación
                    background_tasks.add_task(
                        enviar_push_notification,
                        suscripcion.onesignal_user_id,
                        "🎉 ¡Tu encomienda llegó!",
                        f"La guía {suscripcion.numero_guia} está disponible para recoger en oficina",
                        {
                            "numero_guia": suscripcion.numero_guia,
                            "tipo": "llegada",
                            "estado": "RECLAME EN OFICINA"
                        }
                    )
                    
                    # Marcar para limpieza (se borrará en 48h)
                    suscripcion.fecha_entrega = ahora
                    suscripcion.proxima_verificacion = None
                    notificaciones_enviadas += 1
                    
                else:
                    # Calcular próxima verificación
                    proxima = calcular_proxima_verificacion(
                        estado_actual=estado_nuevo,
                        origen=suscripcion.origen,
                        destino=suscripcion.destino,
                        fecha_admision=suscripcion.fecha_admision,
                        verificaciones_realizadas=suscripcion.verificaciones_realizadas + 1
                    )
                    suscripcion.proxima_verificacion = proxima
                
                suscripcion.verificaciones_realizadas += 1
                verificadas += 1
                
            except Exception as e:
                logger.error(f"❌ Error verificando {suscripcion.numero_guia}: {e}")
                # ✅ Programar reintento en 1 hora
                suscripcion.proxima_verificacion = ahora + timedelta(hours=1)
                continue
        
        db.commit()
        
        # ✅ LIMPIEZA CORREGIDA: Eliminar en el orden correcto
        limite_limpieza = ahora - timedelta(hours=48)
        
        # 1. Obtener IDs de suscripciones a eliminar
        suscripciones_a_eliminar = db.query(Suscripcion.id).filter(
            Suscripcion.fecha_entrega != None,
            Suscripcion.fecha_entrega < limite_limpieza
        ).all()
        
        ids_a_eliminar = [s.id for s in suscripciones_a_eliminar]
        
        historial_eliminado = 0
        suscripciones_eliminadas = 0
        
        if ids_a_eliminar:
            # 2. Eliminar primero el historial (hijo)
            historial_eliminado = db.query(HistorialVerificacion).filter(
                HistorialVerificacion.suscripcion_id.in_(ids_a_eliminar)
            ).delete(synchronize_session=False)
            
            # 3. Luego eliminar las suscripciones (padre)
            suscripciones_eliminadas = db.query(Suscripcion).filter(
                Suscripcion.id.in_(ids_a_eliminar)
            ).delete(synchronize_session=False)
        
        db.commit()
        
        logger.info(f"✅ Verificación completada:")
        logger.info(f"   - Verificadas: {verificadas}")
        logger.info(f"   - Notificaciones enviadas: {notificaciones_enviadas}")
        logger.info(f"   - Errores/Timeouts: {errores_timeout}")
        logger.info(f"   - Historial eliminado: {historial_eliminado}")
        logger.info(f"   - Suscripciones eliminadas: {suscripciones_eliminadas}")
        
        return {
            "timestamp": ahora.isoformat(),
            "guias_verificadas": verificadas,
            "notificaciones_enviadas": notificaciones_enviadas,
            "errores_timeout": errores_timeout,
            "historial_eliminado": historial_eliminado,
            "suscripciones_eliminadas": suscripciones_eliminadas
        }
        
    except Exception as e:
        logger.error(f"❌ Error en verificación: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

# ============ ENDPOINTS DE ADMINISTRACIÓN ============

@app.get("/api/stats", response_model=EstadisticasResponse)
def obtener_estadisticas():
    """Estadísticas del sistema"""
    db = SessionLocal()
    
    try:
        total = db.query(Suscripcion).count()
        activas = db.query(Suscripcion).filter(Suscripcion.activo == True).count()
        completadas = db.query(Suscripcion).filter(Suscripcion.fecha_entrega != None).count()
        
        ahora = datetime.now()
        pendientes = db.query(Suscripcion).filter(
            Suscripcion.activo == True,
            Suscripcion.proxima_verificacion <= ahora
        ).count()
        
        return EstadisticasResponse(
            total_suscripciones=total,
            activas=activas,
            completadas=completadas,
            verificaciones_pendientes=pendientes
        )
        
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    """Health check para Render"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "postgresql"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
```

---

## ✅ **LOS DEMÁS ARCHIVOS ESTÁN CORRECTOS:**

- ✅ **`database.py`** - Está bien configurado
- ✅ **`config.py`** - No necesita cambios
- ✅ **`encomiendas_page.dart`** - Está perfecto, usa el ID correctamente

---

## 📝 **Commit Message:**
```
fix(cron): corregir eliminación en cascada y manejo de timeouts en verificación

- Eliminar historial antes de suscripciones para evitar error FK
- Agregar reintento de 1 hora cuando hay timeout en API
- Mejorar logs con contadores separados de errores
- Sistema robusto ante fallos de red
