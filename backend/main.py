import json
import os
from datetime import date, datetime, timezone
from typing import List, Optional
from security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    get_current_user, 
    require_admin,
    exigir_mismo_usuario
)
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session
import unicodedata
import models
from database import Base, engine, get_db
from models import (
    Curso,
    Departamento,
    Diagnostico,
    EvaluacionResultado,
    Pregunta,
    ProgresoCurso,
    Puesto,
    RutaAprendizaje,
    Usuario,
    XAPIStatement,
)
from services.ai_adapter import generar_evaluacion_final, generar_ruta_aprendizaje
import urllib.parse

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
    
class CompletarCursoSchema(BaseModel):
    usuario_id: int
    curso_id: int

@app.get("/")
def home():
    return {"status": "API Activa", "sistema": "PluriOne Capacitaciones"}

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def registrar_usuario(data: UserRegister, db: Session = Depends(get_db)):
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == data.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")
    
    # Convertir la contraseña en texto plano a un hash seguro con bcrypt
    hashed_pwd = hash_password(data.password)

    nuevo_usuario = models.Usuario(
        nombre=data.nombre,
        email=data.email,
        password=hashed_pwd,
        rol="empleado",
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

    # Validar si el usuario existe y si el hash de la contraseña coincide
    if not usuario or not verify_password(data.password, usuario.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos."
        )

    # Generar Token JWT
    token_data = {"sub": str(usuario.id), "email": usuario.email, "rol": usuario.rol}
    access_token = create_access_token(data=token_data)

    return {
        "status": "ok",
        "access_token": access_token,
        "token_type": "bearer",
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
            rol_usuario = getattr(u, 'rol', 'empleado')

            resultado.append({
                "id": u.id,
                "nombre": u.nombre,
                "email": u.email,
                "rol": rol_usuario,
                "departamento": getattr(u, 'departamento', ''),
                "puesto": val_puesto,
                "puesto_nombre": nombre_puesto
                # ⚠️ Se eliminó "access_token" para evitar la fuga de seguridad
            })
            
        return resultado

    except Exception as e:
        print("Error en /api/usuarios/simulador:", e)
        usuarios_fallback = db.query(models.Usuario).all()
        return [
            {
                "id": u.id,
                "nombre": u.nombre,
                "email": u.email,
                "rol": getattr(u, 'rol', 'empleado'),
                "puesto": getattr(u, 'puesto', ''),
                "puesto_nombre": getattr(u, 'puesto', '')
                # ⚠️ Se eliminó "access_token" del fallback
            }
            for u in usuarios_fallback
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

@app.get("/api/usuarios/perfil/{usuario_id}")
def obtener_perfil_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    exigir_mismo_usuario(current_user, usuario_id)
    try:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # 1. Mapas para traducir IDs de puestos y departamentos
        puestos_db = db.query(models.Puesto).all()
        puestos_map = {str(p.id): p for p in puestos_db}
        deptos_db = db.query(models.Departamento).all()
        deptos_map = {str(d.id): d.nombre for d in deptos_db}

        # 2. Obtener puesto
        val_puesto = getattr(usuario, 'puesto', None) or getattr(usuario, 'puesto_id', None)
        val_puesto_str = str(val_puesto) if val_puesto is not None else ""
        
        puesto_obj = puestos_map.get(val_puesto_str)
        nombre_puesto = puesto_obj.nombre if puesto_obj else (val_puesto_str or "Sin Asignar")
      
        # 3. Obtener departamento
        val_depto = getattr(usuario, 'departamento', None) or getattr(usuario, 'departamento_id', None)
        if not val_depto and puesto_obj and hasattr(puesto_obj, 'departamento_id'):
            val_depto = puesto_obj.departamento_id
            
        val_depto_str = str(val_depto) if val_depto is not None else ""
        nombre_depto = deptos_map.get(val_depto_str, val_depto_str or "General")

        return {
            "id": usuario.id,
            "nombre": getattr(usuario, 'nombre', getattr(usuario, 'nombre_completo', f"Usuario #{usuario.id}")),
            "email": getattr(usuario, 'email', getattr(usuario, 'correo', '')),
            "rol": getattr(usuario, 'rol', 'empleado'),
            "puesto_id": val_puesto,
            "puesto_nombre": nombre_puesto,
            "departamento_id": val_depto,
            "departamento_nombre": nombre_depto
        }

    except Exception as e:
        print("Error en /api/usuarios/perfil:", e)
        raise HTTPException(status_code=500, detail=f"Error al obtener el perfil de usuario: {str(e)}")
    
@app.post("/api/rutas/generar-ia", tags=["Rutas"])
def generar_ruta_ia(datos: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    usuario_id = datos.get("usuario_id") or datos.get("id_usuario")
    if usuario_id:
        exigir_mismo_usuario(current_user, usuario_id)
        
    try:
        puesto_param = datos.get("puesto_id") or datos.get("puesto") or ""
        usuario_id = datos.get("usuario_id") or datos.get("id_usuario")
        respuestas_usuario = datos.get("respuestas", {})

        if not puesto_param:
            raise HTTPException(status_code=400, detail="El 'puesto_id' es requerido.")

        # 1. Búsqueda flexible del puesto
        puesto_db = None
        if str(puesto_param).isdigit():
            puesto_db = db.query(models.Puesto).filter(models.Puesto.id == int(puesto_param)).first()
        
        if not puesto_db:
            puesto_db = db.query(models.Puesto).filter(
                func.lower(models.Puesto.nombre) == str(puesto_param).lower()
            ).first()

        puesto_nombre = puesto_db.nombre if puesto_db else str(puesto_param)

        # 2. Cursos disponibles para este puesto
        cursos_disponibles = db.query(models.Curso).filter(
            (func.lower(models.Curso.puesto_id) == puesto_nombre.lower()) |
            (func.lower(models.Curso.puesto_id) == "general")
        ).all()

        if not cursos_disponibles:
            cursos_disponibles = db.query(models.Curso).all()

        catalogo_cursos = [
            {
                "id": c.id,
                "id_curso": c.id,
                "titulo": c.titulo,
                "nombre": c.titulo,
                "descripcion": getattr(c, 'descripcion', '') or "Sin descripción disponible.",
                "justificacion": getattr(c, 'descripcion', '') or "Curso asignado según plan de estudios.",
                "duracion": getattr(c, 'duracion', '') or "Flexible",
                "nivel": getattr(c, 'nivel', '') or "General",
                "categoria": getattr(c, 'categoria', '') or "Capacitación",
                "puesto_id": getattr(c, 'puesto_id', '') or "",
                "url_contenido": getattr(c, 'url_contenido', '') or "#",
                "tipo_contenido": getattr(c, 'tipo_contenido', '') or "Recurso"
            }
            for c in cursos_disponibles
        ]

        preguntas_puesto = db.query(models.Pregunta).filter(
            func.lower(models.Pregunta.puesto) == puesto_nombre.lower()
        ).all()

        categorias_falladas = []
        if isinstance(respuestas_usuario, dict):
            for p in preguntas_puesto:
                resp_val = respuestas_usuario.get(str(p.id)) if str(p.id) in respuestas_usuario else respuestas_usuario.get(p.id)
                if resp_val is not None and int(resp_val) != p.opcion_correcta:
                    categorias_falladas.append(p.categoria.lower() if p.categoria else "")

        cursos_adaptativos = [
            c for c in catalogo_cursos 
            if c["categoria"].lower() in categorias_falladas or any(cat in c["titulo"].lower() for cat in categorias_falladas)
        ]

        if not cursos_adaptativos:
            cursos_adaptativos = catalogo_cursos[:1]

# 3. Procesamiento con IA
        try:
            resultado_ia = generar_ruta_aprendizaje(
                puesto_nombre=puesto_nombre,
                respuestas_diagnostico=respuestas_usuario,
                cursos_disponibles=catalogo_cursos
            )
        except Exception as e_ia:
            print(f"⚠️ [IA Fallback activado]: {e_ia}")
            resultado_ia = {"ruta": cursos_adaptativos}

        # Extraer la lista devuelta por la IA
        lista_ia = resultado_ia.get("ruta") if isinstance(resultado_ia, dict) else resultado_ia
        if not isinstance(lista_ia, list) or len(lista_ia) == 0:
            lista_ia = cursos_adaptativos
            

        #FILTRO ADAPTATIVO PROPORCIONAL Y ESCALABLE
        
        
        ultimo_diag = db.query(models.Diagnostico).filter(
            models.Diagnostico.usuario_id == int(usuario_id) if usuario_id else True
        ).order_by(models.Diagnostico.id.desc()).first()

        score_usuario = ultimo_diag.score if ultimo_diag else 100
        total_cursos_disponibles = len(catalogo_cursos)

        
        if score_usuario >= 80:
            
            cantidad_cursos = max(1, int(total_cursos_disponibles * 0.20))
        elif score_usuario >= 50:
            
            cantidad_cursos = max(1, int(total_cursos_disponibles * 0.50))
        else:
            
            cantidad_cursos = total_cursos_disponibles

       
        lista_ia = catalogo_cursos[:cantidad_cursos]

        
        mapa_cursos_db = {c["id"]: c for c in catalogo_cursos}
        mapa_titulos_db = {c["titulo"].strip().lower(): c for c in catalogo_cursos}

        ruta_final_enriquecida = []
        for curso_ia in lista_ia:
            c_id = curso_ia.get("id") or curso_ia.get("id_curso")
            c_titulo = (curso_ia.get("titulo") or curso_ia.get("nombre") or "").strip().lower()
            
            curso_db = mapa_cursos_db.get(c_id) or mapa_titulos_db.get(c_titulo) or {}

            curso_corregido = {
                **curso_ia,
                "id": curso_db.get("id", c_id),
                "id_curso": curso_db.get("id", c_id),
                "titulo": curso_db.get("titulo") or curso_ia.get("titulo"),
                "nombre": curso_db.get("titulo") or curso_ia.get("nombre"),
                "descripcion": curso_db.get("descripcion") or curso_ia.get("descripcion"),
                "duracion": curso_db.get("duracion") or curso_ia.get("duracion"),
                "nivel": curso_db.get("nivel") or curso_ia.get("nivel"),
                "categoria": curso_db.get("categoria") or curso_ia.get("categoria"),
                "url_contenido": curso_db.get("url_contenido") or curso_ia.get("url_contenido"),
                "justificacion": curso_ia.get("justificacion") or curso_db.get("descripcion")
            }
            ruta_final_enriquecida.append(curso_corregido)

        # 4. Guardar en BD la estructura enriquecida
        if usuario_id:
            try:
                ruta_db = db.query(models.RutaAprendizaje).filter(
                    models.RutaAprendizaje.id_usuario == int(usuario_id)
                ).first()

                if not ruta_db:
                    nueva_ruta = models.RutaAprendizaje(
                        id_usuario=int(usuario_id),
                        orden_secuencia_json={"ruta": ruta_final_enriquecida},
                        fecha_asignacion=date.today()
                    )
                    db.add(nueva_ruta)
                else:
                    ruta_db.orden_secuencia_json = {"ruta": ruta_final_enriquecida}

                db.commit()
                print("✅ Ruta adaptativa guardada correctamente en la BD.")
            except Exception as e_db:
                db.rollback()
                print(f"Error al guardar en BD: {e_db}")

        return {
            "status": "ok",
            "mensaje": f"Ruta asignada exitosamente para {puesto_nombre}",
            "ruta": ruta_final_enriquecida,
            "cursos": ruta_final_enriquecida
        }

    except Exception as e:
        print(f"Error general en generar_ruta_ia: {e}")
        db.rollback()
        return {"status": "error", "mensaje": str(e)}

@app.post("/api/diagnostico/guardar")
def guardar_diagnostico(data: GuardarDiagnosticoRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    exigir_mismo_usuario(current_user, data.usuario_id)
        
    usuario = db.query(models.Usuario).filter(models.Usuario.id == data.usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="El usuario especificado no existe.")

    # 1. Guardar o actualizar en la tabla diagnosticos
    diag_existente = db.query(models.Diagnostico).filter(models.Diagnostico.usuario_id == data.usuario_id).first()
    
    if diag_existente:
        diag_existente.score = data.score
        diag_existente.puesto_evaluado = str(data.puesto_id)
        nuevo_diagnostico = diag_existente
    else:
        nuevo_diagnostico = models.Diagnostico(
            usuario_id=data.usuario_id,
            puesto_evaluado=str(data.puesto_id),
            score=data.score
        )
        db.add(nuevo_diagnostico)

    # 2. Registrar evento xAPI SIN enviar 'score' ni 'activity' como argumentos directos
    try:
        statement_xapi = models.XAPIStatement(
        usuario_id=data.usuario_id,
        verb="completed",
        object_id="diagnostico-inicial",
        statement_json={
            "actor": usuario.email,
            "verb": "completed",
            "object": "diagnostico-inicial",
            "score": float(data.score)
        }
    )
        db.add(statement_xapi)
    except Exception as e:
        print(f"Aviso xAPI: {e}")

    db.commit()
    db.refresh(nuevo_diagnostico)

    return {"status": "ok", "diagnostico": {"score": nuevo_diagnostico.score}}

@app.post("/api/cursos", status_code=status.HTTP_201_CREATED)
def crear_curso(curso: CursoCreate, db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
    nuevo_curso = models.Curso(**curso.model_dump())
    db.add(nuevo_curso)
    db.commit()
    db.refresh(nuevo_curso)
    return {"status": "ok", "mensaje": "Curso creado exitosamente", "curso": nuevo_curso}


@app.get("/api/cursos")
def obtener_todos_los_cursos(puesto_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Curso)
    if puesto_id:
        query = query.filter(models.Curso.puesto_id == puesto_id)
    cursos = query.all()
    
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
def eliminar_curso(curso_id: int, db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
    curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="El curso no existe.")
    
    db.delete(curso)
    db.commit()
    return {"status": "ok", "mensaje": "Curso eliminado correctamente"}

@app.get("/api/rutas/usuario/{usuario_id}", tags=["Rutas"])
def obtener_ruta_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    exigir_mismo_usuario(current_user, usuario_id)
    
    # 1. Obtener la última ruta guardada
    ruta = db.query(models.RutaAprendizaje)\
             .filter(models.RutaAprendizaje.id_usuario == usuario_id)\
             .order_by(models.RutaAprendizaje.id_ruta.desc())\
             .first()

    if not ruta:
        return {
            "status": "ok",
            "id_ruta": None,
            "fecha_asignacion": None,
            "puntaje": 0,
            "ruta": []
        }

    
    todos_los_cursos = db.query(models.Curso).all()
    mapa_cursos_db = {c.id: c for c in todos_los_cursos}
    mapa_titulos_db = {c.titulo.strip().lower(): c for c in todos_los_cursos if c.titulo}

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
            c_id = curso.get("id") or curso.get("id_curso")
            titulo = (curso.get("nombre") or curso.get("titulo") or "").strip()
            
            curso_db = mapa_cursos_db.get(c_id) or mapa_titulos_db.get(titulo.lower())

            curso_enriquecido = {
                **curso,
                "id": curso_db.id if curso_db else c_id,
                "id_curso": curso_db.id if curso_db else c_id,
                "titulo": curso_db.titulo if curso_db else titulo,
                "nombre": curso_db.titulo if curso_db else titulo,
                "descripcion": curso_db.descripcion if curso_db else curso.get("descripcion"), # <-- DESCRIPCIÓN DEL SEED.PY
                "duracion": curso_db.duracion if curso_db else curso.get("duracion"),
                "nivel": curso_db.nivel if curso_db else curso.get("nivel"),
                "categoria": curso_db.categoria if curso_db else curso.get("categoria"),
                "url_contenido": curso_db.url_contenido if curso_db else curso.get("url_contenido"),
                "justificacion": curso.get("justificacion") or (curso_db.descripcion if curso_db else "")
            }
            cursos_enriquecidos.append(curso_enriquecido)

    return {
        "status": "ok",
        "id_ruta": ruta.id_ruta,
        "fecha_asignacion": ruta.fecha_asignacion,
        "puntaje": 0,
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
def actualizar_progreso(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # 1. Obtener y asegurar conversión a entero de los IDs
    raw_usuario_id = payload.get("id_usuario") or payload.get("usuario_id")
    raw_curso_id = payload.get("id_curso") or payload.get("curso_id")

    if not raw_usuario_id or not raw_curso_id:
        raise HTTPException(status_code=400, detail="id_usuario e id_curso son requeridos.")

    try:
        usuario_id = int(raw_usuario_id)
        curso_id = int(raw_curso_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Los IDs deben ser números enteros válidos.")

    # 2. Validar que sea el mismo usuario
    exigir_mismo_usuario(current_user, usuario_id)
    
    accion = payload.get("accion")  
    calificacion = payload.get("calificacion", None)

    # 3. Buscar Usuario y Curso
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {usuario_id} no encontrado.")
    if not curso:
        raise HTTPException(status_code=404, detail=f"Curso con ID {curso_id} no encontrado.")

    # 4. Determinar estatus
    if accion == "completed":
        nuevo_estatus = "completado"
        verb_id = "http://adlnet.gov/expapi/verbs/completed"
        verb_display = {"en-US": "completed", "es-ES": "completó"}
    else:
        nuevo_estatus = payload.get("estatus", "En progreso")
        verb_id = "http://adlnet.gov/expapi/verbs/launched"
        verb_display = {"en-US": "inició"}

    # 5. Obtener dinámicamente el modelo de Progreso
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

    # 6. Generar Statement xAPI
    xapi_statement = {
        "actor": {
            "objectType": "Agent",
            "name": usuario.nombre,
            "mbox": f"mailto:{getattr(usuario, 'email', None) or f'usuario{usuario.id}@empresa.com'}"
        },
        "verb": {"id": verb_id, "display": verb_display},
        "object": {
            "objectType": "Activity",
            "id": getattr(curso, "url_contenido", None) or f"http://empresa.com/cursos/{curso.id}",
            "definition": {
                "name": {"es-ES": getattr(curso, "titulo", getattr(curso, "nombre", "Curso"))},
                "description": {"es-ES": f"Capacitación"},
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

@app.get("/api/diagnostico/ultimo/{usuario_id}")
async def obtener_ultimo_diagnostico(usuario_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    exigir_mismo_usuario(current_user, usuario_id)
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
def obtener_diagnosticos_usuario(usuario_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    exigir_mismo_usuario(current_user, usuario_id)
    registros = db.query(models.Diagnostico).filter(models.Diagnostico.usuario_id == usuario_id).all()
    return registros


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
async def guardar_resultado(datos: ResultadoExamenSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    exigir_mismo_usuario(current_user, datos.usuario_id)
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
async def obtener_ultimo_examen(usuario_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    exigir_mismo_usuario(current_user, usuario_id)
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
def obtener_xapi_statements(usuario_id: Optional[int] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
   # Si no pasa usuario_id y no es admin, forzamos su propio ID
    if current_user.get("rol") != "admin":
        usuario_id = int(current_user["id"])
    elif usuario_id is not None:
        exigir_mismo_usuario(current_user, usuario_id)
   
    query = db.query(XAPIStatement)
    if usuario_id is not None:
        query = query.filter(XAPIStatement.usuario_id == usuario_id)
        
    statements = query.order_by(XAPIStatement.timestamp.desc()).all()
    usuarios_db = db.query(models.Usuario).all()
    usuarios_map = {u.id: u for u in usuarios_db}
    puestos_db = db.query(models.Puesto).all()
    puestos_map = {str(p.id): p.nombre for p in puestos_db}
    cursos_map = {c.id: c.titulo for c in db.query(models.Curso).all()}
    
    resultado = []
    for st in statements:
        usuario_obj = usuarios_map.get(st.usuario_id)
        nombre_usuario = usuario_obj.nombre if usuario_obj else (f"Usuario #{st.usuario_id}" if st.usuario_id else "Anónimo")
        puesto_id_val = getattr(usuario_obj, 'puesto', None) or getattr(usuario_obj, 'puesto_id', None) if usuario_obj else None
        puesto_str = str(puesto_id_val) if puesto_id_val is not None else ""
        nombre_puesto = puestos_map.get(puesto_str, puesto_str or "Sin Asignar")
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
            "usuario_puesto": nombre_puesto,  # <-- Puesto traducido directamente desde la BD
            "verbo": accion_es,
            "objeto": nombre_curso,
            "detalles": st.statement_json,
            "marca_tiempo": st.timestamp.isoformat() if st.timestamp else None
        })
        
    return resultado

@app.post("/api/xapi/statements")
def registrar_xapi_statement(data: XAPIStatementCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if data.usuario_id:
        exigir_mismo_usuario(current_user, data.usuario_id)
    
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al registrar el evento xAPI: {str(e)}"
        )
   

@app.get("/api/evaluaciones/diagnostico/{puesto_id:path}", tags=["Evaluaciones"])
def obtener_preguntas_por_puesto(puesto_id: str, db: Session = Depends(get_db)):
    try:
        puesto_limpio = urllib.parse.unquote(puesto_id).strip()

        # 1. Búsqueda exacta
        preguntas = db.query(models.Pregunta).filter(
            func.lower(models.Pregunta.puesto) == puesto_limpio.lower()
        ).all()

        # 2. Búsqueda 
        if not preguntas:
            palabras = [p for p in puesto_limpio.lower().split() if len(p) > 3]
            for palabra in palabras:
                preguntas = db.query(models.Pregunta).filter(
                    func.lower(models.Pregunta.puesto).like(f"%{palabra}%")
                ).all()
                if preguntas:
                    break

        if not preguntas:
            preguntas = db.query(models.Pregunta).limit(5).all()

        return [
            {
                "id": p.id,
                "pregunta": p.texto,
                "texto": p.texto,
                "opciones": p.opciones,
                "opcion_correcta": p.opcion_correcta,
                "categoria": p.categoria,
                "puesto": p.puesto
            }
            for p in preguntas
        ]
    except Exception as e:
        print(f"Error al obtener preguntas: {e}")
        return []
    
@app.post("/api/admin/preguntas/crear")
def crear_pregunta_rh(data: PreguntaCreateRequest, db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
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
def evaluar_diagnostico_dinamico(data: EvaluarDiagnosticoRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if data.usuario_id:
        exigir_mismo_usuario(current_user, data.usuario_id)
        
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

def limpiar_texto(texto: str) -> str:
    """Remueve acentos, convierte a minúsculas y elimina espacios extra."""
    if not texto:
        return "sin asignar"
    texto_norm = unicodedata.normalize('NFD', texto)
    texto_sin_acentos = ''.join(c for c in texto_norm if unicodedata.category(c) != 'Mn')
    return texto_sin_acentos.strip().lower()


@app.get("/api/admin/metrics", tags=["Admin"])
def obtener_metricas_admin(db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
    try:
        total_empleados = db.query(models.Usuario).filter(models.Usuario.rol == 'empleado').count() 
        promedio_diag = db.query(func.avg(models.Diagnostico.score)).scalar() or 0.0
        total_cursos_completados = db.query(models.ProgresoCurso).filter(
            func.lower(models.ProgresoCurso.estatus).in_(['completado', 'completed'])
        ).count()

        total_evaluaciones = db.query(models.XAPIStatement).count()
        aprobados_eval = db.query(models.XAPIStatement).filter(
            models.XAPIStatement.verb.in_(['passed', 'completed'])
        ).count()
        
        tasa_aprobacion = round((aprobados_eval / total_evaluaciones * 100), 1) if total_evaluaciones > 0 else 0.0
        diag_por_depto_raw = db.query(
            models.Usuario.departamento,
            models.Diagnostico.score
        ).outerjoin(models.Diagnostico, models.Usuario.id == models.Diagnostico.usuario_id).all()

        agrupado = {}
        for dep, score in diag_por_depto_raw:
            if not dep:
                continue
                
            dep_limpio = limpiar_texto(str(dep))
            if dep_limpio not in agrupado:
                agrupado[dep_limpio] = {"nombre_original": str(dep).strip(), "scores": []}
            
            if score is not None:
                try:
                    score_num = float(score)
                    if score_num > 0:
                        agrupado[dep_limpio]["scores"].append(score_num)
                except ValueError:
                    pass

        grafico_departamentos = [
            {
                "departamento": data["nombre_original"],
                "departamentoNombre": data["nombre_original"], # 👈 Coincide con tu <XAxis dataKey="departamentoNombre" />
                "promedio": round(sum(data["scores"]) / len(data["scores"]), 1) if len(data["scores"]) > 0 else 0.0
            }
            for dep_key, data in agrupado.items()
        ]

        total_asignaciones = db.query(models.ProgresoCurso).count()
        pendientes = max(0, total_asignaciones - total_cursos_completados)

        grafico_estatus_cursos = [
            {"name": "Completados", "value": total_cursos_completados},
            {"name": "Pendientes / En Curso", "value": pendientes}
        ]
        
        puestos_raw = db.query(
            models.Usuario.puesto,
            func.count(models.Usuario.id)
        ).group_by(models.Usuario.puesto).all()

        grafico_puestos = [
            {"puesto": p if p else "Sin Especificar", "cantidad": cant}
            for p, cant in puestos_raw
        ]

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
def obtener_estructura_organizacional(db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
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
def crear_departamento(
    datos: DepartamentoCreate, 
    db: Session = Depends(get_db), 
    admin_user: dict = Depends(require_admin)
):
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
    
    return {
        "mensaje": "Departamento creado exitosamente", 
        "id": nuevo_depto.id, 
        "nombre": nuevo_depto.nombre
    }


@app.post("/api/admin/departamentos/{depto_id}/puestos", tags=["Estructura Organizacional"])
def agregar_puesto_a_departamento(
    depto_id: int, 
    datos: PuestoCreate, 
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
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
def actualizar_curso(curso_id: int, curso: CursoCreate, db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
    db_curso = db.query(models.Curso).filter(models.Curso.id == curso_id).first()
    
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
def obtener_preguntas_rh(puesto: str = None, db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
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
def actualizar_pregunta_rh(pregunta_id: int, data: PreguntaCreateRequest, db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
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
def eliminar_pregunta_rh(pregunta_id: int, db: Session = Depends(get_db), admin_user: dict = Depends(require_admin)):
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
        

@app.post("/api/cursos/completar")
def completar_curso(
    data: CompletarCursoSchema, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    exigir_mismo_usuario(current_user, data.usuario_id)

    # 1. Registrar o actualizar progreso del curso
    progreso = db.query(models.ProgresoCurso).filter(
        models.ProgresoCurso.id_usuario == data.usuario_id,
        models.ProgresoCurso.id_curso == data.curso_id
    ).first()

    if not progreso:
        progreso = models.ProgresoCurso(
            id_usuario=data.usuario_id,
            id_curso=data.curso_id,
            estatus="completado"
        )
        db.add(progreso)
    else:
        progreso.estatus = "completado"

    # 2. Construir la estructura estándar del Statement de xAPI
    payload_xapi = {
        "actor": {
            "account": {
                "homePage": "http://plurione.com",
                "name": str(data.usuario_id)
            },
            "objectType": "Agent"
        },
        "verb": {
            "id": "http://adlnet.gov/expapi/verbs/completed",
            "display": {"en-US": "completed"}
        },
        "object": {
            "id": f"http://plurione.com/courses/{data.curso_id}",
            "definition": {
                "name": {"es-MX": f"Curso {data.curso_id}"}
            },
            "objectType": "Activity"
        }
    }

    # 3. Crear el XAPIStatement agregando la cadena JSON requerida
    statement_xapi = models.XAPIStatement(
        usuario_id=data.usuario_id,
        verb="completed",
        object_id=f"curso-{data.curso_id}",
        statement_json=json.dumps(payload_xapi) # <--- CAMPO OBLIGATORIO
    )
    db.add(statement_xapi)

    db.commit()
    return {"status": "ok", "mensaje": "Curso marcado como completado de forma persistente."}