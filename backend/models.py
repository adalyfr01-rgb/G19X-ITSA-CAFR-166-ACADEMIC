from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from database import Base


# ==========================================
# ESTRUCTURA ORGANIZACIONAL (RRHH)
# ==========================================

class Departamento(Base):
    __tablename__ = "departamentos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    puestos = relationship("Puesto", back_populates="departamento")


class Puesto(Base):
    __tablename__ = "puestos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    departamento_id = Column(Integer, ForeignKey("departamentos.id"), nullable=False)

    departamento = relationship("Departamento", back_populates="puestos")


# ==========================================
# USUARIOS Y AUTENTICACIÓN
# ==========================================

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    rol = Column(String(50), default="empleado") 
    departamento = Column(String(100), nullable=True) 
    puesto = Column(String(100), nullable=True)       
    diagnosticos = relationship("Diagnostico", back_populates="usuario")
    rutas = relationship("RutaAprendizaje", back_populates="usuario")
    progresos = relationship("ProgresoCurso", back_populates="usuario")


# ==========================================
# DIAGNÓSTICO E IA
# ==========================================

class Pregunta(Base):
    __tablename__ = "preguntas"

    id = Column(Integer, primary_key=True, index=True)
    puesto = Column(String, nullable=False)           
    texto = Column(String, nullable=False)           
    opciones = Column(JSON, nullable=False)          
    opcion_correcta = Column(Integer, nullable=False)
    categoria = Column(String, nullable=True)        


class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    puesto_evaluado = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="diagnosticos")


class RutaAprendizaje(Base):
    __tablename__ = "rutas_aprendizaje"

    id_ruta = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    orden_secuencia_json = Column(JSON, nullable=False)
    fecha_asignacion = Column(Date, default=date.today)

    usuario = relationship("Usuario", back_populates="rutas")


# ==========================================
# CURSOS, REPRODUCTOR Y SEGUIMIENTO xAPI
# ==========================================

class Curso(Base):
    __tablename__ = "cursos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    duracion = Column(String(50), nullable=False)   
    nivel = Column(String(50), nullable=False)       
    categoria = Column(String(100), nullable=False) 
    puesto_id = Column(String(50), index=True, nullable=False) 
    url_contenido = Column(String(500), nullable=True) 
    tipo_contenido = Column(String(50), default="VIDEO") 


class ProgresoCurso(Base):
    __tablename__ = "progreso_cursos"

    id_progreso = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    id_curso = Column(Integer, ForeignKey("cursos.id"), nullable=False)
    estatus = Column(String(50), default="Pendiente")  
    calificacion = Column(Float, nullable=True)
    fecha_inicio = Column(DateTime, default=datetime.utcnow)
    fecha_completado = Column(DateTime, nullable=True)

    usuario = relationship("Usuario", back_populates="progresos")
    curso = relationship("Curso")


class XAPIStatement(Base):
    """
    Tabla para almacenar eventos oficiales de xAPI (Learning Record Store simplificado)
    """
    __tablename__ = "xapi_statements"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    verb = Column(String(100), nullable=False)  
    object_id = Column(String(255), nullable=False) 
    statement_json = Column(JSON, nullable=False) 
    timestamp = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario")
    
class EvaluacionResultado(Base):
    __tablename__ = "evaluaciones_resultados"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    puntaje = Column(Float, nullable=False)
    aciertos = Column(Integer, nullable=False)
    total_preguntas = Column(Integer, nullable=False)
    aprobado = Column(Boolean, default=False)
    intentos_restantes = Column(Integer, default=3)
    fecha_evaluacion = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario")