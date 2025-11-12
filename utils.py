"""
Funciones auxiliares del sistema
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import (
    RASTREO_API_URL, 
    ONESIGNAL_API_KEY,
    ONESIGNAL_APP_ID,
    HORAS_ENTRE_VERIFICACIONES,
    obtener_tiempo_viaje,  # ✅ IMPORTAR de config
    limpiar_nombre_ciudad  # ✅ IMPORTAR de config
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

def calcular_proxima_verificacion(
    estado_actual: str,
    origen: str,
    destino: str,
    fecha_admision: str,
    verificaciones_realizadas: int = 0
) -> Optional[datetime]:
    """
    Calcula cuándo debe realizarse la próxima verificación de una guía
    
    ⚠️ LÓGICA CRÍTICA: El timer del 80% SOLO inicia cuando el estado es "DESPACHO NACIONAL BUSES"
    
    Estrategia inteligente:
    1. Espera hasta detectar "DESPACHO NACIONAL BUSES" específicamente
    2. Primera verificación DESPUÉS del despacho: 80% del tiempo estimado de viaje
    3. Siguientes: cada 2 horas hasta encontrar "RECLAME EN OFICINA"
    
    Args:
        estado_actual: Estado actual de la guía
        origen: Ciudad origen (puede incluir departamento)
        destino: Ciudad destino (puede incluir departamento)
        fecha_admision: Fecha de admisión (formato: "2025/10/03 13:07")
        verificaciones_realizadas: Número de verificaciones ya hechas
    
    Returns:
        Datetime de la próxima verificación o None si ya llegó
    """
    try:
        estado_upper = estado_actual.upper() if estado_actual else ""
        
        # ✅ PASO 1: Si ya llegó a destino, NO programar más verificaciones
        if "RECLAME EN OFICINA" in estado_upper or "ENTREGADA" in estado_upper:
            logger.info("📦 Guía ya está en RECLAME EN OFICINA, no programar verificaciones")
            return None
        
        # ✅ PASO 2: Si aún NO está en "DESPACHO NACIONAL BUSES", verificar en 2 horas
        if "DESPACHO NACIONAL BUSES" not in estado_upper:
            proxima = datetime.now() + timedelta(hours=2)
            logger.info(f"⏳ Guía sin despachar todavía, verificar en 2 horas: {proxima}")
            logger.info(f"📍 Estado actual: {estado_actual}")
            return proxima
        
        # ✅ PASO 3: Ya está en "DESPACHO NACIONAL BUSES", usar estrategia inteligente
        logger.info(f"🚛 Guía DESPACHADA - Iniciando cálculo de tiempo estimado")
        
        # Obtener tiempo de viaje (maneja automáticamente departamentos)
        tiempo_viaje = obtener_tiempo_viaje(origen, destino)
        logger.info(f"⏱️ Tiempo estimado de viaje: {tiempo_viaje} horas")
        
        # ✅ Primera verificación después del despacho: 80% del tiempo estimado
        if verificaciones_realizadas == 0 or verificaciones_realizadas == 1:
            # Calcular tiempo desde admisión
            try:
                fecha_obj = datetime.strptime(fecha_admision, "%Y/%m/%d %H:%M")
                logger.info(f"📅 Fecha de admisión: {fecha_obj}")
            except:
                # Si no se puede parsear, usar hora actual
                fecha_obj = datetime.now()
                logger.warning(f"⚠️ No se pudo parsear fecha {fecha_admision}, usando hora actual")
            
            # Calcular cuándo debería llegar (80% del tiempo total)
            horas_hasta_verificacion = int(tiempo_viaje * 0.8)
            primera_verificacion = fecha_obj + timedelta(hours=horas_hasta_verificacion)
            
            # Si ya pasó ese tiempo, verificar inmediatamente
            if primera_verificacion < datetime.now():
                logger.warning(f"⚠️ El 80% del tiempo ya pasó, verificar inmediatamente")
                primera_verificacion = datetime.now() + timedelta(minutes=5)
            
            logger.info(
                f"📅 Primera verificación inteligente programada:\n"
                f"   - Tiempo total viaje: {tiempo_viaje}h\n"
                f"   - Esperar hasta 80%: {horas_hasta_verificacion}h\n"
                f"   - Próxima verificación: {primera_verificacion}"
            )
            return primera_verificacion
        
        # ✅ Verificaciones subsiguientes: cada 2 horas
        proxima = datetime.now() + timedelta(hours=HORAS_ENTRE_VERIFICACIONES)
        logger.info(f"📅 Verificación subsiguiente en {HORAS_ENTRE_VERIFICACIONES}h: {proxima}")
        return proxima
        
    except Exception as e:
        logger.error(f"❌ Error calculando próxima verificación: {e}")
        # En caso de error, verificar en 2 horas
        return datetime.now() + timedelta(hours=2)


# ============ ONESIGNAL PUSH NOTIFICATIONS ============

def enviar_push_notification(
    onesignal_user_id: str, 
    titulo: str, 
    mensaje: str, 
    datos_extra: dict = None
) -> bool:
    """
    ✅ FUNCIÓN CORREGIDA - Envía notificación push usando OneSignal Player ID (API V1)
    
    IMPORTANTE: Usa 'include_player_ids' compatible con el registro via API V1 (/players)
    
    Args:
        onesignal_user_id: OneSignal Player ID (UUID formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        datos_extra: Datos adicionales para la app (opcional)
    
    Returns:
        True si se envió exitosamente, False en caso contrario
    """
    import re
    
    try:
        if not ONESIGNAL_API_KEY or not ONESIGNAL_APP_ID:
            logger.warning("⚠️ OneSignal no configurado (API_KEY o APP_ID faltante)")
            return False
        
        # Validar que el user_id no esté vacío
        if not onesignal_user_id or onesignal_user_id.strip() == "":
            logger.error("❌ OneSignal Player ID está vacío")
            return False
        
        # ✅ Validar formato UUID del Player ID
        uuid_regex = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_regex, onesignal_user_id, re.IGNORECASE):
            logger.warning(f"⚠️ Player ID con formato inválido: {onesignal_user_id}")
            return False
        
        logger.info(f"📲 Enviando push OneSignal: {titulo}")
        logger.info(f"🎯 Destinatario (Player ID): {onesignal_user_id}")
        
        headers = {
            "Authorization": f"Basic {ONESIGNAL_API_KEY}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # ✅✅ CORRECCIÓN CRÍTICA: Usar include_player_ids para API V1
        # Esto es compatible con el registro via /api/v1/players
        payload = {
            "app_id": ONESIGNAL_APP_ID,
            
            # ✅ USAR include_player_ids en lugar de include_aliases
            # Esto funciona con el player_id devuelto por POST /players
            "include_player_ids": [onesignal_user_id],
            
            "headings": {"en": titulo},
            "contents": {"en": mensaje},
            "priority": 10
        }
        
        # Agregar datos adicionales si existen
        if datos_extra:
            payload["data"] = datos_extra
            logger.info(f"📦 Datos extra incluidos: {datos_extra}")
        
        logger.info(f"📡 Enviando a OneSignal API v1/notifications...")
        
        response = requests.post(
            "https://onesignal.com/api/v1/notifications",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        result = response.json()
        
        if response.status_code == 200:
            recipients = result.get("recipients", 0)
            if recipients > 0:
                logger.info(f"✅ Push enviado exitosamente via OneSignal")
                logger.info(f"📊 Recipients: {recipients}")
                logger.info(f"📋 Notification ID: {result.get('id', 'N/A')}")
                return True
            else:
                logger.warning(f"⚠️ OneSignal: No se pudo enviar (sin recipients)")
                logger.warning(f"📄 Response completo: {result}")
                return False
        else:
            logger.error(f"❌ Error HTTP al enviar push: {response.status_code}")
            logger.error(f"📄 Response: {result}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout al enviar notificación OneSignal")
        return False
    except Exception as e:
        logger.error(f"❌ Error enviando push: {e}")
        return False


# ============ VALIDACIONES ============

def validar_numero_guia(numero_guia: str) -> bool:
    """
    Valida el formato del número de guía de Rápido Ochoa
    Formato típico: E121101188 (letra seguida de números) o solo números
    
    Args:
        numero_guia: Número de guía a validar
    
    Returns:
        True si es válido, False en caso contrario
    """
    import re
    if not numero_guia:
        return False
    
    # Rápido Ochoa usa formato: Letra + 8-10 dígitos, o solo números
    patron = r'^[A-Z]?\d{8,10}$'
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
