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
1. Configuración del Backend
Copia el archivo `.env.example` a `.env` dentro de la carpeta `backend/` y ajusta tus credenciales locales:

```bash
cd backend
cp .env.example .env
```
Abre el archivo backend/.env y completa las variables:
- `DATABASE_URL`: Cadena de conexión para PostgreSQL (ej. `postgresql://usuario:password@localhost:5432/capacitacion_db`).
- `GEMINI_API_KEY`: Clave de API para Google Gemini (generación de rutas e IA).
- `JWT_SECRET_KEY`: Clave secreta para la firma de tokens JWT.
Puedes generar una ejecutando en la terminal:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

- `CORS_ORIGINS`: Lista de dominios permitidos para peticiones CORS separados por coma (ej. `http://localhost:5173`).

> **Nota importante:** El archivo backend/.env debe existir obligatoriamente antes de ejecutar cualquier script o iniciar el servidor, ya que database.py y security.py requieren estas variables.

2. Configuración del Frontend
Crea el archivo `.env` en la carpeta `frontend/` a partir de su plantilla antes de iniciar el cliente:

```bash
cd frontend
cp .env.example .env
```
Verifica que contenga la URL del backend: `VITE_API_URL=http://localhost:8000`

## Cómo instalarlo y ejecutarlo

**Backend (FastAPI):**
```bash
cd backend
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
```

## Base de datos

1. Crea una base de datos vacía llamada `capacitacion_db` en PostgreSQL.
2. Con el entorno virtual del backend activo (venv), ejecuta desde la carpeta `backend/`:

```bash
python seed.py
```
> ⚠️ **Atención si ya tenías la base de datos creada previamente:**  
> Si tu base de datos ya contenía usuarios con contraseñas guardadas en texto plano (sin cifrar), es **necesario eliminar y recrear la base de datos `capacitacion_db`** antes de volver a ejecutar `python seed.py`. Debido a que `seed.py` no sobrescribe usuarios existentes y el sistema ahora requiere autenticación con contraseñas cifradas (hash bcrypt), el inicio de sesión no reconocerá las contraseñas antiguas sin cifrar.

**Inicia el servidor backend:**

```bash
uvicorn main:app --reload
```
El servidor backend estará corriendo en: http://localhost:8000

## Levantar Frontend (React + Vite)
En una segunda terminal, dirígete a la carpeta `frontend/`:

```bash
cd frontend
npm install
npm run dev
```
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
El flujo principal de autenticación, diagnóstico con IA, plan de capacitación y panel de RH se encuentra operativo. Sin embargo, para efectos de alcance del proyecto y de esta entrega, existen las siguientes consideraciones técnicas y alcances conocidos:

1. **Alcance de Exportación de Métricas:** El botón de exportación a CSV en el panel de RH descarga el reporte de los eventos y registros de interacción (xAPI), sin incluir reportes personalizados o avanzados por usuario.
2. **Recuperación de Contraseña:** El sistema no cuenta con un flujo para restablecer o recuperar contraseñas mediante correo electrónico en caso de olvido.
3. **Calificación del Examen Final:** La evaluación y cálculo de la calificación del examen final se procesa directamente en el navegador (cliente) y no valida el resultado desde el backend.