"""
Modelos de Base de Datos PostgreSQL
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# URL de conexión a PostgreSQL
# En Render, la variable DATABASE_URL se configura automáticamente
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/rastreo_db"
)

# Render usa postgres:// pero SQLAlchemy necesita postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============ MODELOS ============

class Suscripcion(Base):
    """
    Tabla principal de suscripciones a notificaciones
    """
    __tablename__ = "suscripciones"
    
    # Identificación
    id = Column(Integer, primary_key=True, index=True)
    numero_guia = Column(String(50), nullable=False, index=True)
    token_fcm = Column(String(255), nullable=False)  # Token de Firebase Cloud Messaging
    telefono = Column(String(20), nullable=True)
    
    # Información de la guía
    origen = Column(String(100), nullable=True)
    destino = Column(String(100), nullable=True)
    estado_actual = Column(String(100), nullable=True)
    fecha_admision = Column(String(50), nullable=True)  # Formato: "2025/10/03 13:07"
    
    # Información de personas
    remitente = Column(String(200), nullable=True)
    destinatario = Column(String(200), nullable=True)
    
    # Control de verificaciones
    fecha_creacion = Column(DateTime, default=datetime.now, nullable=False)
    ultima_verificacion = Column(DateTime, nullable=True)
    proxima_verificacion = Column(DateTime, nullable=True, index=True)
    verificaciones_realizadas = Column(Integer, default=0)
    
    # Estado de la suscripción
    activo = Column(Boolean, default=True, index=True)
    fecha_entrega = Column(DateTime, nullable=True)  # Cuando llega a RECLAME EN OFICINA
    
    # Relación con historial
    historial = relationship("HistorialVerificacion", back_populates="suscripcion", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Suscripcion {self.numero_guia} - {self.estado_actual}>"


class HistorialVerificacion(Base):
    """
    Registro de cada verificación realizada
    Útil para análisis y debugging
    """
    __tablename__ = "historial_verificaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    suscripcion_id = Column(Integer, ForeignKey("suscripciones.id"), nullable=False, index=True)
    
    fecha_verificacion = Column(DateTime, default=datetime.now, nullable=False)
    estado_encontrado = Column(String(100), nullable=True)
    
    # Relación
    suscripcion = relationship("Suscripcion", back_populates="historial")
    
    def __repr__(self):
        return f"<Verificacion {self.suscripcion_id} - {self.estado_encontrado}>"


class ConfiguracionCiudad(Base):
    """
    Tabla para almacenar tiempos de viaje entre ciudades
    Opcional: se puede usar para hacer el sistema más dinámico
    """
    __tablename__ = "configuracion_ciudades"
    
    id = Column(Integer, primary_key=True, index=True)
    origen = Column(String(100), nullable=False, index=True)
    destino = Column(String(100), nullable=False, index=True)
    horas_viaje = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<ConfigCiudad {self.origen} -> {self.destino}: {self.horas_viaje}h>"


# ============ FUNCIONES DE INICIALIZACIÓN ============

def init_db():
    """
    Crea todas las tablas en la base de datos
    Se ejecuta al iniciar la aplicación
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🔧 Creando tablas en PostgreSQL...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
        
        # Opcional: Insertar datos iniciales de ciudades
        _insertar_datos_ciudades()
        
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        raise


def _insertar_datos_ciudades():
    """
    Inserta configuración inicial de tiempos entre ciudades
    Solo si la tabla está vacía
    """
    import logging
    logger = logging.getLogger(__name__)
    
    db = SessionLocal()
    
    try:
        # Verificar si ya hay datos
        count = db.query(ConfiguracionCiudad).count()
        
        if count > 0:
            logger.info("ℹ️ Configuración de ciudades ya existe")
            return
        
        logger.info("📍 Insertando configuración de ciudades...")
        
        # Datos iniciales (puedes agregar más)
        ciudades_config = [
            ("MEDELLIN", "BARRANQUILLA", 16),
            ("BARRANQUILLA", "MEDELLIN", 16),
            ("BARRANQUILLA", "SINCELEJO", 4),
            ("SINCELEJO", "BARRANQUILLA", 4),
            ("BOGOTA", "MEDELLIN", 10),
            ("MEDELLIN", "BOGOTA", 10),
            ("BOGOTA", "CALI", 10),
            ("CALI", "BOGOTA", 10),
            ("BOGOTA", "BARRANQUILLA", 18),
            ("BARRANQUILLA", "BOGOTA", 18),
            ("MEDELLIN", "CALI", 8),
            ("CALI", "MEDELLIN", 8),
            ("CALI", "BARRANQUILLA", 20),
            ("BARRANQUILLA", "CALI", 20),
            ("BOGOTA", "BUCARAMANGA", 8),
            ("BUCARAMANGA", "BOGOTA", 8),
            ("MEDELLIN", "PEREIRA", 5),
            ("PEREIRA", "MEDELLIN", 5),
        ]
        
        for origen, destino, horas in ciudades_config:
            config = ConfiguracionCiudad(
                origen=origen,
                destino=destino,
                horas_viaje=horas
            )
            db.add(config)
        
        db.commit()
        logger.info(f"✅ {len(ciudades_config)} configuraciones de ciudades insertadas")
        
    except Exception as e:
        logger.error(f"❌ Error insertando ciudades: {e}")
        db.rollback()
    finally:
        db.close()


def get_tiempo_viaje(origen: str, destino: str) -> int:
    """
    Obtiene el tiempo de viaje entre dos ciudades desde la BD
    Si no existe, retorna un valor por defecto
    """
    db = SessionLocal()
    
    try:
        # Normalizar nombres
        origen = origen.upper().strip()
        destino = destino.upper().strip()
        
        config = db.query(ConfiguracionCiudad).filter(
            ConfiguracionCiudad.origen == origen,
            ConfiguracionCiudad.destino == destino
        ).first()
        
        if config:
            return config.horas_viaje
        
        # Valor por defecto si no se encuentra
        return 12  # 12 horas por defecto
        
    finally:
        db.close()