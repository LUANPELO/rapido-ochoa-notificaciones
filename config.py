"""
Configuración centralizada del sistema de notificaciones Rápido Ochoa
"""
import os
import logging
from typing import Tuple

# ===== ONESIGNAL - CONFIGURACIÓN SEGURA =====
# ✅ Las API keys se leen desde variables de entorno (Render)
# ❌ NUNCA hardcodear las keys aquí por seguridad
ONESIGNAL_API_KEY = os.environ.get("ONESIGNAL_API_KEY", "")
ONESIGNAL_APP_ID = os.environ.get("ONESIGNAL_APP_ID", "")

# Validar que las variables estén configuradas
if not ONESIGNAL_API_KEY or not ONESIGNAL_APP_ID:
    logging.warning("⚠️ OneSignal no configurado - Variables de entorno faltantes")

# ===== API DE RASTREO =====
RASTREO_API_URL = os.environ.get(
    "RASTREO_API_URL",
    "https://api-buses-fkpk.onrender.com/api/rastreo"
)

# ===== CONFIGURACIÓN DE TIEMPOS =====
HORAS_ANTES_LLEGADA = 4
HORAS_ENTRE_VERIFICACIONES = 2

# ===== TIEMPOS DE VIAJE ENTRE CIUDADES =====
# Diccionario con tiempos estimados en horas
# Formato: (CIUDAD_ORIGEN, CIUDAD_DESTINO): horas
TIEMPOS_VIAJE = {
    # Rutas principales - Bogotá
    ("BOGOTA", "MEDELLIN"): 10,
    ("MEDELLIN", "BOGOTA"): 10,
    ("BOGOTA", "CALI"): 10,
    ("CALI", "BOGOTA"): 10,
    ("BOGOTA", "BARRANQUILLA"): 18,
    ("BARRANQUILLA", "BOGOTA"): 18,
    ("BOGOTA", "BUCARAMANGA"): 8,
    ("BUCARAMANGA", "BOGOTA"): 8,
    
    # Rutas principales - Medellín
    ("MEDELLIN", "BARRANQUILLA"): 16,
    ("BARRANQUILLA", "MEDELLIN"): 16,
    ("MEDELLIN", "CALI"): 8,
    ("CALI", "MEDELLIN"): 8,
    ("MEDELLIN", "PEREIRA"): 5,
    ("PEREIRA", "MEDELLIN"): 5,
    ("MEDELLIN", "SINCELEJO"): 12,
    ("SINCELEJO", "MEDELLIN"): 12,
    ("MEDELLIN", "CARTAGENA"): 14,
    ("CARTAGENA", "MEDELLIN"): 14,
    ("MEDELLIN", "CAUCASIA"): 8,
    ("CAUCASIA", "MEDELLIN"): 8,
    ("MEDELLIN", "PLANETA RICA"): 10,
    ("PLANETA RICA", "MEDELLIN"): 10,
    ("MEDELLIN", "MAICAO"): 22,
    ("MAICAO", "MEDELLIN"): 22,
    ("MEDELLIN", "SAHAGUN"): 10,
    ("SAHAGUN", "MEDELLIN"): 10,
    ("MEDELLIN", "TOLU"): 11,
    ("TOLU", "MEDELLIN"): 11,
    ("MEDELLIN", "QUIBDO"): 11,
    ("QUIBDO", "MEDELLIN"): 11,
    ("MEDELLIN", "RIOHACHA"): 16,
    ("RIOHACHA", "MEDELLIN"): 16,
    
    # Rutas principales - Barranquilla
    ("BARRANQUILLA", "SINCELEJO"): 4,
    ("SINCELEJO", "BARRANQUILLA"): 4,
    ("BARRANQUILLA", "CALI"): 20,
    ("CALI", "BARRANQUILLA"): 20,
    ("BARRANQUILLA", "CAUCASIA"): 8,
    ("CAUCASIA", "BARRANQUILLA"): 8,
    ("BARRANQUILLA", "PLANETA RICA"): 6,
    ("PLANETA RICA", "BARRANQUILLA"): 6,
    ("BARRANQUILLA", "MAICAO"): 7,
    ("MAICAO", "BARRANQUILLA"): 7,
    ("BARRANQUILLA", "LA APARTADA"): 7,
    ("LA APARTADA", "BARRANQUILLA"): 7,
    ("BARRANQUILLA", "SANTA MARTA"): 3,
    ("SANTA MARTA", "BARRANQUILLA"): 3,
    ("BARRANQUILLA", "RIOHACHA"): 5,
    ("RIOHACHA", "BARRANQUILLA"): 5,
    ("BARRANQUILLA", "YARUMAL"): 13,
    ("YARUMAL", "BARRANQUILLA"): 13,
    ("BARRANQUILLA", "SAHAGUN"): 7,
    ("SAHAGUN", "BARRANQUILLA"): 7,
    
    # Rutas Costa - Caucasia
    ("CAUCASIA", "SINCELEJO"): 4,
    ("SINCELEJO", "CAUCASIA"): 4,
    ("CAUCASIA", "SANTA MARTA"): 11,
    ("SANTA MARTA", "CAUCASIA"): 11,
    ("CAUCASIA", "MAICAO"): 15,
    ("MAICAO", "CAUCASIA"): 15,
    ("CAUCASIA", "PLANETA RICA"): 2,
    ("PLANETA RICA", "CAUCASIA"): 2,
    
    # Rutas Costa - Santa Marta
    ("SANTA MARTA", "SINCELEJO"): 7,
    ("SINCELEJO", "SANTA MARTA"): 7,
    ("SANTA MARTA", "PLANETA RICA"): 7,
    ("PLANETA RICA", "SANTA MARTA"): 7,
    ("SANTA MARTA", "MAICAO"): 4,
    ("MAICAO", "SANTA MARTA"): 4,
}

