import os
from datetime import date, datetime, timezone
from typing import List, Optional
import json
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Base, Usuario, XAPIStatement 
import models
from database import engine, get_db
from services.ai_adapter import generar_ruta_aprendizaje, generar_evaluacion_final
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import func
from models import Curso  
from models import Usuario, Diagnostico, ProgresoCurso, XAPIStatement

# Carga de variables de entorno (.env)
load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()


class UserRegister(BaseModel):
    nombre: str
    email: str
    password: str
    rol: str = "empleado"
    departamento: str = ""
    puesto: str = ""

class LoginData(BaseModel):
    email: str
    password: str

class DiagnosticoData(BaseModel):
    email: str
    departamento: str
    puesto: str

class GenerarRutaRequest(BaseModel):
    puesto_id: str
    score: int

class GuardarDiagnosticoRequest(BaseModel):
    usuario_id: int
    puesto_id: str
    score: int

class CursoCreate(BaseModel):
    titulo: str
    descripcion: str = ""
    duracion: str
    nivel: str
    categoria: str
    puesto_id: str
    url_contenido: str = ""

class CursoResponse(CursoCreate):
    id: int

    class Config:
        from_attributes = True

class ProgresoUpdate(BaseModel):
    id_usuario: int
    id_curso: int
    accion: str  # 'launched' o 'completed'
    
class ResultadoExamenSchema(BaseModel):
    usuario_id: int
    puntaje: int
    aciertos: int
    total_preguntas: int
    aprobado: bool
    intentos_restantes: int

class XAPIStatementCreate(BaseModel):
    usuario_id: Optional[int] = None
    verb: str
    object_id: str
    statement_json: Optional[dict] = {}

class PreguntaCreateRequest(BaseModel):
    puesto: str
    texto: str
    opciones: List[str]
    opcion_correcta: int
    categoria: Optional[str] = "General"
    
PreguntaCreate = PreguntaCreateRequest

class RespuestaColaborador(BaseModel):
    pregunta_id: int
    opcion_seleccionada: int

class EvaluarDiagnosticoRequest(BaseModel):
    usuario_id: int
    puesto_id: str
    respuestas: List[RespuestaColaborador]

class PuestoCreate(BaseModel):
    nombre: str

class DepartamentoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    puestos: Optional[List[str]] = []
    

