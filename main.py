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

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando API de Notificaciones...")
    init_db()
    logger.info("Base de datos inicializada")

@app.get("/")
def root():
    return {
        "servicio": "API Notificaciones Rapido Ochoa",
        "version": "1.0.0",
        "descripcion": "Sistema inteligente de notificaciones push",
        "caracteristicas": [
            "Verificacion optimizada por distancia",
            "PostgreSQL persistente",
            "OneSignal Push Notifications",
            "Limpieza automatica"
        ],
        "endpoints": {
            "suscribirse": "POST /api/suscribir",
            "estado": "GET /api/suscripcion/{guia}",
            "verificar": "POST /api/verificar",
            "estadisticas": "GET /api/stats"
        }
    }

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
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "database": "postgresql"
    }

@app.get("/api/suscripciones/user/{onesignal_user_id}")
def obtener_suscripciones_por_usuario(onesignal_user_id: str):
    """
    ✅ CORREGIDO - Devuelve lista vacía si no hay suscripciones
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
    """Ver todas las suscripciones activas"""
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
    """Desactiva suscripciones antiguas"""
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