# ===== NORMALIZACIÓN DE CIUDADES =====
# Diccionario para convertir nombres de ciudades a formato estándar
CIUDADES_NORMALIZE = {
    # Ciudades principales
    "medellin": "MEDELLIN",
    "medellín": "MEDELLIN",
    "barranquilla": "BARRANQUILLA",
    "bogota": "BOGOTA",
    "bogotá": "BOGOTA",
    "cali": "CALI",
    "sincelejo": "SINCELEJO",
    "bucaramanga": "BUCARAMANGA",
    "pereira": "PEREIRA",
    "cartagena": "CARTAGENA",
    
    # Ciudades costa y norte
    "maicao": "MAICAO",
    "caucasia": "CAUCASIA",
    "planeta rica": "PLANETA RICA",
    "planetarica": "PLANETA RICA",
    "la apartada": "LA APARTADA",
    "apartada": "LA APARTADA",
    "santa marta": "SANTA MARTA",
    "santamarta": "SANTA MARTA",
    "riohacha": "RIOHACHA",
    "yarumal": "YARUMAL",
    "sahagun": "SAHAGUN",
    "sahagún": "SAHAGUN",
    
    # Ciudades pacífico
    "tolu": "TOLU",
    "tolú": "TOLU",
    "quibdo": "QUIBDO",
    "quibdó": "QUIBDO",
}


def normalizar_ciudad(ciudad: str) -> str:
    """
    Normaliza el nombre de una ciudad a formato estándar (mayúsculas)
    
    Args:
        ciudad: Nombre de la ciudad en cualquier formato
    
    Returns:
        Nombre de la ciudad normalizado en mayúsculas
        
    Examples:
        >>> normalizar_ciudad("medellín")
        'MEDELLIN'
        >>> normalizar_ciudad("Planeta Rica")
        'PLANETA RICA'
        >>> normalizar_ciudad("BOGOTA")
        'BOGOTA'
    """
    if not ciudad:
        return ""
    
    # Convertir a minúsculas y quitar espacios extra
    ciudad_lower = ciudad.lower().strip()
    
    # Buscar en el diccionario de normalización
    return CIUDADES_NORMALIZE.get(ciudad_lower, ciudad.upper())


def limpiar_nombre_ciudad(ciudad: str) -> str:
    """
    Elimina el departamento entre paréntesis y normaliza el nombre
    
    Args:
        ciudad: Nombre con formato "CIUDAD (DEPARTAMENTO)"
    
    Returns:
        Nombre de ciudad limpio y normalizado
        
    Examples:
        >>> limpiar_nombre_ciudad("MEDELLIN (ANTIOQUIA)")
        'MEDELLIN'
        >>> limpiar_nombre_ciudad("RIOHACHA (LA GUAJIRA)")
        'RIOHACHA'
        >>> limpiar_nombre_ciudad("BOGOTA")
        'BOGOTA'
    """
    if not ciudad:
        return ""
    
    # Eliminar texto entre paréntesis: "CIUDAD (DEPTO)" -> "CIUDAD"
    ciudad_limpia = ciudad.split('(')[0].strip()
    
    # Normalizar usando la función existente
    return normalizar_ciudad(ciudad_limpia)


def obtener_tiempo_viaje(origen: str, destino: str) -> int:
    """
    Obtiene el tiempo de viaje entre dos ciudades
    Maneja automáticamente nombres con departamentos: "CIUDAD (DEPTO)"
    
    Args:
        origen: Ciudad de origen (puede incluir departamento)
        destino: Ciudad de destino (puede incluir departamento)
    
    Returns:
        Tiempo de viaje en horas, o tiempo por defecto si no se encuentra
        
    Examples:
        >>> obtener_tiempo_viaje("MEDELLIN (ANTIOQUIA)", "RIOHACHA (LA GUAJIRA)")
        16
        >>> obtener_tiempo_viaje("MEDELLIN", "RIOHACHA")
        16
        >>> obtener_tiempo_viaje("BOGOTA", "CALI")
        10
    """
    # Limpiar nombres de ciudades (elimina departamentos)
    origen_limpio = limpiar_nombre_ciudad(origen)
    destino_limpio = limpiar_nombre_ciudad(destino)
    
    # Buscar en el diccionario
    ruta = (origen_limpio, destino_limpio)
    
    # Si existe la ruta, devolverla
    if ruta in TIEMPOS_VIAJE:
        return TIEMPOS_VIAJE[ruta]
    
    # Si no existe, usar tiempo por defecto (12 horas)
    logging.warning(
        f"⚠️ Ruta {origen_limpio} -> {destino_limpio} no encontrada, "
        f"usando tiempo por defecto de 12 horas"
    )
    return 12
