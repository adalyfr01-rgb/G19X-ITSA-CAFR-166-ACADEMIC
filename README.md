# Plataforma de Capacitación Inicial Personalizada

**Alumno:** Carmen Adaly Flores Rendon · **Matrícula:** G19X-ITSA-CAFR-166  
**Institución:** Instituto Tecnológico Superior de Atlixco  

## Qué hace

Es una plataforma web para el proceso de capacitación del personal de nuevo ingreso. Aunque es una solución genérica diseñada para adaptarse a los planes de estudio y requerimientos de cualquier empresa u organización, para efectos de esta evaluación está configurada y cargada con los contenidos de PluriOne S.A. de C.V.

## Integración con IA

Utiliza la API de Google Gemini para la generación dinámica de rutas de aprendizaje adaptativas y evaluaciones diagnósticas según el perfil y puesto del empleado.

## Qué necesitas instalado

- Python 3.11+
- Node.js 18+
- PostgreSQL 16+

## Configuración

Copia el archivo `.env.example` a `.env` dentro de la carpeta `backend/` y reemplaza los valores con tus credenciales locales (`DATABASE_URL` para PostgreSQL, `GEMINI_API_KEY` para la IA y `JWT_SECRET_KEY` para la firma de tokens JWT).

> **Nota importante:** El archivo `.env` debe existir obligatoriamente antes de ejecutar cualquier script o iniciar el servidor, ya que `database.py` requiere la variable `DATABASE_URL` para establecer la conexión a la base de datos.

## Base de datos

1. Crea una base de datos vacía llamada `capacitacion_db` en PostgreSQL.
2. Para cargar la estructura y los datos de prueba iniciales, ejecuta desde la carpeta `backend/`:

```bash
python seed.py
```
> ⚠️ **Atención si ya tenías la base de datos creada previamente:**  
> Si tu base de datos ya contenía usuarios con contraseñas guardadas en texto plano (sin cifrar), es **necesario borrar esos usuarios o eliminar y recrear la base de datos `capacitacion_db`** antes de volver a ejecutar `python seed.py`. Debido a que `seed.py` no sobrescribe usuarios existentes y el sistema ahora requiere autenticación con contraseñas cifradas (hash bcrypt), el inicio de sesión no reconocerá las contraseñas antiguas sin cifrar.

## Cómo instalarlo y ejecutarlo

**Backend (FastAPI):**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend (React + Vite):**
```bash
cd frontend
npm install
npm run dev
```
### Configuración de Variables de Entorno del Frontend
Crea un archivo `.env` dentro de `frontend/` tomando como base `frontend/.env.example`:
`VITE_API_URL=http://localhost:8000`

Se abre en http://localhost:5173

## Usuarios de Prueba

Para probar el sistema, inicia sesión ingresando con **correo electrónico** y **contraseña**:

### Administradores / Recursos Humanos
- **Ana Rojas:** `ana.rojas@plurione.com` / `password123`

### Empleados
- **Carlos Mendoza:** `carlos.mendoza@plurione.com` / `password123`
- **Mariana Gómez:** `mariana.gomez@plurione.com` / `password123`
- **David Aguilar:** `david.aguilar@plurione.com` / `password123`

## Lo que todavía no funciona
Actualmente ninguna funcionalidad del flujo principal presenta fallos. El sistema opera de manera integral desde el inicio de sesión hasta la evaluación final y administración de RH.