import os
import json
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generar_ruta_aprendizaje(puesto_nombre: str, respuestas_diagnostico: list, cursos_disponibles: list):
    """
    Genera una ruta de aprendizaje adaptativa basada en el diagnóstico usando Gemini IA.
    Conserva los atributos originales de la base de datos (URLs, descripciones, duraciones, etc.).
    """
    
    # 1. Prompt enriquecido
    prompt = f"""
    Actúa como un Director de Capacitación Organizacional y Experto en Pedagogía.
    
    PUESTO EVALUADO: {puesto_nombre}
    RESULTADOS DEL DIAGNÓSTICO (PREGUNTAS Y RESPUESTAS OBTENIDAS):
    {json.dumps(respuestas_diagnostico, ensure_ascii=False)}

    CATÁLOGO DE CURSOS DISPONIBLES EN LA BASE DE DATOS:
    {json.dumps(cursos_disponibles, ensure_ascii=False)}

    INSTRUCCIONES:
    1. Analiza qué temas del diagnóstico respondió mal o con dudas el usuario para identificar sus brechas específicas de conocimiento.
    2. De los cursos del catálogo, selecciona los más relevantes para cerrar esas brechas y ordénalos pedagógicamente (priorizando las mayores deficiencias).
    3. Copia el campo 'descripcion' EXACTAMENTE como viene en el catálogo de entrada (NO inventes ni reescribas descripciones nuevas).
    4. INCLUYE el campo 'justificacion' redactado por ti, explicando brevemente por qué se le asigna dicho curso según sus fallos del diagnóstico.

    ESTRUCTURA OBLIGATORIA DE RESPUESTA (Únicamente JSON válido):
    {{
      "puesto": "{puesto_nombre}",
      "resumen_brechas": "Breve análisis clínico del nivel demostrado y áreas a reforzar.",
      "ruta": [
        {{
          "id": 1,
          "id_curso": 1,
          "titulo": "Nombre del curso tal como viene en el catálogo",
          "descripcion": "Descripción detallada del curso traída del catálogo",
          "justificacion": "Razón pedagógica personalizada basada en sus fallos del diagnóstico",
          "duracion": "Flexible",
          "nivel": "Principiante",
          "categoria": "Capacitación",
          "url_contenido": "https://link-real-del-curso",
          "orden_secuencia": 1
        }}
      ]
    }}
    """

    # 2. Configuración de Reintentos conservando gemini-3.6-flash
    max_retries = 3
    delay = 2  

    for intento in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            
            texto_limpio = response.text.strip()
            if texto_limpio.startswith("```json"):
                texto_limpio = texto_limpio.replace("```json", "", 1).rstrip("```").strip()
            elif texto_limpio.startswith("```"):
                texto_limpio = texto_limpio.replace("```", "", 1).rstrip("```").strip()

            datos_ia = json.loads(texto_limpio)
            print("🤖 [IA SUCCESS] Ruta adaptada correctamente por Gemini.")
            return datos_ia

        except APIError as e:
            if getattr(e, 'code', None) in [503, 429] and intento < max_retries - 1:
                tiempo_espera = delay * (intento + 1)
                print(f"[IA Retry] Servidor saturado ({e.code}). Reintentando en {tiempo_espera}s... ({intento + 1}/{max_retries})")
                time.sleep(tiempo_espera)
                continue
            
            print(f"Error en API de Gemini: {e}")
            break

        except Exception as e:
            print(f"Error procesando la respuesta de la IA: {e}")
            break

    # 3. Fallback con descripciones reales de la BD
    print("⚠️ [IA Fallback] Asignando cursos directamente desde la BD.")
    return {
        "puesto": puesto_nombre,
        "resumen_brechas": "Asignación inicial basada en catálogo por reajuste momentáneo del motor de IA.",
        "ruta": [
            {
                "id": c.get("id"),
                "id_curso": c.get("id"),
                "titulo": c.get("titulo"),
                "nombre": c.get("titulo"),
                "descripcion": c.get("descripcion") or "Curso asignado para refuerzo general.",
                "justificacion": c.get("descripcion") or "Curso recomendado para tu perfil.",
                "duracion": c.get("duracion") or "Flexible",
                "nivel": c.get("nivel") or "General",
                "categoria": c.get("categoria") or "Capacitación",
                "url_contenido": c.get("url_contenido") or "#",
                "orden_secuencia": idx + 1
            }
            for idx, c in enumerate(cursos_disponibles)
        ]
    }
    
