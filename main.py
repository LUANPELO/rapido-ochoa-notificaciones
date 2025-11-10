from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import logging
import os
import requests  # ← AGREGADO

from database import SessionLocal, init_db, Suscripcion, HistorialVerificacion
from config import TIEMPOS_VIAJE, CIUDADES_NORMALIZE, ONESIGNAL_API_KEY, ONESIGNAL_APP_ID  # ← AGREGADO
from utils import consultar_guia_rastreo, enviar_push_notification, calcular_proxima_verificacion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Notificaciones Rapido Ochoa",
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

# ===== MODELOS DE DATOS =====

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

class RegistroDispositivoRequest(BaseModel):
    """Request para registrar un dispositivo en OneSignal desde el backend"""
    device_type: int  # 0 = iOS, 1 = Android, 2 = Web
    identifier: str   # FCM Token
    language: str = "es"
    timezone: int = -18000  # Colombia (UTC-5)

# ===== FUNCIONES AUXILIARES =====

def guia_llego_a_destino(estado: str) -> bool:
    """
    Detecta si una guía llegó a su destino final.
    """
    if not estado:
        return False
    
    estado_normalizado = estado.upper().strip()
    
    estados_llegada = [
        "RECIBIDA EN BODEGA",
        "RECLAME EN OFICINA",
        "REALME EN OFICINA",
        "EN OFICINA",
    ]
    
    return any(estado_destino in estado_normalizado for estado_destino in estados_llegada)

def debe_continuar_verificando(estado: str) -> bool:
    """
    Determina si se debe seguir verificando esta guía.
    """
    if not estado:
        return True
    
    estado_normalizado = estado.upper().strip()
    
    estados_finales = [
        "ENTREGADA",
        "ENTREGADO",
        "FACTURADA",
        "FACTURADO",
        "LISTA PARA FACTURAR",
        "ENCAUTADA",
        "ENCAUTADO",
        "INCAUTADA",
        "INCAUTADO",
        "DEVUELTA",
        "DEVUELTO",
        "CANCELADA",
        "CANCELADO"
    ]
    
    return not any(estado_final in estado_normalizado for estado_final in estados_finales)

# ===== EVENTOS DE INICIO =====

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando API de Notificaciones Rápido Ochoa...")
    init_db()
    logger.info("✅ Base de datos inicializada")
    
    # Verificar configuración de OneSignal
    if ONESIGNAL_API_KEY and ONESIGNAL_APP_ID:
        logger.info("✅ OneSignal configurado correctamente")
    else:
        logger.warning("⚠️ OneSignal NO configurado - Variables de entorno faltantes")

# ===== ENDPOINTS =====

@app.get("/")
def root():
    """Endpoint raíz con información de la API"""
    return {
        "servicio": "API Notificaciones Rapido Ochoa",
        "version": "1.0.0",
        "descripcion": "Sistema inteligente de notificaciones push",
        "caracteristicas": [
            "Verificacion optimizada por distancia",
            "PostgreSQL persistente",
            "OneSignal Push Notifications",
            "Limpieza automatica",
            "Registro seguro de dispositivos"
        ],
        "endpoints": {
            "registrar_dispositivo": "POST /api/registrar-dispositivo",
            "suscribirse": "POST /api/suscribir",
            "estado": "GET /api/suscripcion/{guia}",
            "verificar": "POST /api/verificar",
            "estadisticas": "GET /api/stats",
            "health": "GET /api/health"
        }
    }

