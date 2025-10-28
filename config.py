"""
Configuración del sistema
Incluye tiempos de viaje entre ciudades principales de Colombia
"""

import os

# ============ CONFIGURACIÓN GENERAL ============

# OneSignal Push Notifications
ONESIGNAL_API_KEY = os.environ.get("ONESIGNAL_API_KEY", "")
ONESIGNAL_APP_ID = os.environ.get("ONESIGNAL_APP_ID", "")
ONESIGNAL_API_URL = "https://onesignal.com/api/v1/notifications"

# URL de la API de rastreo (tu API existente)
RASTREO_API_URL = os.environ.get(
    "RASTREO_API_URL",
    "https://rapido-ochoa-api-fast.onrender.com/api/rastreo"
)

# Configuración de verificaciones
HORAS_ANTES_LLEGADA = 3  # Verificar 3 horas antes del tiempo estimado
HORAS_ENTRE_VERIFICACIONES = 2  # Cada 2 horas después
HORAS_LIMPIEZA_DESPUES_ENTREGA = 48  # Borrar registro 48h después de entregado

# ============ TIEMPOS DE VIAJE ENTRE CIUDADES ============
# Formato: (CIUDAD_ORIGEN, CIUDAD_DESTINO): HORAS_APROXIMADAS

TIEMPOS_VIAJE = {
    # === RUTAS DE RÁPIDO OCHOA ===
    # Basado en tiempos reales de la empresa (2025)
    
    # Desde BARRANQUILLA
    ("BARRANQUILLA", "MEDELLIN"): 16,
    ("BARRANQUILLA", "BOGOTA"): 18,
    ("BARRANQUILLA", "CARTAGENA"): 2,
    ("BARRANQUILLA", "SANTA MARTA"): 2,
    ("BARRANQUILLA", "VALLEDUPAR"): 5,
    ("BARRANQUILLA", "MONTERIA"): 6,
    ("BARRANQUILLA", "SINCELEJO"): 4,
    ("BARRANQUILLA", "RIOHACHA"): 3,
    ("BARRANQUILLA", "MAICAO"): 5,
    ("BARRANQUILLA", "CALI"): 20,
    
    # Desde MEDELLIN
    ("MEDELLIN", "BARRANQUILLA"): 16,
    ("MEDELLIN", "BOGOTA"): 10,
    ("MEDELLIN", "CARTAGENA"): 16,
    ("MEDELLIN", "SANTA MARTA"): 17,
    ("MEDELLIN", "MONTERIA"): 9,
    ("MEDELLIN", "TOLU"): 11,
    ("MEDELLIN", "SINCELEJO"): 10,
    ("MEDELLIN", "CALI"): 8,
    ("MEDELLIN", "CAUCASIA"): 5,
    ("MEDELLIN", "QUIBDO"): 8,
    ("MEDELLIN", "PEREIRA"): 5,
    ("MEDELLIN", "BUCARAMANGA"): 12,
    ("MEDELLIN", "PUERTO BERRIO"): 4,
    ("MEDELLIN", "JARDIN"): 3,
    ("MEDELLIN", "URRAO"): 4,
    
    # Desde BOGOTA
    ("BOGOTA", "MEDELLIN"): 10,
    ("BOGOTA", "BARRANQUILLA"): 18,
    ("BOGOTA", "CARTAGENA"): 20,
    ("BOGOTA", "BUCARAMANGA"): 8,
    ("BOGOTA", "PEREIRA"): 8,
    ("BOGOTA", "CALI"): 10,
    ("BOGOTA", "TOLU"): 23,
    ("BOGOTA", "MONTERIA"): 19,
    ("BOGOTA", "SANTA MARTA"): 20,
    ("BOGOTA", "SINCELEJO"): 18,
    
    # Desde CARTAGENA
    ("CARTAGENA", "MEDELLIN"): 16,
    ("CARTAGENA", "BARRANQUILLA"): 2,
    ("CARTAGENA", "BOGOTA"): 20,
    ("CARTAGENA", "MONTERIA"): 6,
    ("CARTAGENA", "SINCELEJO"): 3,
    ("CARTAGENA", "SANTA MARTA"): 4,
    ("CARTAGENA", "TOLU"): 3,
    
    # Desde SANTA MARTA
    ("SANTA MARTA", "MEDELLIN"): 17,
    ("SANTA MARTA", "BARRANQUILLA"): 2,
    ("SANTA MARTA", "CARTAGENA"): 4,
    ("SANTA MARTA", "BOGOTA"): 20,
    ("SANTA MARTA", "VALLEDUPAR"): 4,
    ("SANTA MARTA", "RIOHACHA"): 3,
    
    # Desde MONTERIA
    ("MONTERIA", "BARRANQUILLA"): 6,
    ("MONTERIA", "MEDELLIN"): 9,
    ("MONTERIA", "CARTAGENA"): 6,
    ("MONTERIA", "SINCELEJO"): 3,
    ("MONTERIA", "BOGOTA"): 19,
    ("MONTERIA", "CAUCASIA"): 4,
    ("MONTERIA", "PLANETA RICA"): 2,
    
    # Desde SINCELEJO
    ("SINCELEJO", "BARRANQUILLA"): 4,
    ("SINCELEJO", "CARTAGENA"): 3,
    ("SINCELEJO", "MONTERIA"): 3,
    ("SINCELEJO", "MEDELLIN"): 10,
    ("SINCELEJO", "BOGOTA"): 18,
    ("SINCELEJO", "TOLU"): 1,
    
    # Desde TOLU (Santiago de Tolú)
    ("TOLU", "MEDELLIN"): 11,
    ("TOLU", "BOGOTA"): 23,
    ("TOLU", "CARTAGENA"): 3,
    ("TOLU", "BARRANQUILLA"): 5,
    ("TOLU", "SINCELEJO"): 1,
    ("TOLU", "COVENAS"): 1,
    
    # Desde CALI
    ("CALI", "MEDELLIN"): 8,
    ("CALI", "BOGOTA"): 10,
    ("CALI", "BARRANQUILLA"): 20,
    ("CALI", "PEREIRA"): 4,
    
    # Desde CAUCASIA
    ("CAUCASIA", "MEDELLIN"): 5,
    ("CAUCASIA", "MONTERIA"): 4,
    ("CAUCASIA", "BOGOTA"): 14,
    ("CAUCASIA", "CARTAGENA"): 10,
    
    # Desde QUIBDO
    ("QUIBDO", "MEDELLIN"): 8,
    
    # Desde PEREIRA
    ("PEREIRA", "MEDELLIN"): 5,
    ("PEREIRA", "BOGOTA"): 8,
    ("PEREIRA", "CALI"): 4,
    
    # Desde BUCARAMANGA
    ("BUCARAMANGA", "BOGOTA"): 8,
    ("BUCARAMANGA", "MEDELLIN"): 12,
    ("BUCARAMANGA", "BARRANQUILLA"): 10,
    
    # Desde VALLEDUPAR
    ("VALLEDUPAR", "BARRANQUILLA"): 5,
    ("VALLEDUPAR", "SANTA MARTA"): 4,
    ("VALLEDUPAR", "RIOHACHA"): 4,
    
    # Desde RIOHACHA
    ("RIOHACHA", "BARRANQUILLA"): 3,
    ("RIOHACHA", "SANTA MARTA"): 3,
    ("RIOHACHA", "MAICAO"): 2,
    ("RIOHACHA", "VALLEDUPAR"): 4,
    
    # Desde MAICAO
    ("MAICAO", "BARRANQUILLA"): 5,
    ("MAICAO", "RIOHACHA"): 2,
    ("MAICAO", "MEDELLIN"): 18,
    
    # Desde AGUACHICA
    ("AGUACHICA", "BUCARAMANGA"): 4,
    ("AGUACHICA", "BOGOTA"): 10,
    
    # Pequeños municipios Antioquia
    ("PUERTO BERRIO", "MEDELLIN"): 4,
    ("JARDIN", "MEDELLIN"): 3,
    ("URRAO", "MEDELLIN"): 4,
    ("GIRALDO", "MEDELLIN"): 4,
    ("BETULIA", "MEDELLIN"): 3,
    ("CONCORDIA", "MEDELLIN"): 4,
    ("CIUDAD BOLIVAR", "MEDELLIN"): 3,
    ("ARBOLETES", "MEDELLIN"): 5,
    ("PLANETA RICA", "MONTERIA"): 2,
    ("COVENAS", "TOLU"): 1,
    ("SAN ONOFRE", "SINCELEJO"): 2,
}

