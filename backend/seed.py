from database import SessionLocal, engine
import models
from security import hash_password

# Crear las tablas en la base de datos si no existen
models.Base.metadata.create_all(bind=engine)

def seed_database():
    db = SessionLocal()
    try:
        print("Iniciando carga amplia de datos de prueba...")

        # 1. DEPARTAMENTOS Y PUESTOS
        if not db.query(models.Departamento).first():
            dept_ti = models.Departamento(nombre="Tecnología e Innovación", descripcion="Área de TI, infraestructura y desarrollo de software")
            dept_rh = models.Departamento(nombre="Recursos Humanos", descripcion="Gestión del talento, inducción y capacitaciones")
            dept_ventas = models.Departamento(nombre="Ventas y Comercial", descripcion="Atención a clientes y estrategias comerciales")
            db.add_all([dept_ti, dept_rh, dept_ventas])
            db.commit()

            puesto_dev = models.Puesto(nombre="Desarrollador Junior", departamento_id=dept_ti.id)
            puesto_sys = models.Puesto(nombre="Administrador de Sistemas", departamento_id=dept_ti.id)
            puesto_rh = models.Puesto(nombre="Analista de Capacitación", departamento_id=dept_rh.id)
            puesto_ejecutivo = models.Puesto(nombre="Ejecutivo de Ventas", departamento_id=dept_ventas.id)
            db.add_all([puesto_dev, puesto_sys, puesto_rh, puesto_ejecutivo])
            db.commit()
            print("✓ 3 Departamentos y 4 Puestos creados.")

        # 2. USUARIOS DE PRUEBA
        if not db.query(models.Usuario).first():
            admin_rh = models.Usuario(
                nombre="Ana Rojas Fuentes",
                email="ana.rojas@plurione.com",
                password=hash_password("password123"),
                rol="admin",
                departamento="Recursos Humanos",
                puesto="Analista de Capacitación"
            )
            emp_dev = models.Usuario(
                nombre="Carlos Mendoza",
                email="carlos.mendoza@plurione.com",
                password=hash_password("password123"),
                rol="empleado",
                departamento="Tecnología e Innovación",
                puesto="Desarrollador Junior"
            )
            emp_ventas = models.Usuario(
                nombre="Mariana Gómez",
                email="mariana.gomez@plurione.com",
                password=hash_password("password123"),
                rol="empleado",
                departamento="Ventas y Comercial",
                puesto="Ejecutivo de Ventas"
            )
            db.add_all([admin_rh, emp_dev, emp_ventas])
            db.commit()
            print("✓ 3 Usuarios de prueba creados (1 Admin, 2 Empleados).")

        # 3. BANCO DE PREGUNTAS DIAGNÓSTICAS (6 PREGUNTAS)
        if not db.query(models.Pregunta).first():
            preguntas = [
                # Preguntas Desarrollo
                models.Pregunta(
                    puesto="Desarrollador Junior",
                    texto="¿Qué comando de Git se utiliza para subir cambios locales al repositorio remoto?",
                    opciones=["git push", "git commit", "git pull", "git add"],
                    opcion_correcta=0,
                    categoria="Control de Versiones"
                ),
                models.Pregunta(
                    puesto="Desarrollador Junior",
                    texto="¿Qué método HTTP se utiliza habitualmente para actualizar un recurso existente en FastAPI?",
                    opciones=["GET", "POST", "PUT", "DELETE"],
                    opcion_correcta=2,
                    categoria="Backend API"
                ),
                models.Pregunta(
                    puesto="Desarrollador Junior",
                    texto="En ORMs como SQLAlchemy, ¿qué método confirma las transacciones pendientes en la base de datos?",
                    opciones=["db.save()", "db.commit()", "db.execute()", "db.push()"],
                    opcion_correcta=1,
                    categoria="Base de Datos"
                ),
                # Preguntas Ventas / RRHH / General
                models.Pregunta(
                    puesto="Ejecutivo de Ventas",
                    texto="¿Cuál es el primer paso recomendado en el ciclo de prospección comercial?",
                    opciones=["Cierre de contrato", "Investigación de necesidades", "Presentación de cotización", "Manejo de objeciones"],
                    opcion_correcta=1,
                    categoria="Prospección Comercial"
                ),
                models.Pregunta(
                    puesto="Ejecutivo de Ventas",
                    texto="¿Qué significa el concepto de CRM en la gestión empresarial?",
                    opciones=["Customer Relationship Management", "Core Resource Model", "Central Regional Marketing", "Control Resource Manager"],
                    opcion_correcta=0,
                    categoria="Herramientas Comerciales"
                ),
                models.Pregunta(
                    puesto="Analista de Capacitación",
                    texto="¿Qué métrica permite evaluar la efectividad del aprendizaje según el estándar xAPI?",
                    opciones=["Eventos de interacción (Verbo-Objeto)", "Horas de conexión diarias", "Número de descargas en PDF", "Porcentaje de clicks"],
                    opcion_correcta=0,
                    categoria="Estándares LRS"
                )
            ]
            db.add_all(preguntas)
            db.commit()
            print("✓ 6 Preguntas de diagnóstico creadas.")

        # 4. CATÁLOGO DE CURSOS (5 CURSOS)
        if not db.query(models.Curso).first():
            cursos = [
                models.Curso(
                    titulo="Inducción a Herramientas de Desarrollo y Git",
                    descripcion="Aprende el flujo de trabajo estándar en Git, ramas y Conventional Commits.",
                    duracion="2 horas",
                    nivel="Principiante",
                    categoria="Tecnología",
                    puesto_id="Desarrollador Junior",
                    url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                    tipo_contenido="VIDEO"
                ),
                models.Curso(
                    titulo="Desarrollo de APIs RESTful con FastAPI y Python",
                    descripcion="Dominio de endpoints, autenticación, validaciones con Pydantic y ORM SQLAlchemy.",
                    duracion="5 horas",
                    nivel="Intermedio",
                    categoria="Tecnología",
                    puesto_id="Desarrollador Junior",
                    url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                    tipo_contenido="VIDEO"
                ),
                models.Curso(
                    titulo="Técnicas de Negociación y Cierre Efectivo",
                    descripcion="Estrategias modernas de prospección, manejo de objeciones y comunicación persuasiva.",
                    duracion="3 horas",
                    nivel="Principiante",
                    categoria="Ventas",
                    puesto_id="Ejecutivo de Ventas",
                    url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                    tipo_contenido="VIDEO"
                ),
                models.Curso(
                    titulo="Gestión de CRM y Pipeline de Clientes",
                    descripcion="Uso del CRM institucional para seguimiento de prospectos y métricas de conversión.",
                    duracion="2 horas",
                    nivel="Intermedio",
                    categoria="Ventas",
                    puesto_id="Ejecutivo de Ventas",
                    url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                    tipo_contenido="VIDEO"
                ),
                models.Curso(
                    titulo="Seguridad de la Información y Protección de Datos",
                    descripcion="Buenas prácticas de ciberseguridad, gestión de contraseñas y privacidad empresarial.",
                    duracion="1.5 horas",
                    nivel="Principiante",
                    categoria="General",
                    puesto_id="General",
                    url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                    tipo_contenido="VIDEO"
                )
            ]
            db.add_all(cursos)
            db.commit()
            print("✓ 5 Cursos variados creados.")

        print("\n¡Base de datos poblada exitosamente con el catálogo completo!")

    except Exception as e:
        print(f"Error al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()