@app.get("/")
def home():
    return {"status": "API Activa", "sistema": "PluriOne Capacitaciones"}

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def registrar_usuario(data: UserRegister, db: Session = Depends(get_db)):
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == data.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")

    nuevo_usuario = models.Usuario(
        nombre=data.nombre,
        email=data.email,
        password=data.password,
        rol=data.rol,
        departamento=data.departamento,
        puesto=data.puesto
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return {
        "status": "ok",
        "mensaje": "Usuario creado exitosamente",
        "user": {
            "id": nuevo_usuario.id,
            "nombre": nuevo_usuario.nombre,
            "email": nuevo_usuario.email,
            "rol": nuevo_usuario.rol
        }
    }

@app.post("/api/auth/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == data.email).first()

    if not usuario or usuario.password != data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos."
        )

    return {
        "status": "ok",
        "user": {
            "id": usuario.id,
            "email": usuario.email,
            "nombre": usuario.nombre,
            "rol": usuario.rol,
            "departamento": usuario.departamento,
            "puesto": usuario.puesto
        }
    }

@app.get("/api/usuarios/simulador")
def obtener_usuarios_simulador(db: Session = Depends(get_db)):
    try:
        
        puestos_db = db.query(models.Puesto).all()
        puestos_map = {str(p.id): p.nombre for p in puestos_db}

        
        usuarios = db.query(models.Usuario).all()
        resultado = []
        
        for u in usuarios:
            
            val_puesto = getattr(u, 'puesto', None) or getattr(u, 'puesto_id', None)
            val_puesto_str = str(val_puesto) if val_puesto is not None else ""

            nombre_puesto = puestos_map.get(val_puesto_str, val_puesto_str or "Sin puesto")

            resultado.append({
                "id": u.id,
                "nombre": u.nombre,
                "email": u.email,
                "rol": getattr(u, 'rol', 'empleado'),
                "departamento": getattr(u, 'departamento', ''),
                "puesto": val_puesto,
                "puesto_nombre": nombre_puesto
            })
            
        return resultado

    except Exception as e:
        print("Error en /api/usuarios/simulador:", e)
        # Si ocurre cualquier error, devolvemos un listado simple para evitar el error 500
        usuarios_fallaback = db.query(models.Usuario).all()
        return [
            {
                "id": u.id,
                "nombre": u.nombre,
                "email": u.email,
                "rol": getattr(u, 'rol', 'empleado'),
                "puesto": getattr(u, 'puesto', ''),
                "puesto_nombre": getattr(u, 'puesto', '')
            }
            for u in usuarios_fallaback
        ]
    
@app.get("/api/perfiles")
def obtener_perfiles(db: Session = Depends(get_db)):
    departamentos = db.query(Departamento).all()
    
    lista_deptos = []
    puestos_dict = {}

    for dep in departamentos:
        lista_deptos.append({"id": str(dep.id), "nombre": dep.nombre})
        puestos_dict[str(dep.id)] = [
            {"id": str(p.id), "nombre": p.nombre} for p in dep.puestos
        ]

    return {
        "departamentos": lista_deptos,
        "puestos": puestos_dict
    }


@app.post("/api/rutas/generar-ia")
def generar_ruta_ia(payload: dict, db: Session = Depends(get_db)):
    puesto_id = payload.get("puesto_id")
    usuario_id = payload.get("usuario_id") 

    if not puesto_id:
        raise HTTPException(status_code=400, detail="El 'puesto_id' es requerido.")

   
    puesto_db = db.query(models.Puesto).filter(models.Puesto.id == puesto_id).first()
    
    if puesto_db:
        puesto_nombre = puesto_db.nombre
    else:
        puesto_nombre = f"Puesto #{puesto_id}"

    cursos_db = db.query(models.Curso).filter(models.Curso.puesto_id == str(puesto_id)).all()
    
    if not cursos_db:
        cursos_db = db.query(models.Curso).all()

    catalogo_cursos = [
        {
            "id": c.id,
            "titulo": c.titulo,
            "descripcion": getattr(c, 'descripcion', '') or "Sin descripción disponible.",
            "duracion": getattr(c, 'duracion', '') or "No especificada",
            "nivel": getattr(c, 'nivel', '') or "General",
            "categoria": getattr(c, 'categoria', '') or "Capacitación",
            "puesto_id": getattr(c, 'puesto_id', '') or "",
            "url_contenido": getattr(c, 'url_contenido', '') or "#",
            "tipo_contenido": getattr(c, 'tipo_contenido', '') or "Recurso"
        }
        for c in cursos_db
    ]

    try:
        resultado_ia = generar_ruta_aprendizaje(
            puesto_nombre=puesto_nombre,
            respuestas_diagnostico=payload.get("respuestas", []),
            cursos_disponibles=catalogo_cursos
        )
    except Exception as e:
        print(f"Error procesando endpoint de IA: {e}")
        resultado_ia = {
            "puesto": puesto_nombre,
            "resumen_brechas": "No se pudo procesar con IA. Cursos asignados directamente por catálogo.",
            "ruta": [
                {
                    "id_curso": c["id"],
                    "titulo": c["titulo"],
                    "tipo": "OBLIGATORIO",
                    "orden_secuencia": idx + 1,
                    "justificacion": "Asignado por catálogo por defecto",
                    "plazo_dias": 30
                }
                for idx, c in enumerate(catalogo_cursos[:4])
            ]
        }

    nueva_ruta = None
    if usuario_id:
        try:
            nueva_ruta = models.RutaAprendizaje(
                id_usuario=int(usuario_id),
                orden_secuencia_json=resultado_ia,
                fecha_asignacion=date.today()
            )
            db.add(nueva_ruta)
            db.commit()
            if nueva_ruta:
                db.refresh(nueva_ruta)

        except Exception as e:
            db.rollback()
            print(f"Error al guardar la ruta en BD: {e}")

    return {
        "status": "ok",
        "mensaje": "Ruta generada exitosamente",
        "id_ruta": nueva_ruta.id_ruta if nueva_ruta else None,
        "ruta": resultado_ia
    }

@app.post("/api/diagnostico/guardar")
def guardar_diagnostico(data: GuardarDiagnosticoRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.id == data.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="El usuario especificado no existe.")

    nuevo_diagnostico = models.Diagnostico(
        usuario_id=data.usuario_id,
        puesto_evaluado=data.puesto_id,
        score=data.score
    )

    db.add(nuevo_diagnostico)
    db.commit()
    db.refresh(nuevo_diagnostico)

    return {
        "status": "ok",
        "mensaje": "Diagnóstico registrado exitosamente",
        "diagnostico": {
            "id": nuevo_diagnostico.id,
            "usuario_id": nuevo_diagnostico.usuario_id,
            "puesto_id": nuevo_diagnostico.puesto_evaluado,
            "score": nuevo_diagnostico.score,
            "fecha": nuevo_diagnostico.fecha
        }
    }


@app.post("/api/cursos", status_code=status.HTTP_201_CREATED)
def crear_curso(curso: CursoCreate, db: Session = Depends(get_db)):
    nuevo_curso = models.Curso(**curso.model_dump())
    db.add(nuevo_curso)
    db.commit()
    db.refresh(nuevo_curso)
    return {"status": "ok", "mensaje": "Curso creado exitosamente", "curso": nuevo_curso}

@app.get("/api/cursos")
def listar_cursos(puesto_id: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Curso)
    if puesto_id:
        query = query.filter(models.Curso.puesto_id == puesto_id)
    cursos = query.all()
    return {"status": "ok", "total": len(cursos), "cursos": cursos}

@app.get("/api/cursos/{curso_id}")
def obtener_detalle_curso(curso_id: int, db: Session = Depends(get_db)):
    curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"El curso con ID {curso_id} no fue encontrado."
        )
    return curso