# ============ NORMALIZACIÓN DE NOMBRES DE CIUDADES ============
# Para manejar variaciones en cómo aparecen los nombres en el sistema de Rápido Ochoa

CIUDADES_NORMALIZE = {
    # Costa Atlántica
    "BARRANQUILLA": ["BARRANQUILLA", "BARRANQUILLA (ATLANTICO)", "ATLANTICO"],
    "CARTAGENA": ["CARTAGENA", "CARTAGENA (BOLIVAR)", "BOLIVAR"],
    "SANTA MARTA": ["SANTA MARTA", "SANTA MARTA (MAGDALENA)", "MAGDALENA"],
    "SINCELEJO": ["SINCELEJO", "SINCELEJO (SUCRE)", "SUCRE"],
    "MONTERIA": ["MONTERIA", "MONTERIA (CORDOBA)", "CORDOBA"],
    "VALLEDUPAR": ["VALLEDUPAR", "VALLEDUPAR (CESAR)", "CESAR"],
    "RIOHACHA": ["RIOHACHA", "RIOHACHA (LA GUAJIRA)", "LA GUAJIRA"],
    "MAICAO": ["MAICAO", "MAICAO (LA GUAJIRA)"],
    "TOLU": ["TOLU", "SANTIAGO DE TOLU", "TOLU (SUCRE)"],
    "COVENAS": ["COVENAS", "COVENAS (SUCRE)"],
    "SAN ONOFRE": ["SAN ONOFRE", "SAN ONOFRE (SUCRE)"],
    "LORICA": ["LORICA", "LORICA (CORDOBA)"],
    "SAHAGUN": ["SAHAGUN", "SAHAGUN (CORDOBA)"],
    "PLANETA RICA": ["PLANETA RICA", "PLANETA RICA (CORDOBA)"],
    
    # Antioquia
    "MEDELLIN": ["MEDELLIN", "MEDELLIN (ANTIOQUIA)", "ANTIOQUIA"],
    "CAUCASIA": ["CAUCASIA", "CAUCASIA (ANTIOQUIA)"],
    "PUERTO BERRIO": ["PUERTO BERRIO", "PUERTO BERRÍO", "PUERTO BERRIO (ANTIOQUIA)"],
    "JARDIN": ["JARDIN", "JARDÍN", "JARDIN (ANTIOQUIA)"],
    "URRAO": ["URRAO", "URRAO (ANTIOQUIA)"],
    "GIRALDO": ["GIRALDO", "GIRALDO (ANTIOQUIA)"],
    "BETULIA": ["BETULIA", "BETULIA (ANTIOQUIA)"],
    "CONCORDIA": ["CONCORDIA", "CONCORDIA (ANTIOQUIA)"],
    "CIUDAD BOLIVAR": ["CIUDAD BOLIVAR", "CIUDAD BOLÍVAR", "CIUDAD BOLIVAR (ANTIOQUIA)"],
    "ARBOLETES": ["ARBOLETES", "ARBOLETES (ANTIOQUIA)"],
    
    # Centro y Oriente
    "BOGOTA": ["BOGOTA", "BOGOTÁ", "BOGOTA (CUNDINAMARCA)", "CUNDINAMARCA"],
    "BUCARAMANGA": ["BUCARAMANGA", "BUCARAMANGA (SANTANDER)", "SANTANDER"],
    "AGUACHICA": ["AGUACHICA", "AGUACHICA (CESAR)"],
    
    # Eje Cafetero
    "PEREIRA": ["PEREIRA", "PEREIRA (RISARALDA)", "RISARALDA"],
    
    # Pacífico
    "CALI": ["CALI", "CALI (VALLE DEL CAUCA)", "VALLE DEL CAUCA"],
    "QUIBDO": ["QUIBDO", "QUIBDÓ", "QUIBDO (CHOCO)", "CHOCO"],
}

def normalizar_ciudad(ciudad: str) -> str:
    """
    Normaliza el nombre de una ciudad para búsqueda en TIEMPOS_VIAJE
    
    Args:
        ciudad: Nombre de la ciudad como viene del sistema (ej: "BARRANQUILLA (ATLANTICO)")
    
    Returns:
        Nombre normalizado (ej: "BARRANQUILLA")
    """
    if not ciudad:
        return ""
    
    ciudad_upper = ciudad.upper().strip()
    
    # Buscar en las variaciones
    for ciudad_base, variaciones in CIUDADES_NORMALIZE.items():
        for variacion in variaciones:
            if variacion in ciudad_upper or ciudad_upper in variacion:
                return ciudad_base
    
    # Si no se encuentra, retornar limpio (quitar paréntesis)
    import re
    ciudad_limpia = re.sub(r'\s*\([^)]*\)', '', ciudad_upper).strip()
    return ciudad_limpia