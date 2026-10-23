from database import SessionLocal, engine
import models
from security import hash_password

def seed_database():
    db = SessionLocal()
    try:
        print("Limpiando y recreando tablas en la base de datos...")

        # Método limpio y seguro de SQLAlchemy para resetear la BD
        models.Base.metadata.drop_all(bind=engine)
        models.Base.metadata.create_all(bind=engine)

        # ---------------------------------------------------------------------------
        # 1. DEPARTAMENTOS Y PUESTOS
        # ---------------------------------------------------------------------------
        dept_prod = models.Departamento(
            nombre="Gestión de Productos y Proyectos",
            descripcion=(
                "Gestión integral del ciclo de vida de productos y proyectos"
                " corporativos."
            ),
        )
        dept_rh = models.Departamento(
            nombre="Recursos Humanos",
            descripcion="Gestión del talento, inducción y capacitaciones.",
        )
        dept_dev = models.Departamento(
            nombre="Desarrollo de Software",
            descripcion="Diseño, desarrollo y aseguramiento de calidad.",
        )
        dept_ventas = models.Departamento(
            nombre="Administración y Ventas",
            descripcion=(
                "Ventas, marketing digital, recursos humanos y contabilidad."
            ),
        )
        dept_fin = models.Departamento(
            nombre="Finanzas y Contabilidad",
            descripcion="Encargados de documentos y reportes administrativos.",
        )

        db.add_all([dept_prod, dept_rh, dept_dev, dept_ventas, dept_fin])
        db.commit()

        puestos = [
            models.Puesto(
                nombre="Product Manager", departamento_id=dept_prod.id
            ),
            models.Puesto(
                nombre="Director de Producto", departamento_id=dept_prod.id
            ),
            models.Puesto(
                nombre="Generalista de Recursos Humanos", departamento_id=dept_rh.id
            ),
            models.Puesto(
                nombre="Líder de Desarrollo", departamento_id=dept_dev.id
            ),
            models.Puesto(
                nombre="Desarrollador Backend", departamento_id=dept_dev.id
            ),
            models.Puesto(
                nombre="Gerente de Ventas / Business", departamento_id=dept_ventas.id
            ),
            models.Puesto(
                nombre="Especialista en Marketing Digital",
                departamento_id=dept_ventas.id,
            ),
            models.Puesto(
                nombre="Analista Financiero Corporativo", departamento_id=dept_fin.id
            ),
        ]
        db.add_all(puestos)
        db.commit()
        print("✓ 5 Departamentos y 8 Puestos oficiales creados.")

        # ---------------------------------------------------------------------------
        # 2. USUARIOS DE PRUEBA
        # ---------------------------------------------------------------------------
        admin_rh = models.Usuario(
            nombre="Ana Rojas Fuentes",
            email="ana.rojas@plurione.com",
            password=hash_password("password123"),
            rol="admin",
            departamento="Recursos Humanos",
            puesto="Generalista de Recursos Humanos",
        )
        emp_dev = models.Usuario(
            nombre="Carlos Mendoza",
            email="carlos.mendoza@plurione.com",
            password=hash_password("password123"),
            rol="empleado",
            departamento="Desarrollo de Software",
            puesto="Desarrollador Backend",
        )
        emp_ventas = models.Usuario(
            nombre="Mariana Gómez",
            email="mariana.gomez@plurione.com",
            password=hash_password("password123"),
            rol="empleado",
            departamento="Administración y Ventas",
            puesto="Gerente de Ventas / Business",
        )
        emp_product = models.Usuario(
            nombre="David Aguilar",
            email="david.aguilar@plurione.com",
            password=hash_password("password123"),
            rol="empleado",
            departamento="Gestión de Productos y Proyectos",
            puesto="Product Manager",
        )
        db.add_all([admin_rh, emp_dev, emp_ventas, emp_product])
        db.commit()
        print("✓ 4 Usuarios creados.")

        # ---------------------------------------------------------------------------
        # 3. BANCO DE PREGUNTAS DIAGNÓSTICAS (Índices e Opciones Verificadas 0-based)
        # ---------------------------------------------------------------------------
        preguntas = [
            # === DESARROLLADOR BACKEND (5 Preguntas) ===
            models.Pregunta(
                puesto="Desarrollador Backend",
                texto="¿Qué comando de Git se utiliza para subir cambios locales al repositorio remoto?",
                opciones=["git push", "git commit", "git pull", "git add"],
                opcion_correcta=0, # Index 0: git push
                categoria="Control de Versiones",
            ),
            models.Pregunta(
                puesto="Desarrollador Backend",
                texto="¿Qué método HTTP se utiliza habitualmente para actualizar un recurso existente en FastAPI?",
                opciones=["GET", "POST", "PUT", "DELETE"],
                opcion_correcta=2, # Index 2: PUT
                categoria="Backend API",
            ),
            models.Pregunta(
                puesto="Desarrollador Backend",
                texto="En ORMs como SQLAlchemy, ¿qué método confirma las transacciones pendientes en la base de datos?",
                opciones=["db.save()", "db.commit()", "db.execute()", "db.push()"],
                opcion_correcta=1, # Index 1: db.commit()
                categoria="Base de Datos",
            ),
            models.Pregunta(
                puesto="Desarrollador Backend",
                texto="¿Qué librería/estándar se utiliza comúnmente para la validación de esquemas de datos en FastAPI?",
                opciones=["Pydantic", "Marshmallow", "Django Forms", "Cerberus"],
                opcion_correcta=0, # Index 0: Pydantic
                categoria="Validación de Datos",
            ),
            models.Pregunta(
                puesto="Desarrollador Backend",
                texto="¿Cuál es el código de estado HTTP estándar para responder que un recurso no fue encontrado?",
                opciones=["200 OK", "401 Unauthorized", "404 Not Found", "500 Error"],
                opcion_correcta=2, # Index 2: 404 Not Found
                categoria="Protocolo HTTP",
            ),

            # === GERENTE DE VENTAS / BUSINESS (5 Preguntas) ===
            models.Pregunta(
                puesto="Gerente de Ventas / Business",
                texto="¿Cuál es el primer paso recomendado en el ciclo de prospección comercial?",
                opciones=[
                    "Cierre de contrato",
                    "Investigación de necesidades",
                    "Presentación de cotización",
                    "Manejo de objeciones",
                ],
                opcion_correcta=1, # Index 1: Investigación de necesidades
                categoria="Prospección Comercial",
            ),
            models.Pregunta(
                puesto="Gerente de Ventas / Business",
                texto="¿Qué significa el concepto de CRM en la gestión empresarial?",
                opciones=[
                    "Customer Relationship Management",
                    "Core Resource Model",
                    "Central Regional Marketing",
                    "Control Resource Manager",
                ],
                opcion_correcta=0, # Index 0: Customer Relationship Management
                categoria="Herramientas Comerciales",
            ),
            models.Pregunta(
                puesto="Gerente de Ventas / Business",
                texto="¿Qué métrica evalúa la proporción de prospectos que se convierten en clientes reales?",
                opciones=[
                    "Tasa de conversión",
                    "Churn rate",
                    "NPS",
                    "Costo de adquisición",
                ],
                opcion_correcta=0, # Index 0: Tasa de conversión
                categoria="Métricas Comerciales",
            ),
            models.Pregunta(
                puesto="Gerente de Ventas / Business",
                texto="En una negociación, ¿qué representa la técnica de 'Manejo de Objeciones'?",
                opciones=[
                    "Ignorar los comentarios del cliente",
                    "Transformar dudas en argumentos de valor",
                    "Bajar el precio inmediatamente",
                    "Finalizar la reunión abruptamente",
                ],
                opcion_correcta=1, # Index 1: Transformar dudas en argumentos de valor
                categoria="Técnicas de Negociación",
            ),
            models.Pregunta(
                puesto="Gerente de Ventas / Business",
                texto="¿Qué término describe el embudo que representa las etapas por las que pasa un cliente antes de comprar?",
                opciones=[
                    "Sales Pipeline",
                    "Gantt Chart",
                    "Product Roadmap",
                    "Backlog",
                ],
                opcion_correcta=0, # Index 0: Sales Pipeline
                categoria="Estrategia Comercial",
            ),

            # === PRODUCT MANAGER (5 Preguntas) ===
            models.Pregunta(
                puesto="Product Manager",
                texto="¿Qué metodología ágil se basa en iteraciones cortas llamadas Sprints?",
                opciones=["Scrum", "Waterfall", "Six Sigma", "ITIL"],
                opcion_correcta=0, # Index 0: Scrum
                categoria="Metodologías Ágiles",
            ),
            models.Pregunta(
                puesto="Product Manager",
                texto="¿Qué herramienta se utiliza para mapear la visión y evolución del producto a lo largo del tiempo?",
                opciones=[
                    "Product Roadmap",
                    "Diagrama de Flujo",
                    "Balanced Scorecard",
                    "Organigrama",
                ],
                opcion_correcta=0, # Index 0: Product Roadmap
                categoria="Estrategia de Producto",
            ),
            models.Pregunta(
                puesto="Product Manager",
                texto="¿Qué representan las siglas MVP en el desarrollo de productos?",
                opciones=[
                    "Minimum Viable Product",
                    "Most Valuable Partner",
                    "Maximum Value Process",
                    "Main Product Vision",
                ],
                opcion_correcta=0, # Index 0: Minimum Viable Product
                categoria="Desarrollo de Producto",
            ),
            models.Pregunta(
                puesto="Product Manager",
                texto="¿Cuál es el objetivo principal de la priorización del Backlog mediante el método RICE?",
                opciones=[
                    "Evaluar Reach, Impact, Confidence y Effort",
                    "Reducir costos operativos al mínimo",
                    "Asignar salarios a los desarrolladores",
                    "Crear campañas en redes sociales",
                ],
                opcion_correcta=0, # Index 0: Evaluar Reach, Impact...
                categoria="Gestión de Prioridades",
            ),
            models.Pregunta(
                puesto="Product Manager",
                texto="¿Qué métrica permite evaluar si los usuarios encuentran el valor central de un producto e interactúan continuamente?",
                opciones=[
                    "User Engagement / Retention",
                    "Bounce Rate",
                    "Page Views",
                    "Total Downloads",
                ],
                opcion_correcta=0, # Index 0: User Engagement / Retention
                categoria="Métricas de Producto",
            ),
        ]
        db.add_all(preguntas)
        db.commit()
        print("✓ 15 Preguntas de diagnóstico creadas con índices exactos.")

        # ---------------------------------------------------------------------------
        # 4. CATÁLOGO DE CURSOS (15 Cursos - 5 por puesto)
        # ---------------------------------------------------------------------------
        cursos = [
            # === DESARROLLADOR BACKEND ===
            models.Curso(
                titulo="Inducción a Herramientas de Desarrollo y Git",
                descripcion="Aprende el flujo de trabajo estándar en Git, ramas y Conventional Commits.",
                duracion="2 horas",
                nivel="Principiante",
                categoria="Tecnología",
                puesto_id="Desarrollador Backend",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Desarrollo de APIs RESTful con FastAPI y Python",
                descripcion="Dominio de endpoints, autenticación JWT, validaciones con Pydantic y SQLAlchemy.",
                duracion="5 horas",
                nivel="Intermedio",
                categoria="Tecnología",
                puesto_id="Desarrollador Backend",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Diseño de Bases de Datos Relacionales con PostgreSQL",
                descripcion="Modelado de datos, normalización, índices y optimización de consultas SQL.",
                duracion="4 horas",
                nivel="Intermedio",
                categoria="Tecnología",
                puesto_id="Desarrollador Backend",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Arquitectura de Microservicios y Clean Architecture",
                descripcion="Patrones de diseño de software backend, desacoplamiento y escalabilidad.",
                duracion="6 horas",
                nivel="Avanzado",
                categoria="Tecnología",
                puesto_id="Desarrollador Backend",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Seguridad en Web APIs y Protocolos OAuth2",
                descripcion="Protección contra ataques comunes (OWASP Top 10), encriptación y CORS.",
                duracion="3 horas",
                nivel="Avanzado",
                categoria="Tecnología",
                puesto_id="Desarrollador Backend",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),

            # === GERENTE DE VENTAS / BUSINESS ===
            models.Curso(
                titulo="Técnicas de Negociación y Cierre Efectivo",
                descripcion="Estrategias modernas de prospección, manejo de objeciones y comunicación.",
                duracion="3 horas",
                nivel="Principiante",
                categoria="Ventas",
                puesto_id="Gerente de Ventas / Business",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Gestión de CRM y Pipeline de Clientes",
                descripcion="Uso del CRM institucional para seguimiento de prospectos y métricas de conversión.",
                duracion="2 horas",
                nivel="Intermedio",
                categoria="Ventas",
                puesto_id="Gerente de Ventas / Business",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Estrategias B2B y Venta Consultiva",
                descripcion="Metodología SPIN Selling para negociaciones con cuentas corporativas grandes.",
                duracion="4 horas",
                nivel="Intermedio",
                categoria="Ventas",
                puesto_id="Gerente de Ventas / Business",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Pronóstico de Ventas y Proyecciones Comerciales",
                descripcion="Modelos cuantitativos para proyectar ingresos de ventas por trimestre.",
                duracion="3.5 horas",
                nivel="Avanzado",
                categoria="Ventas",
                puesto_id="Gerente de Ventas / Business",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Liderazgo y Gestión de Equipos Comerciales High-Performance",
                descripcion="Motivación, comisiones, KPIs clave y coaching para fuerza de ventas.",
                duracion="4 horas",
                nivel="Avanzado",
                categoria="Ventas",
                puesto_id="Gerente de Ventas / Business",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),

            # === PRODUCT MANAGER ===
            models.Curso(
                titulo="Fundamentos de Product Management y Roadmap",
                descripcion="Definición del ciclo de vida del producto, visión y estrategia corporativa.",
                duracion="4 horas",
                nivel="Principiante",
                categoria="Gestión",
                puesto_id="Product Manager",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Gestión de Proyectos Ágiles con Scrum y Kanban",
                descripcion="Gestión de backlog, Sprints, historias de usuario y métricas de agilidad.",
                duracion="3 horas",
                nivel="Intermedio",
                categoria="Gestión",
                puesto_id="Product Manager",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="User Research y Pruebas de Concepto",
                descripcion="Entrevistas a usuarios, diseño de hipótesis y validación rápida de MVPs.",
                duracion="3.5 horas",
                nivel="Intermedio",
                categoria="Gestión",
                puesto_id="Product Manager",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Analítica de Producto y Métricas de Crecimiento (North Star)",
                descripcion="Medición de adopción, retención, Churn y valor del cliente (LTV).",
                duracion="5 horas",
                nivel="Avanzado",
                categoria="Gestión",
                puesto_id="Product Manager",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
            models.Curso(
                titulo="Estrategias de Monetización y Modelos de Negocio SaaS",
                descripcion="Estructura de precios, modelos Freemium y escalamiento de productos digitales.",
                duracion="4 horas",
                nivel="Avanzado",
                categoria="Gestión",
                puesto_id="Product Manager",
                url_contenido="https://www.youtube.com/embed/dQw4w9WgXcQ",
                tipo_contenido="VIDEO",
            ),
        ]
        db.add_all(cursos)
        db.commit()
        print("✓ 15 Cursos creados (5 por puesto).")

        print("\n¡Base de datos poblada exitosamente sin inconsistencias!")

    except Exception as e:
        print(f"❌ Error al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()