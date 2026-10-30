import React, { useState } from 'react';
import { apiFetch } from '../api';

export const ModalExamen = ({ examenData, intentosRestantes, onClose, FinalizarExamen, usuarioId }) => {
  const [preguntaActual, setPreguntaActual] = useState(0);
  const [respuestasSeleccionadas, setRespuestasSeleccionadas] = useState({});
  const [examenEnviado, setExamenEnviado] = useState(false);
  const [resultado, setResultado] = useState(null);

  const preguntas = examenData?.preguntas || [];
  const totalPreguntas = preguntas.length;

  const seleccionarOpción = (indiceOpcion) => {
    if (examenEnviado) return;
    setRespuestasSeleccionadas({
      ...respuestasSeleccionadas,
      [preguntaActual]: indiceOpcion
    });
  };

  const calcularCalificacion = async () => {
    let aciertos = 0;
    preguntas.forEach((q, idx) => {
      if (respuestasSeleccionadas[idx] === q.respuesta_correcta) {
        aciertos++;
      }
    });

    const puntaje = Math.round((aciertos / (totalPreguntas || 1)) * 100);
    const aprobado = puntaje >= 80;

    const res = {
      aciertos,
      totalPreguntas,
      puntaje,
      aprobado
    };

    setResultado(res);
    setExamenEnviado(true);

    // 1. Enviar evento xAPI al Backend usando apiFetch (inyecta automáticamente el Bearer token)
    try {
      const activeUserId = usuarioId || 1;
      await apiFetch('/api/xapi/statements', {
        method: 'POST',
        body: JSON.stringify({
          usuario_id: activeUserId,
          verb: aprobado ? 'passed' : 'failed',
          object_id: 'evaluacion-final-capacitacion',
          statement_json: {
            score: puntaje,
            aciertos: aciertos,
            total_preguntas: totalPreguntas,
            status: aprobado ? 'passed' : 'failed'
          }
        })
      });
      console.log('✅ Evento xAPI de examen final registrado');
    } catch (err) {
      console.error('❌ Error registrando evento xAPI en ModalExamen:', err);
    }

    // 2. Notificar al padre
    if (FinalizarExamen) {
      FinalizarExamen(res);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6 relative flex flex-col max-h-[90vh]">
        
        {/* Cabecera */}
        <div className="flex justify-between items-center border-b pb-4 mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-800">Evaluación Final de Capacitación</h2>
            <p className="text-xs text-slate-500">
              Intentos restantes: <span className="font-semibold text-indigo-600">{intentosRestantes}</span>
            </p>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 font-bold text-lg"
          >
            ✕
          </button>
        </div>

        {/* Vista del Examen (preguntas) */}
        {!examenEnviado ? (
          <div className="flex-1 overflow-y-auto">
            {/* Barra de Progreso del Examen */}
            <div className="w-full bg-slate-100 rounded-full h-2 mb-4">
              <div 
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((preguntaActual + 1) / (totalPreguntas || 1)) * 100}%` }}
              ></div>
            </div>

            <div className="mb-2">
              <span className="text-xs font-semibold px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-md">
                Curso: {preguntas[preguntaActual]?.curso_asociado || 'General'}
              </span>
              <span className="text-xs text-slate-400 ml-2">
                Pregunta {preguntaActual + 1} de {totalPreguntas}
              </span>
            </div>

            <h3 className="text-base font-semibold text-slate-800 mb-4">
              {preguntas[preguntaActual]?.pregunta}
            </h3>

            {/* Opciones de respuesta */}
            <div className="space-y-2 mb-6">
              {preguntas[preguntaActual]?.opciones.map((opcion, idx) => {
                const seleccionada = respuestasSeleccionadas[preguntaActual] === idx;
                return (
                  <button
                    key={idx}
                    onClick={() => seleccionarOpción(idx)}
                    className={`w-full text-left p-3 rounded-xl border text-sm transition-all ${
                      seleccionada 
                        ? 'border-indigo-600 bg-indigo-50/60 font-medium text-indigo-900 shadow-sm' 
                        : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    <span className="font-bold mr-2">{String.fromCharCode(65 + idx)}.</span>
                    {opcion}
                  </button>
                );
              })}
            </div>

            {/* Navegación */}
            <div className="flex justify-between items-center pt-4 border-t">
              <button
                disabled={preguntaActual === 0}
                onClick={() => setPreguntaActual(preguntaActual - 1)}
                className="px-4 py-2 text-sm text-slate-600 bg-slate-100 rounded-lg disabled:opacity-40"
              >
                Anterior
              </button>

              {preguntaActual < totalPreguntas - 1 ? (
                <button
                  disabled={respuestasSeleccionadas[preguntaActual] === undefined}
                  onClick={() => setPreguntaActual(preguntaActual + 1)}
                  className="px-4 py-2 text-sm bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-40"
                >
                  Siguiente
                </button>
              ) : (
                <button
                  disabled={Object.keys(respuestasSeleccionadas).length < totalPreguntas}
                  onClick={calcularCalificacion}
                  className="px-5 py-2 text-sm bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700 disabled:opacity-40"
                >
                  Finalizar Examen
                </button>
              )}
            </div>
          </div>
        ) : (
          /* PANTALLA DE RESULTADOS */
          <div className="text-center py-6 flex-1 flex flex-col justify-center items-center">
            <div className={`w-20 h-20 rounded-full flex items-center justify-center text-3xl mb-4 ${
              resultado.aprobado ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'
            }`}>
              {resultado.aprobado ? '🎉' : '❌'}
            </div>

            <h3 className="text-2xl font-bold text-slate-800 mb-1">
              {resultado.aprobado ? '¡Felicidades, Aprobaste!' : 'Examen No Aprobado'}
            </h3>

            <p className="text-sm text-slate-500 mb-4">
              Puntaje obtenido: <span className="font-bold text-slate-800">{resultado.puntaje} / 100 pts</span> 
              ({resultado.aciertos} de {resultado.totalPreguntas} correctas)
            </p>

            {resultado.aprobado ? (
              <p className="text-sm text-emerald-700 bg-emerald-50 p-3 rounded-lg border border-emerald-200 max-w-md mb-6">
                Has demostrado el dominio suficiente en los cursos recomendados. Tu avance ha sido guardado.
              </p>
            ) : (
              <p className="text-sm text-rose-700 bg-rose-50 p-3 rounded-lg border border-rose-200 max-w-md mb-6">
                Necesitas un mínimo de 80 pts para aprobar. Revisa nuevamente los materiales e inténtalo de nuevo.
              </p>
            )}

            <button
              onClick={onClose}
              className="px-6 py-2.5 bg-slate-800 text-white text-sm font-medium rounded-xl hover:bg-slate-900"
            >
              Cerrar
            </button>
          </div>
        )}

      </div>
    </div>
  );
};