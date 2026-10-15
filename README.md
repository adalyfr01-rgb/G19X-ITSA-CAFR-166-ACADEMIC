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

## Base de datos

1. Crea una base vacía llamada `capacitacion_db`.
2. Para cargar la estructura y datos de prueba, ejecuta desde la carpeta `backend/`:

```bash
python seed.py
```

## Configuración
Copia el archivo `.env.example` a `.env` dentro de la carpeta `backend/` y reemplaza los valores con tus credenciales locales (`DATABASE_URL` para PostgreSQL y `GEMINI_API_KEY` para la IA).

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

Se abre en http://localhost:5173

## Usuario de prueba

Administrador (RH): ana.rojas@plurione.com / password123
Empleado (Dev): carlos.mendoza@plurione.com / password123
Empleado (Ventas): mariana.gomez@plurione.com / password123

## Lo que todavía no funciona
El inicio de sesión con cuenta de Microsoft es una simulación de interfaz para fines del entorno de prueba local (no conecta a un Azure Active Directory / Tenant de producción real).