@app.delete("/api/cursos/{curso_id}")
def eliminar_curso(curso_id: int, db: Session = Depends(get_db)):
    curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="El curso no existe.")
    
    db.delete(curso)
    db.commit()
    return {"status": "ok", "mensaje": "Curso eliminado correctamente"}

@app.get("/api/rutas/usuario/{usuario_id}")
def obtener_ruta_usuario(usuario_id: int, db: Session = Depends(get_db)):
    # 1. Obtener la última ruta del usuario
    ruta = db.query(models.RutaAprendizaje)\
             .filter(models.RutaAprendizaje.id_usuario == usuario_id)\
             .order_by(models.RutaAprendizaje.id_ruta.desc())\
             .first()

    if not ruta:
        raise HTTPException(status_code=404, detail="El usuario no tiene una ruta de aprendizaje guardada.")

    diagnostico = db.query(models.Diagnostico)\
                    .filter(models.Diagnostico.usuario_id == usuario_id)\
                    .order_by(models.Diagnostico.id.desc())\
                    .first()

    puntaje_obtenido = diagnostico.score if diagnostico and diagnostico.score is not None else 0

    todos_los_cursos = db.query(models.Curso).all()
    
    mapa_urls = {
        c.titulo.strip().lower(): c.url_contenido 
        for c in todos_los_cursos if c.titulo and c.url_contenido
    }

    datos_json = ruta.orden_secuencia_json or {}
    
    if isinstance(datos_json, dict):
        lista_cursos_raw = datos_json.get("ruta") or datos_json.get("cursos") or []
    elif isinstance(datos_json, list):
        lista_cursos_raw = datos_json
    else:
        lista_cursos_raw = []

    cursos_enriquecidos = []
    for curso in lista_cursos_raw:
        if isinstance(curso, dict):
            titulo = (curso.get("nombre") or curso.get("titulo") or "").strip()
            url_hallada = curso.get("url_contenido")
            if not url_hallada:
                for t_db, url_db in mapa_urls.items():
                    if t_db in titulo.lower() or titulo.lower() in t_db:
                        url_hallada = url_db
                        break
            
            curso["url_contenido"] = url_hallada
            cursos_enriquecidos.append(curso)
            
        elif isinstance(curso, str):
            titulo = curso.strip()
            url_hallada = None
            for t_db, url_db in mapa_urls.items():
                if t_db in titulo.lower() or titulo.lower() in t_db:
                    url_hallada = url_db
                    break

            cursos_enriquecidos.append({
                "nombre": titulo,
                "url_contenido": url_hallada
            })

    return {
        "status": "ok",
        "id_ruta": ruta.id_ruta,
        "fecha_asignacion": ruta.fecha_asignacion,
        "puntaje": puntaje_obtenido,
        "ruta": cursos_enriquecidos
    }


