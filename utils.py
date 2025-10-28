"""
Funciones auxiliares del sistema
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import (
    RASTREO_API_URL, 
    FIREBASE_SERVER_KEY, 
    FIREBASE_FCM_URL,
    TIEMPOS_VIAJE,
    HORAS_ANTES_LLEGADA,
    HORAS_ENTRE_VERIFICACIONES,
    normalizar_ciudad
)

logger = logging.getLogger(__name__)

# ============ INTEGRACIÓN CON API DE RASTREO ============

def consultar_guia_rastreo(numero_guia: str) -> Optional[Dict]:
    """
    Consulta la información de una guía en la API de rastreo existente
    
    Args:
        numero_guia: Número de guía a consultar
    
    Returns:
        Diccionario con la información de la guía o None si hay error
    """
    try:
        logger.info(f"🔍 Consultando guía {numero_guia} en API de rastreo...")
        
        response = requests.get(
            f"{RASTREO_API_URL}/{numero_guia}",
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Guía {numero_guia} consultada exitosamente")
            return data
        else:
            logger.error(f"❌ Error consultando guía: HTTP {response.status_code}")
            return None
            
    except requests.Timeout:
        logger.error(f"⏰ Timeout consultando guía {numero_guia}")
        return None
    except Exception as e:
        logger.error(f"❌ Error consultando guía: {e}")
        return None


# ============ CÁLCULO DE TIEMPOS ============

def obtener_tiempo_viaje(origen: str, destino: str) -> int:
    """
    Obtiene el tiempo de viaje entre dos ciudades
    
    Args:
        origen: Ciudad de origen
        destino: Ciudad de destino
    
    Returns:
        Horas de viaje aproximadas
    """
    # Normalizar nombres de ciudades
    origen_norm = normalizar_ciudad(origen)
    destino_norm = normalizar_ciudad(destino)
    
    # Buscar en el diccionario
    tiempo = TIEMPOS_VIAJE.get((origen_norm, destino_norm))
    
    if tiempo:
        return tiempo
    
    # Si no existe la ruta exacta, retornar tiempo por defecto
    logger.warning(f"⚠️ Ruta {origen_norm} -> {destino_norm} no encontrada, usando tiempo por defecto")
    return 12  # 12 horas por defecto


def calcular_proxima_verificacion(
    estado_actual: str,
    origen: str,
    destino: str,
    fecha_admision: str,
    verificaciones_realizadas: int = 0
) -> Optional[datetime]:
    """
    Calcula cuándo debe realizarse la próxima verificación de una guía
    
    Estrategia inteligente:
    - Espera hasta detectar "DESPACHO" o similar
    - Primera verificación: 80% del tiempo estimado de viaje
    - Siguientes: cada 2 horas hasta encontrar "RECLAME EN OFICINA"
    
    Args:
        estado_actual: Estado actual de la guía
        origen: Ciudad origen
        destino: Ciudad destino
        fecha_admision: Fecha de admisión (formato: "2025/10/03 13:07")
        verificaciones_realizadas: Número de verificaciones ya hechas
    
    Returns:
        Datetime de la próxima verificación o None si ya llegó
    """
    try:
        estado_upper = estado_actual.upper() if estado_actual else ""
        
        # Si ya llegó a destino, no programar más verificaciones
        if "RECLAME EN OFICINA" in estado_upper or "ENTREGADA" in estado_upper:
            logger.info("📦 Guía ya está en RECLAME EN OFICINA, no programar verificaciones")
            return None
        
        # Si aún no ha sido despachada, verificar en 2 horas
        if "DESPACHO" not in estado_upper and "EN RUTA" not in estado_upper:
            proxima = datetime.now() + timedelta(hours=2)
            logger.info(f"📅 Guía sin despachar, verificar en 2 horas: {proxima}")
            return proxima
        
        # Ya fue despachada, usar estrategia inteligente
        tiempo_viaje = obtener_tiempo_viaje(origen, destino)
        
        # Primera verificación después del despacho: 80% del tiempo estimado
        if verificaciones_realizadas == 0 or verificaciones_realizadas == 1:
            # Calcular tiempo desde admisión
            try:
                fecha_obj = datetime.strptime(fecha_admision, "%Y/%m/%d %H:%M")
            except:
                # Si no se puede parsear, usar hora actual
                fecha_obj = datetime.now()
            
            # Calcular cuándo debería llegar (80% del tiempo)
            horas_hasta_llegada = int(tiempo_viaje * 0.8)
            primera_verificacion = fecha_obj + timedelta(hours=horas_hasta_llegada)
            
            # Si ya pasó ese tiempo, verificar inmediatamente
            if primera_verificacion < datetime.now():
                primera_verificacion = datetime.now() + timedelta(minutes=5)
            
            logger.info(f"📅 Primera verificación inteligente en {horas_hasta_llegada}h: {primera_verificacion}")
            return primera_verificacion
        
        # Verificaciones subsiguientes: cada 2 horas
        proxima = datetime.now() + timedelta(hours=HORAS_ENTRE_VERIFICACIONES)
        logger.info(f"📅 Verificación subsiguiente en {HORAS_ENTRE_VERIFICACIONES}h: {proxima}")
        return proxima
        
    except Exception as e:
        logger.error(f"❌ Error calculando próxima verificación: {e}")
        # En caso de error, verificar en 2 horas
        return datetime.now() + timedelta(hours=2)


# ============ FIREBASE CLOUD MESSAGING ============

def enviar_push_notification(token_fcm: str, titulo: str, mensaje: str) -> bool:
    """
    Envía una notificación push a través de Firebase Cloud Messaging
    
    Args:
        token_fcm: Token del dispositivo
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
    
    Returns:
        True si se envió exitosamente, False en caso contrario
    """
    try:
        if not FIREBASE_SERVER_KEY:
            logger.warning("⚠️ FIREBASE_SERVER_KEY no configurada")
            return False
        
        logger.info(f"📲 Enviando push: {titulo}")
        
        headers = {
            "Authorization": f"key={FIREBASE_SERVER_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "to": token_fcm,
            "notification": {
                "title": titulo,
                "body": mensaje,
                "sound": "default",
                "priority": "high"
            },
            "priority": "high"
        }
        
        response = requests.post(
            FIREBASE_FCM_URL,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success") == 1:
                logger.info(f"✅ Push enviado exitosamente")
                return True
            else:
                logger.error(f"❌ FCM respondió con error: {result}")
                return False
        else:
            logger.error(f"❌ Error HTTP al enviar push: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error enviando push: {e}")
        return False


# ============ VALIDACIONES ============

def validar_numero_guia(numero_guia: str) -> bool:
    """
    Valida el formato del número de guía de Rápido Ochoa
    Formato típico: E121101188 (letra seguida de números)
    
    Args:
        numero_guia: Número de guía a validar
    
    Returns:
        True si es válido, False en caso contrario
    """
    import re
    if not numero_guia:
        return False
    
    # Rápido Ochoa usa formato: Letra + 9-10 dígitos
    patron = r'^[A-Z]\d{8,10}$'
    return bool(re.match(patron, numero_guia.upper()))


def parsear_fecha_admision(fecha_str: str) -> Optional[datetime]:
    """
    Parsea la fecha de admisión del formato de Rápido Ochoa
    
    Args:
        fecha_str: Fecha en formato "2025/10/03 13:07"
    
    Returns:
        Objeto datetime o None si hay error
    """
    try:
        return datetime.strptime(fecha_str, "%Y/%m/%d %H:%M")
    except:
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        except:
            logger.warning(f"⚠️ No se pudo parsear fecha: {fecha_str}")
            return None