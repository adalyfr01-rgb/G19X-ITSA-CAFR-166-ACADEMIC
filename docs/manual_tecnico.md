# MANUAL TÉCNICO DEL SISTEMA
## Guía de Arquitectura, Instalación, Configuración y Mantenimiento

**Proyecto:** Plataforma de Capacitación Inicial Personalizada (PluriOne Enterprise)  
**Cliente / Entorno:** PluriOne S.A. de C.V.  
**Caso de Estudio:** PluriOne S.A. de C.V.  
**Stack Tecnológico:** React.js, FastAPI (Python), PostgreSQL, Google Gemini API  
**Autor:** Carmen Adaly Flores Rendon  

---

## 1. Requisitos Previos y Entorno de Desarrollo

El sistema está diseñado para ejecutarse en cualquier entorno estándar de desarrollo web (Windows, macOS o Linux) que cuente con las siguientes herramientas básicas instaladas:

- **Python 3.11+:** Para la ejecución del servicio API REST en FastAPI y scripts de backend.
- **Node.js / npm (v18+):** Utilizado exclusivamente en desarrollo para gestionar paquetes del frontend y compilar la interfaz en React.
- **PostgreSQL 16+:** Sistema gestor de base de datos relacional (configurado localmente o en servidor).
- **Git:** Control de versiones para la gestión del repositorio.

---

## 2. Estructura y Módulos del Repositorio

El proyecto mantiene una separación clara entre la lógica del servidor (backend), la interfaz de usuario (frontend) y la documentación:

```text
capacitaciones/
├── backend/
│   ├── services/
│   │   └── ai_adapter.py    # Adaptador para integración con Google Gemini API y fallback
│   ├── database.py          # Configuración y sesión de SQLAlchemy para PostgreSQL
│   ├── main.py              # Punto de entrada de FastAPI, endpoints y middleware CORS
│   ├── models.py            # Modelos ORM (Usuario, Curso, Pregunta, Examen, etc.)
│   ├── security.py          # Hash de contraseñas (bcrypt) y gestión de tokens JWT
│   ├── seed.py              # Script automatizado para estructurar y popular la BD
│   ├── requirements.txt     # Librerías de Python requeridas
│   ├── .env                 # Variables de entorno locales
│   └── .env.example         # Plantilla de variables de entorno
├── docs/
│   └── manual_tecnico.md    # Documentación técnica y de mantenimiento
├── frontend/
│   ├── src/
│   │   ├── assets/          # Recurso estáticos e imágenes
│   │   ├── components/      # Componentes UI reutilizables
│   │   ├── pages/           # Vistas (AdminDashboard, Dashboard, Exam, Login, etc.)
│   │   ├── App.jsx          # Enrutador principal y estructura de la app React
│   │   └── main.jsx         # Punto de entrada de Vite / React
│   ├── package.json         # Dependencias del proyecto Frontend
│   └── vite.config.js       # Configuración del empaquetador Vite
└── README.md                # Guía rápida de uso del repositorio
```

## 3. Configuración de Variables de Entorno (.env)

Para que el backend se conecte correctamente a PostgreSQL, firme tokens de autenticación y comunique con la API de IA, se debe crear un archivo llamado `.env` dentro de la carpeta `backend/` tomando como base el archivo `.env.example`:

```env
# Conexión a Base de Datos PostgreSQL
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/capacitacion_db

# Credencial para Google Gemini
GEMINI_API_KEY=tu_api_key_aqui

# Llave para firmar los tokens JWT
JWT_SECRET_KEY=
```

## 4. Guía Paso a Paso de Instalación y Puesta en Marcha
Paso 1: Configurar y Desplegar el Backend (Servidor)
Abrir una terminal y navegar a la carpeta del servidor:

```bash
cd backend
```

Crear un entorno virtual de Python e instalar las librerías necesarias:
```bash
python -m venv venv
```

Activar en Windows:
```bash
venv\Scripts\activate
```

Instalar dependencias del proyecto:
```bash
pip install -r requirements.txt
```

Ejecutar el script automatizado para crear la base de datos y popular los datos iniciales de PluriOne S.A. de C.V.:
```bash
python seed.py
```

Iniciar el servidor API de FastAPI:
```bash
uvicorn main:app --reload
```

API activa en: http://localhost:8000

Documentación interactiva disponible en: http://localhost:8000/docs

Paso 2: Configurar y Desplegar el Frontend (Interfaz Web)
En una nueva terminal, navegar a la carpeta de la interfaz:

```bash
cd frontend
```

Instalar los paquetes e iniciar el servidor de desarrollo:
```bash
npm install
npm run dev
```

Interfaz web disponible en: http://localhost:5173

## 5. Funcionamiento del Script de Carga Inicial (seed.py)
El script seed.py permite preparar el entorno de prueba en un solo comando sin necesidad de insertar datos manualmente:

- Estructura de Base de Datos: Detecta las tablas en PostgreSQL y las crea si no existen.

- Carga de Organización: Registra los departamentos y puestos del entorno de PluriOne S.A. de C.V.

- Catálogo de Contenidos: Puebla el catálogo de cursos clasificados por sus niveles (Básico, Intermedio, Avanzado).

- Banco de Reactivos: Carga las preguntas y opciones del cuestionario diagnóstico inicial.

- Seguridad: Genera las contraseñas iniciales con hash seguro (bcrypt).

## 6. Mantenimiento del Sistema
- Incorporación de Cursos: Nuevos contenidos agregados por el administrador desde el panel web o la base de datos son detectados automáticamente por ai_adapter.py en las recomendaciones de la ruta adaptativa.

- Rotación de Claves: En caso de cambiar la clave de acceso a la API de Gemini, la firma JWT o la contraseña de PostgreSQL, únicamente se edita el archivo .env del backend sin alterar el código fuente.