def generar_xapi_statement(usuario, curso, estatus: str, calificacion: float = None):
    verbos_xapi = {
        "En progreso": {
            "id": "http://adlnet.gov/expapi/verbs/initialized",
            "display": {"es": "inicio"}
        },
        "Completado": {
            "id": "http://adlnet.gov/expapi/verbs/completed",
            "display": {"es": "completo"}
        }
    }

    verbo = verbos_xapi.get(
        estatus, 
        {"id": "http://adlnet.gov/expapi/verbs/progressed", "display": {"es": "avanzo"}}
    )

    email_usuario = getattr(usuario, 'email', None) or getattr(usuario, 'correo', None) or f"usuario{usuario.id}@plurione.com"
    nombre_usuario = getattr(usuario, 'nombre', None) or f"Usuario {usuario.id}"

    statement = {
        "actor": {
            "mbox": f"mailto:{email_usuario}",
            "name": nombre_usuario,
            "objectType": "Agent"
        },
        "verb": verbo,
        "object": {
            "id": f"http://plurione.com/cursos/{curso.id}",
            "definition": {
                "name": {"es": curso.titulo},
                "description": {"es": getattr(curso, 'descripcion', 'Curso de capacitacion')}
            },
            "objectType": "Activity"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    if calificacion is not None and estatus == "Completado":
        statement["result"] = {
            "score": {
                "scaled": float(calificacion) / 100.0,
                "raw": float(calificacion)
            },
            "completion": True
        }

    return statement

@app.post("/api/progreso/actualizar")
def actualizar_progreso(payload: dict, db: Session = Depends(get_db)):
    usuario_id = payload.get("id_usuario")
    curso_id = payload.get("id_curso")
    accion = payload.get("accion")  
    calificacion = payload.get("calificacion", None)

    if not usuario_id or not curso_id:
        raise HTTPException(status_code=400, detail="id_usuario e id_curso son requeridos.")

    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()

    if not usuario or not curso:
        raise HTTPException(status_code=404, detail="Usuario o Curso no encontrado.")

    if accion == "completed":
        nuevo_estatus = "completado"
        verb_id = "http://adlnet.gov/expapi/verbs/completed"
        verb_display = {"en-US": "completed", "es-ES": "completó"}
    else:
        nuevo_estatus = payload.get("estatus", "En progreso")
        verb_id = "http://adlnet.gov/expapi/verbs/launched"
        verb_display = {"en-US": "inició"}

    progreso_model = getattr(models, "ProgresoCurso", getattr(models, "Progreso", None))
    progreso = db.query(progreso_model).filter(
        progreso_model.id_usuario == usuario_id,
        progreso_model.id_curso == curso_id
    ).first()

    if progreso:
        progreso.estatus = nuevo_estatus
        if hasattr(progreso, "calificacion") and calificacion is not None:
            progreso.calificacion = calificacion
    else:
        kwargs = {
            "id_usuario": usuario_id,
            "id_curso": curso_id,
            "estatus": nuevo_estatus
        }
        if hasattr(progreso_model, "calificacion"):
            kwargs["calificacion"] = calificacion

        progreso = progreso_model(**kwargs)
        db.add(progreso)

    db.commit()

    xapi_statement = {
        "actor": {
            "objectType": "Agent",
            "name": usuario.nombre,
            "mbox": f"mailto:{getattr(usuario, 'email', None) or f'usuario{usuario.id}@empresa.com'}"
        },
        "verb": {"id": verb_id, "display": verb_display},
        "object": {
            "objectType": "Activity",
            "id": curso.url_contenido or f"http://empresa.com/cursos/{curso.id}",
            "definition": {
                "name": {"es-ES": curso.titulo},
                "description": {"es-ES": f"Capacitación en {curso.titulo}"},
                "type": "http://adlnet.gov/expapi/activities/course"
            }
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    return {
        "status": "ok",
        "mensaje": "Progreso actualizado correctamente",
        "estatus_actual": nuevo_estatus,
        "xapi_statement": xapi_statement
    }

@app.get("/api/progreso/usuario/{usuario_id}")
def obtener_progreso_usuario(usuario_id: int, db: Session = Depends(get_db)):
    progreso_model = getattr(models, "ProgresoCurso", getattr(models, "Progreso", None))
    progresos = db.query(progreso_model).filter(progreso_model.id_usuario == usuario_id).all()
    
    return {
        "status": "ok",
        "usuario_id": usuario_id,
        "progresos": [
            {
                "id_progreso": getattr(p, "id_progreso", getattr(p, "id", None)),
                "id_curso": p.id_curso,
                "estatus": p.estatus,
                "calificacion": getattr(p, "calificacion", None)
            }
            for p in progresos
        ]
    }

from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/api/diagnostico/ultimo/{usuario_id}")
async def obtener_ultimo_diagnostico(usuario_id: int, db: Session = Depends(get_db)):
    try:
    
        query = text("""
            SELECT * FROM diagnosticos 
            WHERE usuario_id = :usuario_id AND score > 0
            ORDER BY fecha DESC 
            LIMIT 1
        """)
        
        resultado = db.execute(query, {"usuario_id": usuario_id}).fetchone()
        
        if not resultado:
            return {"mensaje": "No hay diagnostico previo", "score": 0}
            
        return dict(resultado._mapping)
    except Exception as e:
        print(f"Error en diagnostico/ultimo: {e}")
        return {"mensaje": "Error en servidor", "score": 0}
    
@app.get("/api/diagnostico/usuario/{usuario_id}")
def obtener_diagnosticos_usuario(usuario_id: int, db: Session = Depends(get_db)):
    registros = db.query(models.Diagnostico).filter(models.Diagnostico.usuario_id == usuario_id).all()
    return registros

@app.get("/api/cursos")
def obtener_todos_los_cursos(db: Session = Depends(get_db)):
    cursos = db.query(models.Curso).all()
    return [
        {
            "id": c.id,
            "titulo": c.titulo,
            "descripcion": c.descripcion,
            "categoria": getattr(c, 'categoria', 'Capacitación'),
            "duracion": getattr(c, 'duracion', 'Flexible'),
            "nivel": getattr(c, 'nivel', 'General'),
            "url_contenido": c.url_contenido
        }
        for c in cursos
    ]
    

@app.post("/api/evaluaciones/generar")
def api_generar_evaluacion(payload: dict, db: Session = Depends(get_db)):
    usuario_id = payload.get("usuario_id")
    
    if not usuario_id:
        raise HTTPException(status_code=400, detail="usuario_id es requerido.")

    ruta_guardada = db.query(models.RutaAprendizaje).filter(
        models.RutaAprendizaje.id_usuario == usuario_id
    ).first()

    cursos = []
    puesto = "Colaborador"

    if ruta_guardada:
        puesto = getattr(ruta_guardada, "puesto", None) or "Colaborador"
        
        cursos_raw = (
            getattr(ruta_guardada, "ruta", None) or 
            getattr(ruta_guardada, "recomendaciones", None) or 
            getattr(ruta_guardada, "ruta_recomendada", None) or 
            getattr(ruta_guardada, "contenido", None) or
            getattr(ruta_guardada, "cursos", None)
        )

        if cursos_raw:
            if isinstance(cursos_raw, str):
                try:
                    cursos = json.loads(cursos_raw)
                except Exception:
                    cursos = []
            else:
                cursos = cursos_raw

            if isinstance(cursos, dict):
                cursos = cursos.get("ruta") or cursos.get("cursos") or []

    if not cursos and payload.get("cursos"):
        cursos = payload.get("cursos")

    if not cursos:
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontraron cursos asignados para el usuario ID: {usuario_id}"
        )

    # 3. Generar el examen con Gemini
    examen_generado = generar_evaluacion_final(
        puesto_nombre=puesto,
        cursos_asignados=cursos
    )

    return {
        "status": "ok",
        "evaluacion": examen_generado
    }

@app.post("/api/evaluaciones/guardar-resultado")
async def guardar_resultado(datos: ResultadoExamenSchema, db: Session = Depends(get_db)):
    try:
        query = text("""
            INSERT INTO evaluaciones_resultados 
            (usuario_id, puntaje, aciertos, total_preguntas, aprobado, intentos_restantes)
            VALUES (:usuario_id, :puntaje, :aciertos, :total_preguntas, :aprobado, :intentos_restantes)
        """)
        
        db.execute(query, {
            "usuario_id": datos.usuario_id,
            "puntaje": datos.puntaje,
            "aciertos": datos.aciertos,
            "total_preguntas": datos.total_preguntas,
            "aprobado": datos.aprobado,
            "intentos_restantes": datos.intentos_restantes
        })
        db.commit()

        return {"status": "ok", "mensaje": "Resultado guardado correctamente para RH"}
    except Exception as e:
        db.rollback()
        print(f"Error al guardar resultado: {e}")
        raise HTTPException(status_code=500, detail="Error al guardar el resultado en la base de datos")


@app.get("/api/evaluaciones/ultimo/{usuario_id}")
async def obtener_ultimo_examen(usuario_id: int, db: Session = Depends(get_db)):
    try:
        query = text("""
            SELECT id, usuario_id, puntaje, aciertos, total_preguntas, aprobado, intentos_restantes
            FROM evaluaciones_resultados 
            WHERE usuario_id = :usuario_id 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        resultado = db.execute(query, {"usuario_id": usuario_id}).fetchone()

        if not resultado:
            return {
                "id": None,
                "usuario_id": usuario_id,
                "puntaje": 0,
                "aciertos": 0,
                "total_preguntas": 0,
                "aprobado": False,
                "intentos_restantes": 3
            }

        return {
            "id": resultado.id,
            "usuario_id": resultado.usuario_id,
            "puntaje": resultado.puntaje,
            "aciertos": resultado.aciertos,
            "total_preguntas": resultado.total_preguntas,
            "aprobado": resultado.aprobado,
            "intentos_restantes": resultado.intentos_restantes
        }
    except Exception as e:
        print(f"Error al obtener evaluación: {e}")
        return {
            "id": None,
            "usuario_id": usuario_id,
            "puntaje": 0,
            "aciertos": 0,
            "total_preguntas": 0,
            "aprobado": False,
            "intentos_restantes": 3
        }
        
@app.get("/api/xapi/statements")
def obtener_xapi_statements(usuario_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(XAPIStatement)
    if usuario_id is not None:
        query = query.filter(XAPIStatement.usuario_id == usuario_id)
        
    statements = query.order_by(XAPIStatement.timestamp.desc()).all()
    usuarios_map = {u.id: u.nombre for u in db.query(models.Usuario).all()}
    cursos_map = {c.id: c.titulo for c in db.query(models.Curso).all()}
    
    resultado = []
    for st in statements:
        nombre_usuario = usuarios_map.get(st.usuario_id, f"Usuario #{st.usuario_id}") if st.usuario_id else "Anónimo"
        verb_clean = (st.verb or "").lower()
        if "completed" in verb_clean or "completó" in verb_clean:
            accion_es = "Completado"
        elif "launched" in verb_clean or "inició" in verb_clean:
            accion_es = "Iniciado"
        else:
            accion_es = st.verb.capitalize() if st.verb else "Interactuó"

       
        obj_str = str(st.object_id or "")
        nombre_curso = obj_str
        if "curso-" in obj_str:
            try:
                c_id = int(obj_str.split("curso-")[-1])
                nombre_curso = cursos_map.get(c_id, obj_str)
            except ValueError:
                pass
        elif obj_str.isdigit():
            c_id = int(obj_str)
            nombre_curso = cursos_map.get(c_id, obj_str)

        resultado.append({
            "id": st.id,
            "usuario_id": st.usuario_id,
            "usuario_nombre": nombre_usuario,
            "verbo": accion_es,
            "objeto": nombre_curso,
            "detalles": st.statement_json,
            "marca_tiempo": st.timestamp.isoformat() if st.timestamp else None
        })
        
    return resultado

@app.post("/api/xapi/statements")
def registrar_xapi_statement(data: XAPIStatementCreate, db: Session = Depends(get_db)):
    try:
        nuevo_statement = XAPIStatement(
            usuario_id=data.usuario_id,
            verb=data.verb,
            object_id=data.object_id,
            statement_json=data.statement_json,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(nuevo_statement)
        db.commit()
        db.refresh(nuevo_statement)
        return {"status": "ok", "mensaje": "Statement xAPI registrado con éxito", "id": nuevo_statement.id}
    except Exception as e:
        db.rollback()
        print(f"Error guardando xAPI statement: {e}")
        return {"status": "ok", "mensaje": "Statement procesado"}
   
@app.post("/api/admin/preguntas")
def crear_pregunta_diagnostico(data: PreguntaCreate, db: Session = Depends(get_db)):
    try:
        nueva_p = models.PreguntaDiagnostico(
            puesto_id=data.puesto_id,
            pregunta=data.pregunta,
            opciones=data.opciones,
            opcion_correcta=data.opcion_correcta,
            categoria=data.categoria
        )
        db.add(nueva_p)
        db.commit()
        db.refresh(nueva_p)
        return {"status": "ok", "mensaje": "Pregunta guardada con éxito", "id": nueva_p.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar la pregunta: {str(e)}")

@app.get("/api/evaluaciones/diagnostico/{puesto_id}")
def obtener_preguntas_por_puesto(puesto_id: str, db: Session = Depends(get_db)):
    preguntas = db.query(models.Pregunta).filter(
        models.Pregunta.puesto == puesto_id
    ).all()
    
    return {
        "status": "ok",
        "puesto_id": puesto_id,
        "total": len(preguntas),
        "preguntas": [
            {
                "id": p.id,
                "pregunta": p.texto,       
                "opciones": p.opciones,    
                "categoria": p.categoria
            }
            for p in preguntas
        ]
    }
    
@app.post("/api/admin/preguntas/crear")
def crear_pregunta_rh(data: PreguntaCreateRequest, db: Session = Depends(get_db)):
    try:
        nueva_p = models.Pregunta(
            puesto=data.puesto,
            texto=data.texto,
            opciones=data.opciones,
            opcion_correcta=data.opcion_correcta,
            categoria=data.categoria
        )
        db.add(nueva_p)
        db.commit()
        db.refresh(nueva_p)

        return {
            "status": "ok",
            "mensaje": "Pregunta guardada correctamente",
            "id": nueva_p.id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al guardar la pregunta: {str(e)}"
        )
        
@app.post("/api/evaluaciones/diagnostico/evaluar")
def evaluar_diagnostico_dinamico(data: EvaluarDiagnosticoRequest, db: Session = Depends(get_db)):
    aciertos = 0
    total = len(data.respuestas)
    
    if total == 0:
        raise HTTPException(status_code=400, detail="No se enviaron respuestas para la evaluación.")

    for resp in data.respuestas:
        pregunta_db = db.query(models.Pregunta).filter(
            models.Pregunta.id == resp.pregunta_id
        ).first()
        
        if pregunta_db and pregunta_db.opcion_correcta == resp.opcion_seleccionada:
            aciertos += 1

    score_final = int((aciertos / total) * 100)

    nuevo_diag = models.Diagnostico(
        usuario_id=data.usuario_id,
        puesto_evaluado=data.puesto_id,
        score=score_final
    )
    db.add(nuevo_diag)
    db.commit()
    db.refresh(nuevo_diag)

    try:
        nuevo_st = models.XAPIStatement(
            usuario_id=data.usuario_id,
            verb="completed",
            object_id=f"evaluacion-diagnostica-{data.puesto_id}",
            statement_json={
                "evaluacion": "Diagnóstico Inicial de Puesto",
                "score": score_final,
                "aciertos": aciertos,
                "total": total
            },
            timestamp=datetime.now(timezone.utc)
        )
        db.add(nuevo_st)
        db.commit()
    except Exception as e:
        print(f"Error registrando statement xAPI: {e}")

    return {
        "status": "ok",
        "diagnostico_id": nuevo_diag.id,
        "score": score_final,
        "aciertos": aciertos,
        "total_preguntas": total
    }

import unicodedata
def limpiar_texto(texto: str) -> str:
    """Remueve acentos, convierte a minúsculas y elimina espacios extra."""
    if not texto:
        return "sin asignar"
    texto_norm = unicodedata.normalize('NFD', texto)
    texto_sin_acentos = ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
    return texto_sin_acentos.strip().lower()


@app.get("/api/admin/metrics", tags=["Admin"])
def obtener_metricas_admin(db: Session = Depends(get_db)):
    try:
        # 1. Total de empleados 
        total_empleados = db.query(models.Usuario).filter(models.Usuario.rol == 'empleado').count()

        # 2. Promedio general de Puntaje Diagnóstico 
        promedio_diag = db.query(func.avg(models.Diagnostico.score)).scalar() or 0.0

        # 3. Total de Cursos Completados
        total_cursos_completados = db.query(models.ProgresoCurso).filter(
            func.lower(models.ProgresoCurso.estatus).in_(['completado', 'completed'])
        ).count()

        # 4. Tasa de Aprobación vía xAPI
        total_evaluaciones = db.query(models.XAPIStatement).count()
        aprobados_eval = db.query(models.XAPIStatement).filter(
            models.XAPIStatement.verb.in_(['passed', 'completed'])
        ).count()
        
        tasa_aprobacion = round((aprobados_eval / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0.0

      ## 5. Promedio de Diagnóstico agrupado por Departamento 
        diag_por_depto_raw = db.query(
            models.Usuario.departamento,
            models.Diagnostico.score
        ).join(models.Diagnostico, models.Usuario.id == models.Diagnostico.usuario_id).all()

        # Agrupamos en Python para unificar sin importar acentos/mayúsculas
        agrupado = {}
        for dep, score in diag_por_depto_raw:
            dep_limpio = limpiar_texto(dep)
            if dep_limpio not in agrupado:
                agrupado[dep_limpio] = []
            if score is not None:
                agrupado[dep_limpio].append(score)

        # Formateamos con nombres limpios y bonitos para React
        grafico_departamentos = [
            {
                "departamento": dep_key.capitalize(),  
                "promedio": round(sum(scores) / len(scores), 1) if scores else 0.0
            }
            for dep_key, scores in agrupado.items()
        ]

        # 6. Estatus Global de Cursos
        total_asignaciones = db.query(models.ProgresoCurso).count()
        pendientes = max(0, total_asignaciones - total_cursos_completados)

        grafico_estatus_cursos = [
            {"name": "Completados", "value": total_cursos_completados},
            {"name": "Pendientes / En Curso", "value": pendientes}
        ]
        
        # 7. Distribución por Puesto
        puestos_raw = db.query(
            models.Usuario.puesto,
            func.count(models.Usuario.id)
        ).group_by(models.Usuario.puesto).all()

        grafico_puestos = [
            {"puesto": p if p else "Sin Especificar", "cantidad": cant}
            for p, cant in puestos_raw
        ]

        # 8. Evolución del Aprendizaje en el Tiempo (xAPI por mes)
        evolucion_raw = db.query(
            func.to_char(models.XAPIStatement.timestamp, 'YYYY-MM').label("mes"),
            func.count(models.XAPIStatement.id).label("total")
        ).group_by("mes").order_by("mes").all()

        grafico_evolucion = [
            {"mes": mes if mes else "Sin Fecha", "actividades": total}
            for mes, total in evolucion_raw
        ]

        return {
            "kpis": {
                "total_empleados": total_empleados,
                "promedio_diagnostico": round(promedio_diag, 1),
                "cursos_completados": total_cursos_completados,
                "tasa_aprobacion": tasa_aprobacion
            },
            "graficos": {
                "por_departamento": grafico_departamentos,
                "estatus_cursos": grafico_estatus_cursos,
                "por_puesto": grafico_puestos,
                "evolucion_aprendizaje": grafico_evolucion
            }
        }
        

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando métricas: {str(e)}")

app.include_router(router)




# 1. Obtener la lista completa de departamentos con sus puestos
@app.get("/api/admin/estructura", tags=["Estructura Organizacional"])
def obtener_estructura_organizacional(db: Session = Depends(get_db)):
    deptos = db.query(models.Departamento).all()
    resultado = []
    for d in deptos:
        resultado.append({
            "id": d.id,
            "nombre": d.nombre,
            "descripcion": d.descripcion,
            "puestos": [
                {"id": p.id, "nombre": p.nombre} for p in d.puestos
            ]
        })
    return resultado


# 2. Crear un nuevo departamento 
@app.post("/api/admin/departamentos", tags=["Estructura Organizacional"])
def crear_departamento(datos: DepartamentoCreate, db: Session = Depends(get_db)):
    nombre_limpio = datos.nombre.strip()
    
    depto_existente = db.query(models.Departamento).filter(
        func.lower(models.Departamento.nombre) == nombre_limpio.lower()
    ).first()
    
    if depto_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"El departamento '{nombre_limpio}' ya existe."
        )
        
    nuevo_depto = models.Departamento(
        nombre=nombre_limpio,
        descripcion=datos.descripcion.strip() if datos.descripcion else None
    )
    db.add(nuevo_depto)
    db.commit()
    db.refresh(nuevo_depto)
    
    if datos.puestos:
        for p_nombre in datos.puestos:
            if p_nombre.strip():
                puesto_obj = models.Puesto(
                    nombre=p_nombre.strip(),
                    departamento_id=nuevo_depto.id
                )
                db.add(puesto_obj)
        db.commit()
        
    return {
        "mensaje": "Departamento creado exitosamente", 
        "id": nuevo_depto.id, 
        "nombre": nuevo_depto.nombre
    }


@app.post("/api/admin/departamentos/{depto_id}/puestos", tags=["Estructura Organizacional"])
def agregar_puesto_a_departamento(depto_id: int, datos: PuestoCreate, db: Session = Depends(get_db)):
    depto = db.query(models.Departamento).filter(models.Departamento.id == depto_id).first()
    if not depto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="El departamento especificado no existe."
        )
        
    puesto_nombre = datos.nombre.strip()
    
    puesto_existente = db.query(models.Puesto).filter(
        models.Puesto.departamento_id == depto_id,
        func.lower(models.Puesto.nombre) == puesto_nombre.lower()
    ).first()
    
    if puesto_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"El puesto '{puesto_nombre}' ya existe en el departamento '{depto.nombre}'."
        )
        
    nuevo_puesto = models.Puesto(
        nombre=puesto_nombre,
        departamento_id=depto.id
    )
    db.add(nuevo_puesto)
    db.commit()
    db.refresh(nuevo_puesto)
    
    return {
        "mensaje": f"Puesto '{nuevo_puesto.nombre}' agregado exitosamente a '{depto.nombre}'",
        "id": nuevo_puesto.id
    }

@app.put("/api/cursos/{curso_id}")
def actualizar_curso(curso_id: int, curso: CursoCreate, db: Session = Depends(get_db)):
    db_curso = db.query(Curso).filter(Curso.id == curso_id).first()
    
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    datos_actualizados = curso.model_dump() 
    for clave, valor in datos_actualizados.items():
        setattr(db_curso, clave, valor)
        
    db.commit()
    db.refresh(db_curso)
    return db_curso

# 1. LISTAR TODAS LAS PREGUNTAS (O FILTRADAS POR PUESTO)
@app.get("/api/admin/preguntas")
def obtener_preguntas_rh(puesto: str = None, db: Session = Depends(get_db)):
    try:
        query = db.query(models.Pregunta)
        if puesto:
            query = query.filter(models.Pregunta.puesto == puesto)
        preguntas = query.all()
        return preguntas
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener las preguntas: {str(e)}"
        )

# 2. EDITAR / ACTUALIZAR PREGUNTA
@app.put("/api/admin/preguntas/actualizar/{pregunta_id}")
def actualizar_pregunta_rh(pregunta_id: int, data: PreguntaCreateRequest, db: Session = Depends(get_db)):
    try:
        pregunta = db.query(models.Pregunta).filter(models.Pregunta.id == pregunta_id).first()
        if not pregunta:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")
        
        pregunta.puesto = data.puesto
        pregunta.texto = data.texto
        pregunta.opciones = data.opciones
        pregunta.opcion_correcta = data.opcion_correcta
        pregunta.categoria = data.categoria

        db.commit()
        db.refresh(pregunta)

        return {
            "status": "ok",
            "mensaje": "Pregunta actualizada correctamente",
            "id": pregunta.id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar la pregunta: {str(e)}"
        )

# 3. ELIMINAR PREGUNTA
@app.delete("/api/admin/preguntas/eliminar/{pregunta_id}")
def eliminar_pregunta_rh(pregunta_id: int, db: Session = Depends(get_db)):
    try:
        pregunta = db.query(models.Pregunta).filter(models.Pregunta.id == pregunta_id).first()
        if not pregunta:
            raise HTTPException(status_code=404, detail="Pregunta no encontrada")

        db.delete(pregunta)
        db.commit()

        return {
            "status": "ok",
            "mensaje": "Pregunta eliminada correctamente"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar la pregunta: {str(e)}"
        )