"""
Funciones auxiliares del sistema
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from config import (
    RASTREO_API_URL, 
    ONESIGNAL_API_KEY,
    ONESIGNAL_APP_ID,
    HORAS_ENTRE_VERIFICACIONES,
    obtener_tiempo_viaje,
    limpiar_nombre_ciudad
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
    verificaciones_realizadas: int = 0,
    trazabilidad: List[Dict] = None
) -> Optional[datetime]:
    """
    Calcula cuándo debe realizarse la próxima verificación de una guía
    
    ⚠️ LÓGICA OPTIMIZADA:
    1. Espera hasta detectar "DESPACHO NACIONAL BUSES" específicamente
    2. Primera verificación DESPUÉS del despacho: 90% del tiempo estimado de viaje
    3. Siguientes: cada 30 minutos hasta encontrar "RECLAME EN OFICINA"
    4. Si ya pasó el 100% del tiempo: verifica cada 1 hora (guía retrasada)
    
    Args:
        estado_actual: Estado actual de la guía
        origen: Ciudad origen (puede incluir departamento)
        destino: Ciudad destino (puede incluir departamento)
        fecha_admision: Fecha de admisión (formato: "2025/10/03 13:07")
        verificaciones_realizadas: Número de verificaciones ya hechas
        trazabilidad: Lista con el historial de estados y fechas
    
    Returns:
        Datetime de la próxima verificación o None si ya llegó
    """
    try:
        estado_upper = estado_actual.upper() if estado_actual else ""
        ahora = datetime.now()
        
        # ✅ PASO 1: Si ya llegó a destino, NO programar más verificaciones
        if "RECLAME EN OFICINA" in estado_upper or "ENTREGADA" in estado_upper:
            logger.info("📦 Guía ya está en RECLAME EN OFICINA, no programar verificaciones")
            return None
        
        # ✅ PASO 2: Si aún NO está en "DESPACHO NACIONAL BUSES", verificar cada 30 minutos
        if "DESPACHO NACIONAL BUSES" not in estado_upper:
            proxima = ahora + timedelta(minutes=30)
            logger.info(f"⏳ Guía sin despachar todavía, verificar en 30 minutos: {proxima}")
            logger.info(f"📍 Estado actual: {estado_actual}")
            return proxima
        
        # ✅ PASO 3: Ya está en "DESPACHO NACIONAL BUSES", usar estrategia inteligente
        logger.info(f"🚛 Guía DESPACHADA - Iniciando cálculo de tiempo estimado")
        
        # ✅ BUSCAR LA FECHA REAL DEL DESPACHO EN LA TRAZABILIDAD
        fecha_despacho = None
        
        if trazabilidad:
            logger.info(f"🔍 Buscando fecha real de despacho en trazabilidad...")
            for registro in trazabilidad:
                detalle = registro.get('detalle', '').upper()
                if "DESPACHO NACIONAL BUSES" in detalle:
                    fecha_str = registro.get('fecha')
                    if fecha_str:
                        fecha_despacho = parsear_fecha_admision(fecha_str)
                        if fecha_despacho:
                            logger.info(f"✅ Fecha real de despacho encontrada: {fecha_despacho}")
                            break
        
        # Si no se encontró la fecha en trazabilidad, usar ahora como fallback
        if not fecha_despacho:
            logger.warning("⚠️ No se encontró fecha de despacho en trazabilidad")
            logger.warning("⚠️ Usando fecha/hora actual como fallback")
            fecha_despacho = ahora
        
        # Obtener tiempo de viaje (maneja automáticamente departamentos)
        tiempo_viaje = obtener_tiempo_viaje(origen, destino)
        logger.info(f"⏱️ Tiempo estimado de viaje: {tiempo_viaje} horas")
        
        # Calcular cuándo debería llegar (100% del tiempo)
        tiempo_llegada_esperado = fecha_despacho + timedelta(hours=tiempo_viaje)
        
        logger.info(f"⏰ Hora actual del servidor: {ahora}")
        logger.info(f"🎯 Hora de llegada esperada: {tiempo_llegada_esperado}")
        
        # ✅ CASO 1: Si YA PASÓ el 100% del tiempo (guía retrasada)
        if ahora > tiempo_llegada_esperado:
            logger.warning(f"⚠️ El tiempo estimado de viaje (100%) ya pasó completo")
            logger.warning(f"⏰ Debió llegar a las {tiempo_llegada_esperado}, pero aún no llegó")
            logger.info(f"🔄 Guía retrasada - Verificando cada 1 HORA")
            proxima = ahora + timedelta(hours=1)
            logger.info(f"📅 Próxima verificación: {proxima}")
            return proxima
        
        # ✅ CASO 2: Calcular el 90% del tiempo
        horas_hasta_90 = tiempo_viaje * 0.9
        hora_90_porciento = fecha_despacho + timedelta(hours=horas_hasta_90)
        
        # Si es la primera verificación y aún NO ha llegado al 90%
        if verificaciones_realizadas == 0 and ahora < hora_90_porciento:
            logger.info(
                f"📅 Primera verificación programada al 90%:\n"
                f"   - Fecha despacho: {fecha_despacho}\n"
                f"   - Tiempo total viaje: {tiempo_viaje}h\n"
                f"   - Esperar hasta 90%: {horas_hasta_90:.1f}h\n"
                f"   - Próxima verificación: {hora_90_porciento}"
            )
            return hora_90_porciento
        
        # ✅ CASO 3: Ya pasó el 90% pero NO el 100% (entre 90% y 100%)
        # O es una verificación subsiguiente
        # En ambos casos: verificar cada 30 MINUTOS
        proxima = ahora + timedelta(minutes=30)
        tiempo_restante = (tiempo_llegada_esperado - ahora).total_seconds() / 3600
        logger.info(f"📅 Verificación cada 30 MINUTOS: {proxima}")
        logger.info(f"⏱️ Tiempo restante hasta llegada esperada: {tiempo_restante:.1f}h")
        return proxima
        
    except Exception as e:
        logger.error(f"❌ Error calculando próxima verificación: {e}")
        # En caso de error, verificar en 30 minutos
        ahora = datetime.now()
        return ahora + timedelta(minutes=30)


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