def generar_evaluacion_final(puesto_nombre: str, cursos_asignados: list):
    """
    Genera un examen técnico usando Gemini (5 preguntas por curso).
    Incluye un Fallback enriquecido con opciones realistas en caso de contingencia.
    """
    import json
    import time
    from google.genai.errors import APIError

    
    nombres_cursos = [
        c.get("titulo") or c.get("nombre") or str(c) 
        for c in cursos_asignados
    ]
    
    total_cursos = len(nombres_cursos)
    preguntas_por_curso = 4  
    total_preguntas = total_cursos * preguntas_por_curso

    
    prompt = f"""
    Actúa como un evaluador técnico y académico experto en {puesto_nombre}.
    
    PUESTO DEL EVALUADO: {puesto_nombre}
    CURSOS COMPLETADOS: {json.dumps(nombres_cursos, ensure_ascii=False)}

    TAREA:
    Genera un examen de opción múltiple con nivel profesional para validar los conocimientos adquiridos.
    Debes generar exactamente {preguntas_por_curso} preguntas técnicas redactadas específicamente por cada uno de los {total_cursos} cursos asignados (Total: {total_preguntas} preguntas).

    REGLAS ESTRICTAS:
    1. "pregunta": Debe ser un caso práctico o pregunta técnica concreta sobre el temario del curso.
    2. "opciones": Debe ser un arreglo con 4 alternativas técnicas REALES y plausibles relacionadas con el tema (NUNCA usar respuestas genéricas como "Opción A", "Concepto A" o "Ninguna de las anteriores").
    3. "respuesta_correcta": Un número entero entre 0 y 3 indicando el índice de la opción correcta en el arreglo.
    4. "explicacion": Explicación técnica breve sustentando la respuesta correcta.
    5. Retorna ÚNICAMENTE la estructura JSON especificada a continuación:

    {{
      "titulo": "Evaluación Final de Capacitación",
      "total_preguntas": {total_preguntas},
      "preguntas": [
        {{
          "id": 1,
          "curso_asociado": "Nombre exacto de uno de los cursos",
          "pregunta": "¿Qué mecanismo garantiza la confidencialidad de la firma en un token JWT?",
          "opciones": [
            "El algoritmo de hashing HMAC o RSA en la firma",
            "El cifrado en base64 del Payload",
            "La inclusión de la clave secreta en los Headers",
            "La validación automática por parte del navegador"
          ],
          "respuesta_correcta": 0,
          "explicacion": "Los JWT se firman usando un secreto (HMAC) o una clave privada (RSA) para evitar su alteración."
        }}
      ]
    }}
    """

    # 2. Configuración de Reintentos
    max_retries = 3
    delay = 3

    for intento in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",  # O la versión activa de Gemini que utilices
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            texto_limpio = response.text.strip()
            if texto_limpio.startswith("```json"):
                texto_limpio = texto_limpio.replace("```json", "", 1).rstrip("```").strip()
            
            datos_evaluacion = json.loads(texto_limpio)
            # Validamos que Gemini devuelva preguntas antes de retornar
            if datos_evaluacion.get("preguntas") and len(datos_evaluacion["preguntas"]) > 0:
                return datos_evaluacion

        except APIError as e:
            if getattr(e, 'code', None) == 503 and intento < max_retries - 1:
                tiempo_espera = delay * (intento + 1)
                print(f"[IA Retry Exam] Servidor ocupado (503). Reintentando en {tiempo_espera}s...")
                time.sleep(tiempo_espera)
                continue
            print(f"Error en API de Gemini (Examen): {e}")
            break

        except Exception as e:
            print(f"Error inesperado al generar examen con IA: {e}")
            break

    # 3. Fallback Mejorado 
    print("[IA Fallback Exam] Generando preguntas de respaldo técnicas.")
    preguntas_fallback = []
    id_counter = 1

    for nombre_curso in nombres_cursos:
        # Pregunta 1 del curso
        preguntas_fallback.append({
            "id": id_counter,
            "curso_asociado": nombre_curso,
            "pregunta": f"¿Cuál es el objetivo principal aplicado en el módulo de {nombre_curso}?",
            "opciones": [
                f"Establecer buenas prácticas y estándares técnicos en {nombre_curso}.",
                "Reducir la complejidad de lectura reemplazando arquitecturas.",
                "Sustituir el uso de bases de datos por archivos locales.",
                "Aumentar el uso de recursos del servidor sin optimización."
            ],
            "respuesta_correcta": 0,
            "explicacion": f"El estándar principal de {nombre_curso} busca implementar mejores prácticas."
        })
        id_counter += 1

        
        preguntas_fallback.append({
            "id": id_counter,
            "curso_asociado": nombre_curso,
            "pregunta": f"¿Qué beneficio principal aporta la correcta implementación de {nombre_curso} en producción?",
            "opciones": [
                "Mayor consumo de ancho de banda.",
                "Mayor escalabilidad, seguridad y mantenibilidad del software.",
                "Eliminación total de pruebas unitarias y de integración.",
                "Desactivación de los registros de auditoría y logs."
            ],
            "respuesta_correcta": 1,
            "explicacion": f"La aplicación de {nombre_curso} promueve código seguro y escalable."
        })
        id_counter += 1

    return {
        "titulo": "Evaluación Final de Capacitación",
        "total_preguntas": len(preguntas_fallback),
        "preguntas": preguntas_fallback
    }