@app.post("/api/registrar-dispositivo")
async def registrar_dispositivo(data: RegistroDispositivoRequest):
    """
    🔒 ENDPOINT SEGURO: Registra un dispositivo en OneSignal desde el backend.
    
    Flutter envía los datos del dispositivo (FCM token), el backend los registra
    en OneSignal usando la API key que está en variables de entorno.
    
    SEGURIDAD CRÍTICA: La API key de OneSignal NUNCA sale del backend.
    
    Args:
        data: Información del dispositivo
            - device_type: 0=iOS, 1=Android, 2=Web
            - identifier: Token FCM del dispositivo
            - language: Idioma (default: "es")
            - timezone: Zona horaria en segundos (default: -18000 para Colombia UTC-5)
    
    Returns:
        {
            "success": true,
            "onesignal_user_id": "uuid-del-usuario",
            "message": "Dispositivo registrado exitosamente"
        }
    
    Raises:
        HTTPException 400: Token FCM inválido o error de validación
        HTTPException 500: OneSignal no configurado o error interno
        HTTPException 504: Timeout conectando con OneSignal
    """
    try:
        logger.info("=" * 60)
        logger.info("📱 NUEVA SOLICITUD DE REGISTRO DE DISPOSITIVO")
        logger.info("=" * 60)
        logger.info(f"   Device Type: {data.device_type} (0=iOS, 1=Android, 2=Web)")
        logger.info(f"   Language: {data.language}")
        logger.info(f"   Timezone: {data.timezone}")
        logger.info(f"   FCM Token (primeros 30 chars): {data.identifier[:30]}...")
        
        # ✅ VALIDACIÓN 1: Verificar que OneSignal esté configurado
        if not ONESIGNAL_API_KEY or not ONESIGNAL_APP_ID:
            logger.error("❌ CRÍTICO: OneSignal no configurado")
            logger.error("   Variables de entorno faltantes:")
            logger.error(f"   - ONESIGNAL_API_KEY: {'✅ OK' if ONESIGNAL_API_KEY else '❌ FALTA'}")
            logger.error(f"   - ONESIGNAL_APP_ID: {'✅ OK' if ONESIGNAL_APP_ID else '❌ FALTA'}")
            raise HTTPException(
                status_code=500, 
                detail="OneSignal no está configurado en el servidor. Contacte al administrador del sistema."
            )
        
        # ✅ VALIDACIÓN 2: Verificar que el token no esté vacío
        if not data.identifier or len(data.identifier.strip()) == 0:
            logger.error("❌ Token FCM vacío o inválido")
            raise HTTPException(
                status_code=400,
                detail="El token FCM es requerido y no puede estar vacío"
            )
        
        # ✅ VALIDACIÓN 3: Verificar tipo de dispositivo válido
        if data.device_type not in [0, 1, 2]:
            logger.error(f"❌ Tipo de dispositivo inválido: {data.device_type}")
            raise HTTPException(
                status_code=400,
                detail="device_type debe ser 0 (iOS), 1 (Android) o 2 (Web)"
            )
        
        logger.info("✅ Todas las validaciones pasadas")
        logger.info("🔐 Preparando credenciales de OneSignal...")
        
        # Preparar headers para OneSignal API
        headers = {
            "Authorization": f"Basic {ONESIGNAL_API_KEY}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Preparar payload para registrar dispositivo
        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "device_type": data.device_type,
            "identifier": data.identifier.strip(),
            "language": data.language,
            "timezone": data.timezone,
        }
        
        logger.info("📡 Enviando solicitud a OneSignal API...")
        logger.info(f"   URL: https://onesignal.com/api/v1/players")
        logger.info(f"   App ID: {ONESIGNAL_APP_ID[:20]}...")
        
        # ✅ LLAMADA SEGURA A ONESIGNAL API
        response = requests.post(
            "https://onesignal.com/api/v1/players",
            json=payload,
            headers=headers,
            timeout=15  # Timeout de 15 segundos
        )
        
        logger.info(f"📥 Respuesta recibida de OneSignal")
        logger.info(f"   Status Code: {response.status_code}")
        
        # ✅ PROCESAR RESPUESTA EXITOSA
        if response.status_code in [200, 201]:
            result = response.json()
            onesignal_user_id = result.get("id")
            
            # Validar que se recibió un User ID válido
            if not onesignal_user_id:
                logger.error("⚠️ OneSignal no devolvió un User ID")
                logger.error(f"   Response completo: {result}")
                raise HTTPException(
                    status_code=500,
                    detail="OneSignal no devolvió un User ID válido. Intente nuevamente."
                )
            
            # Validar formato UUID del User ID
            if len(onesignal_user_id) < 30:
                logger.warning(f"⚠️ User ID con formato sospechoso: {onesignal_user_id}")
            
            logger.info("=" * 60)
            logger.info("✅ REGISTRO EXITOSO")
            logger.info("=" * 60)
            logger.info(f"   OneSignal User ID: {onesignal_user_id}")
            logger.info(f"   Success: {result.get('success', True)}")
            logger.info("=" * 60)
            
            return {
                "success": True,
                "onesignal_user_id": onesignal_user_id,
                "message": "Dispositivo registrado exitosamente en OneSignal"
            }
        
        # ✅ MANEJO DE ERRORES 400 (Validación)
        elif response.status_code == 400:
            error_data = response.json()
            logger.error("❌ Error de validación en OneSignal")
            logger.error(f"   Status: 400")
            logger.error(f"   Errores: {error_data.get('errors', {})}")
            
            error_msg = "Token FCM inválido o parámetros incorrectos"
            if 'errors' in error_data:
                errors_list = error_data['errors']
                if isinstance(errors_list, list) and len(errors_list) > 0:
                    error_msg = str(errors_list[0])
                elif isinstance(errors_list, dict):
                    error_msg = str(list(errors_list.values())[0])
            
            raise HTTPException(
                status_code=400,
                detail=f"Error de validación de OneSignal: {error_msg}"
            )
        
        # ✅ MANEJO DE OTROS ERRORES DE ONESIGNAL
        else:
            logger.error(f"❌ Error inesperado de OneSignal")
            logger.error(f"   Status Code: {response.status_code}")
            logger.error(f"   Response: {response.text[:500]}")
            
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error de OneSignal (código {response.status_code}). Intente nuevamente."
            )
    
    # ✅ MANEJO DE TIMEOUT
    except requests.exceptions.Timeout:
        logger.error("⏰ TIMEOUT conectando con OneSignal")
        logger.error("   La solicitud tardó más de 15 segundos")
        raise HTTPException(
            status_code=504,
            detail="Timeout al conectar con OneSignal. Verifique su conexión e intente nuevamente."
        )
    
    # ✅ MANEJO DE ERRORES DE CONEXIÓN
    except requests.exceptions.ConnectionError as e:
        logger.error(f"🌐 Error de conexión con OneSignal: {e}")
        raise HTTPException(
            status_code=503,
            detail="No se pudo conectar con OneSignal. Verifique su conexión a internet."
        )
    
    # Re-lanzar HTTPException para que FastAPI las maneje correctamente
    except HTTPException:
        raise
    
    # ✅ MANEJO DE ERRORES INESPERADOS
    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ ERROR INESPERADO EN REGISTRO DE DISPOSITIVO")
        logger.error("=" * 60)
        logger.error(f"   Tipo: {type(e).__name__}")
        logger.error(f"   Mensaje: {str(e)}")
        logger.error("=" * 60)
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.post("/api/suscribir", response_model=SuscripcionResponse)
async def suscribir_guia(data: SuscripcionCreate, background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        logger.info(f"Nueva suscripcion: {data.numero_guia}")
        
        suscripcion_existente = db.query(Suscripcion).filter(
            Suscripcion.numero_guia == data.numero_guia,
            Suscripcion.onesignal_user_id == data.onesignal_user_id,
            Suscripcion.activo == True
        ).first()
        
        if suscripcion_existente:
            logger.info(f"Suscripcion ya existe para {data.numero_guia}")
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
        
        logger.info(f"Consultando informacion inicial de {data.numero_guia}")
        info_guia = consultar_guia_rastreo(data.numero_guia)
        
        if not info_guia:
            raise HTTPException(status_code=404, detail=f"No se encontro la guia {data.numero_guia}")
        
        estado_actual = info_guia.get('estado_actual', '')
        
        if guia_llego_a_destino(estado_actual):
            raise HTTPException(
                status_code=400, 
                detail=f"Guia ya esta en {estado_actual}, no se puede suscribir a notificaciones"
            )
        
        if not debe_continuar_verificando(estado_actual):
            raise HTTPException(
                status_code=400,
                detail=f"Guia en estado final ({estado_actual}), no se puede suscribir"
            )
        
        nueva_suscripcion = Suscripcion(
            numero_guia=data.numero_guia,
            onesignal_user_id=data.onesignal_user_id,
            token_fcm=data.token_fcm,
            telefono=data.telefono,
            origen=info_guia.get('origen'),
            destino=info_guia.get('destino'),
            estado_actual=estado_actual,
            fecha_admision=info_guia.get('fecha_admision'),
            remitente=info_guia.get('remitente_nombre'),
            destinatario=info_guia.get('destinatario_nombre')
        )
        
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
        
        logger.info(f"✅ Suscripcion creada: ID {nueva_suscripcion.id}")
        logger.info(f"📅 Primera verificacion en: {proxima}")
        
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
        logger.error(f"❌ Error creando suscripcion: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/suscripcion/{numero_guia}", response_model=SuscripcionResponse)
def obtener_estado_suscripcion(numero_guia: str):
    db = SessionLocal()
    try:
        suscripcion = db.query(Suscripcion).filter(
            Suscripcion.numero_guia == numero_guia,
            Suscripcion.activo == True
        ).first()
        
        if not suscripcion:
            raise HTTPException(status_code=404, detail="No se encontro suscripcion activa para esta guia")
        
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
    db = SessionLocal()
    try:
        suscripcion = db.query(Suscripcion).filter(
            Suscripcion.numero_guia == numero_guia,
            Suscripcion.activo == True
        ).first()
        
        if not suscripcion:
            raise HTTPException(status_code=404, detail="No se encontro suscripcion activa")
        
        suscripcion.activo = False
        db.commit()
        
        logger.info(f"Suscripcion cancelada: {numero_guia}")
        return {"mensaje": "Suscripcion cancelada exitosamente"}
    finally:
        db.close()

@app.post("/api/verificar")
async def verificar_guias(background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        ahora = datetime.now()
        logger.info(f"🔍 Iniciando verificacion de guias: {ahora}")
        
        suscripciones = db.query(Suscripcion).filter(
            Suscripcion.activo == True,
            Suscripcion.proxima_verificacion <= ahora
        ).all()
        
        logger.info(f"📦 Guias a verificar: {len(suscripciones)}")
        
        verificadas = 0
        notificaciones_enviadas = 0
        errores_timeout = 0
        desactivadas_por_estado_final = 0
        
        for suscripcion in suscripciones:
            try:
                logger.info(f"🔍 Consultando guia {suscripcion.numero_guia} en API de rastreo...")
                info_guia = consultar_guia_rastreo(suscripcion.numero_guia)
                
                if not info_guia:
                    logger.warning(f"⚠️ No se pudo consultar guia {suscripcion.numero_guia}")
                    suscripcion.proxima_verificacion = ahora + timedelta(hours=1)
                    errores_timeout += 1
                    continue
                
                estado_anterior = suscripcion.estado_actual
                estado_nuevo = info_guia.get('estado_actual', '')
                
                historial = HistorialVerificacion(
                    suscripcion_id=suscripcion.id,
                    estado_encontrado=estado_nuevo
                )
                db.add(historial)
                
                suscripcion.estado_actual = estado_nuevo
                suscripcion.ultima_verificacion = ahora
                
                logger.info(f"📊 Datos extra incluidos: {info_guia.get('datos_extra', {})}")
                
                if guia_llego_a_destino(estado_nuevo):
                    logger.info(f"🎉 Guia {suscripcion.numero_guia} llego a destino! Estado: {estado_nuevo}")
                    
                    background_tasks.add_task(
                        enviar_push_notification,
                        suscripcion.onesignal_user_id,
                        "¡Tu encomienda llegó! 🎉",
                        f"La guía {suscripcion.numero_guia} ya está disponible para recoger en oficina",
                        {
                            "numero_guia": suscripcion.numero_guia,
                            "tipo": "llegada",
                            "estado": estado_nuevo
                        }
                    )
                    
                    suscripcion.fecha_entrega = ahora
                    suscripcion.proxima_verificacion = None
                    suscripcion.activo = False
                    notificaciones_enviadas += 1
                    
                    logger.info(f"✅ Notificación enviada para {suscripcion.numero_guia}")
                
                elif not debe_continuar_verificando(estado_nuevo):
                    logger.info(f"⚠️ Guia {suscripcion.numero_guia} en estado final: {estado_nuevo}")
                    suscripcion.activo = False
                    suscripcion.proxima_verificacion = None
                    desactivadas_por_estado_final += 1
                
                else:
                    proxima = calcular_proxima_verificacion(
                        estado_actual=estado_nuevo,
                        origen=suscripcion.origen,
                        destino=suscripcion.destino,
                        fecha_admision=suscripcion.fecha_admision,
                        verificaciones_realizadas=suscripcion.verificaciones_realizadas + 1
                    )
                    suscripcion.proxima_verificacion = proxima
                    logger.info(f"📅 Proxima verificacion en: {proxima}")
                
                suscripcion.verificaciones_realizadas += 1
                verificadas += 1
                
            except Exception as e:
                logger.error(f"❌ Error verificando {suscripcion.numero_guia}: {e}")
                suscripcion.proxima_verificacion = ahora + timedelta(hours=1)
                continue
        
        db.commit()
        
        limite_limpieza = ahora - timedelta(hours=48)
        suscripciones_a_eliminar = db.query(Suscripcion.id).filter(
            Suscripcion.fecha_entrega != None,
            Suscripcion.fecha_entrega < limite_limpieza
        ).all()
        
        ids_a_eliminar = [s.id for s in suscripciones_a_eliminar]
        historial_eliminado = 0
        suscripciones_eliminadas = 0
        
        if ids_a_eliminar:
            historial_eliminado = db.query(HistorialVerificacion).filter(
                HistorialVerificacion.suscripcion_id.in_(ids_a_eliminar)
            ).delete(synchronize_session=False)
            
            suscripciones_eliminadas = db.query(Suscripcion).filter(
                Suscripcion.id.in_(ids_a_eliminar)
            ).delete(synchronize_session=False)
        
        db.commit()
        
        logger.info(f"✅ Verificacion completada:")
        logger.info(f"   - Verificadas: {verificadas}")
        logger.info(f"   - Notificaciones enviadas: {notificaciones_enviadas}")
        logger.info(f"   - Desactivadas (estado final): {desactivadas_por_estado_final}")
        logger.info(f"   - Errores/Timeouts: {errores_timeout}")
        logger.info(f"   - Historial eliminado: {historial_eliminado}")
        logger.info(f"   - Suscripciones eliminadas: {suscripciones_eliminadas}")
        
        return {
            "timestamp": ahora.isoformat(),
            "guias_verificadas": verificadas,
            "notificaciones_enviadas": notificaciones_enviadas,
            "desactivadas_estado_final": desactivadas_por_estado_final,
            "errores_timeout": errores_timeout,
            "historial_eliminado": historial_eliminado,
            "suscripciones_eliminadas": suscripciones_eliminadas
        }
    except Exception as e:
        logger.error(f"❌ Error en verificacion: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/stats", response_model=EstadisticasResponse)
def obtener_estadisticas():
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
    """Endpoint de salud para monitoreo"""
    onesignal_status = "configured" if (ONESIGNAL_API_KEY and ONESIGNAL_APP_ID) else "not_configured"
    
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "postgresql",
        "onesignal": onesignal_status
    }

@app.get("/api/suscripciones/user/{onesignal_user_id}")
def obtener_suscripciones_por_usuario(onesignal_user_id: str):
    """
    Obtiene todas las suscripciones activas de un usuario
    """
    db = SessionLocal()
    try:
        suscripciones = db.query(Suscripcion).filter(
            Suscripcion.onesignal_user_id == onesignal_user_id,
            Suscripcion.activo == True
        ).all()
        
        resultado = []
        for s in suscripciones:
            resultado.append({
                "numero_guia": s.numero_guia,
                "estado_actual": s.estado_actual,
                "origen": s.origen,
                "destino": s.destino,
                "fecha_creacion": s.fecha_creacion.isoformat() if s.fecha_creacion else None,
                "proxima_verificacion": s.proxima_verificacion.isoformat() if s.proxima_verificacion else None,
            })
        
        logger.info(f"📋 Usuario {onesignal_user_id}: {len(resultado)} suscripciones activas")
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error consultando suscripciones de usuario: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/admin/ver-suscripciones")
def ver_todas_suscripciones():
    """Ver todas las suscripciones activas (endpoint administrativo)"""
    db = SessionLocal()
    try:
        suscripciones = db.query(Suscripcion).filter(
            Suscripcion.activo == True
        ).all()
        
        resultado = []
        for s in suscripciones:
            resultado.append({
                "id": s.id,
                "numero_guia": s.numero_guia,
                "onesignal_user_id": s.onesignal_user_id,
                "estado_actual": s.estado_actual,
                "fecha_creacion": s.fecha_creacion.isoformat() if s.fecha_creacion else None,
                "proxima_verificacion": s.proxima_verificacion.isoformat() if s.proxima_verificacion else None,
            })
        
        logger.info(f"📊 Consultando suscripciones activas: {len(resultado)}")
        
        return {
            "total_activas": len(resultado),
            "suscripciones": resultado
        }
    finally:
        db.close()

@app.get("/api/admin/limpiar-suscripciones")
def limpiar_suscripciones_antiguas(user_id_actual: str):
    """Desactiva suscripciones antiguas (endpoint administrativo)"""
    db = SessionLocal()
    try:
        logger.info(f"🧹 Limpiando suscripciones antiguas...")
        logger.info(f"✅ Mantener activas: User ID = {user_id_actual}")
        
        total_antes = db.query(Suscripcion).filter(Suscripcion.activo == True).count()
        
        suscripciones_antiguas = db.query(Suscripcion).filter(
            Suscripcion.activo == True,
            Suscripcion.onesignal_user_id != user_id_actual
        ).all()
        
        desactivadas = []
        for suscripcion in suscripciones_antiguas:
            desactivadas.append({
                "guia": suscripcion.numero_guia,
                "user_id": suscripcion.onesignal_user_id,
                "estado": suscripcion.estado_actual
            })
            suscripcion.activo = False
        
        db.commit()
        
        total_despues = db.query(Suscripcion).filter(Suscripcion.activo == True).count()
        
        logger.info(f"✅ Limpieza completada:")
        logger.info(f"   - Antes: {total_antes} activas")
        logger.info(f"   - Desactivadas: {len(desactivadas)}")
        logger.info(f"   - Después: {total_despues} activas")
        
        return {
            "mensaje": "Limpieza exitosa",
            "antes": total_antes,
            "desactivadas": len(desactivadas),
            "despues": total_despues,
            "detalle_desactivadas": desactivadas
        }
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
