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
    
    LÓGICA CORRECTA Y DEFINITIVA:
    1. Antes del despacho: cada 30 minutos
    2. Primera verificación después del despacho: esperar al 90% del tiempo
    3. Entre 90% y 100% del tiempo: cada 30 minutos
    4. Después del 100% (guía retrasada): cada 1 HORA
    
    Args:
        estado_actual: Estado actual de la guía
        origen: Ciudad origen
        destino: Ciudad destino
        fecha_admision: Fecha de admisión
        verificaciones_realizadas: Número de verificaciones ya hechas
        trazabilidad: Lista con el historial de estados y fechas
    
    Returns:
        Datetime de la próxima verificación (en UTC para la BD) o None si ya llegó
    """
    try:
        estado_upper = estado_actual.upper() if estado_actual else ""
        
        # Convertir UTC a hora Colombia para todos los cálculos
        ahora_utc = datetime.now()
        ahora_colombia = ahora_utc - timedelta(hours=5)
        
        logger.info(f"⏰ Hora servidor UTC: {ahora_utc}")
        logger.info(f"🇨🇴 Hora Colombia: {ahora_colombia}")
        
        # CASO 1: Si ya llegó a destino, NO programar más verificaciones
        if "RECLAME EN OFICINA" in estado_upper or "ENTREGADA" in estado_upper:
            logger.info("📦 Guía ya está en RECLAME EN OFICINA, no programar verificaciones")
            return None
        
        # CASO 2: Si aún NO está despachada, verificar cada 30 minutos
        if "DESPACHO NACIONAL BUSES" not in estado_upper:
            proxima_colombia = ahora_colombia + timedelta(minutes=30)
            proxima_utc = proxima_colombia + timedelta(hours=5)
            logger.info(f"⏳ Guía sin despachar, verificar en 30 minutos")
            logger.info(f"📍 Estado actual: {estado_actual}")
            logger.info(f"📅 Próxima verificación (Colombia): {proxima_colombia}")
            return proxima_utc
        
        # CASO 3: Ya está DESPACHADA - usar estrategia inteligente
        logger.info(f"🚛 Guía DESPACHADA - Iniciando cálculo de tiempo estimado")
        
        # Buscar la fecha REAL del despacho en la trazabilidad
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
                            logger.info(f"   (Extraída de trazabilidad: {fecha_str})")
                            break
        
        # Si no se encontró, usar ahora como fallback
        if not fecha_despacho:
            logger.warning("⚠️ No se encontró fecha de despacho en trazabilidad")
            logger.warning("⚠️ Usando fecha/hora actual como fallback")
            fecha_despacho = ahora_colombia
        
        # Obtener tiempo de viaje
        tiempo_viaje = obtener_tiempo_viaje(origen, destino)
        logger.info(f"⏱️ Tiempo estimado de viaje: {tiempo_viaje} horas")
        
        # Calcular cuándo debería llegar (100% del tiempo)
        tiempo_llegada_esperado = fecha_despacho + timedelta(hours=tiempo_viaje)
        logger.info(f"🎯 Hora de llegada esperada (Colombia): {tiempo_llegada_esperado}")
        
        # CASO 4: Si YA PASÓ el 100% del tiempo (guía retrasada)
        # LÓGICA: Verificar cada 1 HORA
        if ahora_colombia > tiempo_llegada_esperado:
            logger.warning(f"⚠️ El tiempo estimado de viaje (100%) ya pasó completo")
            logger.warning(f"⏰ Debió llegar a las {tiempo_llegada_esperado} (Colombia)")
            logger.info(f"🔄 Guía retrasada - Verificando cada 1 HORA")
            
            # ✅ CADA 1 HORA cuando está retrasada
            proxima_colombia = ahora_colombia + timedelta(hours=1)
            proxima_utc = proxima_colombia + timedelta(hours=5)
            logger.info(f"📅 Próxima verificación (Colombia): {proxima_colombia}")
            return proxima_utc
        
        # CASO 5: Calcular el 90% del tiempo
        horas_hasta_90 = tiempo_viaje * 0.9
        hora_90_porciento = fecha_despacho + timedelta(hours=horas_hasta_90)
        
        # Si es la PRIMERA verificación y aún NO ha llegado al 90%
        # LÓGICA: Esperar hasta el 90%
        if verificaciones_realizadas == 0 and ahora_colombia < hora_90_porciento:
            logger.info(
                f"📅 Primera verificación programada al 90%:\n"
                f"   - Fecha despacho (Colombia): {fecha_despacho}\n"
                f"   - Tiempo total viaje: {tiempo_viaje}h\n"
                f"   - Esperar hasta 90%: {horas_hasta_90:.1f}h\n"
                f"   - Próxima verificación (Colombia): {hora_90_porciento}"
            )
            proxima_utc = hora_90_porciento + timedelta(hours=5)
            return proxima_utc
        
        # CASO 6: Ya pasó el 90% pero NO el 100% (entre 90% y 100%)
        # O es una verificación subsiguiente
        # LÓGICA: Verificar cada 30 MINUTOS
        proxima_colombia = ahora_colombia + timedelta(minutes=30)
        proxima_utc = proxima_colombia + timedelta(hours=5)
        tiempo_restante = (tiempo_llegada_esperado - ahora_colombia).total_seconds() / 3600
        
        logger.info(f"📅 Verificación cada 30 MINUTOS (Colombia): {proxima_colombia}")
        logger.info(f"⏱️ Tiempo restante hasta llegada: {tiempo_restante:.1f}h")
        return proxima_utc
        
    except Exception as e:
        logger.error(f"❌ Error calculando próxima verificación: {e}")
        # En caso de error, verificar en 30 minutos
        ahora_utc = datetime.now()
        ahora_colombia = ahora_utc - timedelta(hours=5)
        proxima_utc = ahora_colombia + timedelta(minutes=30) + timedelta(hours=5)
        return proxima_utc


# ============ ONESIGNAL PUSH NOTIFICATIONS ============

def enviar_push_notification(
    onesignal_user_id: str, 
    titulo: str, 
    mensaje: str, 
    datos_extra: dict = None
) -> bool:
    """
    Envía notificación push usando OneSignal Player ID (API V1)
    
    CRÍTICO: USA "include_player_ids" que es compatible con API V1
    NO usa "include_aliases" que causaba el error
    
    Args:
        onesignal_user_id: OneSignal Player ID (UUID)
        titulo: Título de la notificación
        mensaje: Mensaje de la notificación
        datos_extra: Datos adicionales (opcional)
    
    Returns:
        True si se envió exitosamente, False en caso contrario
    """
    import re
    
    try:
        if not ONESIGNAL_API_KEY or not ONESIGNAL_APP_ID:
            logger.warning("⚠️ OneSignal no configurado")
            return False
        
        if not onesignal_user_id or onesignal_user_id.strip() == "":
            logger.error("❌ OneSignal Player ID está vacío")
            return False
        
        # Validar formato UUID del Player ID
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
        
        # ✅ CRÍTICO: Usar include_player_ids para API V1
        payload = {
            "app_id": ONESIGNAL_APP_ID,
            "include_player_ids": [onesignal_user_id],
            "headings": {"en": titulo},
            "contents": {"en": mensaje},
            "priority": 10
        }
        
        if datos_extra:
            payload["data"] = datos_extra
            logger.info(f"📦 Datos extra incluidos: {datos_extra}")
        
        logger.info(f"📡 Enviando a OneSignal API...")
        
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
                logger.info(f"✅ Push enviado exitosamente")
                logger.info(f"📊 Recipients: {recipients}")
                logger.info(f"📋 Notification ID: {result.get('id', 'N/A')}")
                return True
            else:
                logger.warning(f"⚠️ OneSignal: No se pudo enviar (sin recipients)")
                logger.warning(f"📄 Response: {result}")
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
    """
    import re
    if not numero_guia:
        return False
    
    patron = r'^[A-Z]?\d{8,10}$'
    return bool(re.match(patron, numero_guia.upper()))


def parsear_fecha_admision(fecha_str: str) -> Optional[datetime]:
    """
    Parsea la fecha de admisión del formato de Rápido Ochoa
    """
    try:
        return datetime.strptime(fecha_str, "%Y/%m/%d %H:%M")
    except:
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        except:
            logger.warning(f"⚠️ No se pudo parsear fecha: {fecha_str}")
            return None
