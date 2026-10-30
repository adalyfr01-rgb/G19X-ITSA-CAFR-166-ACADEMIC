import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api';

export const GestionPreguntasRH = () => {
  const [estructura, setEstructura] = useState([]);
  const [preguntas, setPreguntas] = useState([]);
  const [idEditando, setIdEditando] = useState(null);
  
  const [departamentoId, setDepartamentoId] = useState('');
  const [puestoId, setPuestoId] = useState('');
  const [texto, setTexto] = useState('');
  const [opciones, setOpciones] = useState(['', '', '', '']);
  const [opcionCorrecta, setOpcionCorrecta] = useState(0);
  const [categoria, setCategoria] = useState('');
  const [mensaje, setMensaje] = useState(null);

  useEffect(() => {
    obtenerEstructura();
    obtenerPreguntas();
  }, []);

  // Cargar Estructura Organizacional
  const obtenerEstructura = async () => {
    try {
      const res = await apiFetch('/api/admin/estructura');
      if (res.ok) {
        const data = await res.json();
        setEstructura(data);
      }
    } catch (err) {
      console.error('Error al cargar la estructura:', err);
    }
  };

  // Cargar Preguntas Registradas
  const obtenerPreguntas = async () => {
    try {
      const res = await apiFetch('/api/admin/preguntas');
      if (!res.ok) throw new Error("Error de autorización");
      const data = await res.json();
      setPreguntas(data);
    } catch (err) {
      console.error("Error al obtener preguntas de admin:", err);
    }
  };

  // Función helper para obtener el NOMBRE DEL PUESTO a partir de su ID
  const obtenerNombrePuesto = (puestoIdOTexto) => {
    if (!puestoIdOTexto) return 'Sin asignar';
    
    // Recorremos la estructura para buscar el ID del puesto
    for (const dep of estructura) {
      if (dep.puestos) {
        const puestoEncontrado = dep.puestos.find(
          (pst) => String(pst.id) === String(puestoIdOTexto)
        );
        if (puestoEncontrado) {
          return puestoEncontrado.nombre;
        }
      }
    }
    // Si ya viene el nombre directo como texto en lugar de ID
    return puestoIdOTexto;
  };

  const deptoSeleccionado = estructura.find((d) => String(d.id) === String(departamentoId));
  const puestosDisponibles = deptoSeleccionado ? deptoSeleccionado.puestos : [];

  const handleOpcionChange = (index, value) => {
    const nuevas = [...opciones];
    nuevas[index] = value;
    setOpciones(nuevas);
  };

  const limpiarFormulario = () => {
    setIdEditando(null);
    setTexto('');
    setOpciones(['', '', '', '']);
    setOpcionCorrecta(0);
    setCategoria('');
    setDepartamentoId('');
    setPuestoId('');
  };

  // Guardar / Editar Pregunta
  const guardarPregunta = async (e) => {
    e.preventDefault();
    setMensaje(null);

    if (!puestoId) {
      setMensaje({ tipo: 'error', texto: 'Por favor selecciona un departamento y un puesto válido.' });
      return;
    }

    const payload = {
      puesto: String(puestoId),
      texto,
      opciones,
      opcion_correcta: parseInt(opcionCorrecta),
      categoria: categoria || 'General'
    };

    const url = idEditando
      ? `/api/admin/preguntas/actualizar/${idEditando}`
      : '/api/admin/preguntas/crear';

    const method = idEditando ? 'PUT' : 'POST';

    try {
      const res = await apiFetch(url, {
        method,
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setMensaje({
          tipo: 'éxito',
          texto: idEditando 
            ? '¡Pregunta actualizada en la BD correctamente!' 
            : '¡Pregunta guardada en la BD correctamente!'
        });
        limpiarFormulario();
        obtenerPreguntas();
      } else {
        setMensaje({ tipo: 'error', texto: 'Error al procesar la pregunta en la BD.' });
      }
    } catch (err) {
      console.error(err);
      setMensaje({ tipo: 'error', texto: 'Error de conexión con el backend.' });
    }
  };

  // Cargar para Editar
  const handleEditar = (p) => {
    setIdEditando(p.id);
    setTexto(p.texto || '');
    setOpciones(p.opciones || ['', '', '', '']);
    setOpcionCorrecta(p.opcion_correcta ?? 0);
    setCategoria(p.categoria || '');
    setPuestoId(p.puesto || '');

    // Autoseleccionar departamento según el puesto
    for (const dep of estructura) {
      if (dep.puestos && dep.puestos.some((pst) => String(pst.id) === String(p.puesto))) {
        setDepartamentoId(dep.id);
        break;
      }
    }
    setMensaje(null);
  };

  // Eliminar
  const handleEliminar = async (id) => {
    if (window.confirm("¿Estás seguro de que deseas eliminar esta pregunta del diagnóstico?")) {
      try {
        const res = await apiFetch(`/api/admin/preguntas/eliminar/${id}`, {
          method: 'DELETE'
        });

        if (res.ok) {
          setMensaje({ tipo: 'éxito', texto: 'Pregunta eliminada de la base de datos.' });
          obtenerPreguntas();
        } else {
          setMensaje({ tipo: 'error', texto: 'Error al eliminar la pregunta.' });
        }
      } catch (err) {
        console.error("Error:", err);
        setMensaje({ tipo: 'error', texto: 'Error de conexión con el backend.' });
      }
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* FORMULARIO SUPERIOR */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {idEditando ? "Editar Pregunta Diagnóstica" : "Banco de Preguntas Diagnósticas (RH)"}
            </h2>
            <p className="text-xs text-slate-500">
              Agrega o modifica preguntas para que la IA evalúe las competencias del alumno.
            </p>
          </div>
          {idEditando && (
            <button
              onClick={limpiarFormulario}
              className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs font-semibold"
            >
              Cancelar Edición
            </button>
          )}
        </div>

        {mensaje && (
          <div
            className={`p-3 rounded-xl text-xs font-semibold ${
              mensaje.tipo === 'éxito'
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {mensaje.texto}
          </div>
        )}

        <form onSubmit={guardarPregunta} className="space-y-4 text-sm">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Departamento:</label>
              <select
                value={departamentoId}
                onChange={(e) => {
                  setDepartamentoId(e.target.value);
                  setPuestoId('');
                }}
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              >
                <option value="">-- Selecciona Departamento --</option>
                {estructura.map((dep) => (
                  <option key={dep.id} value={dep.id}>
                    {dep.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Puesto Asignado:</label>
              <select
                value={puestoId}
                onChange={(e) => setPuestoId(e.target.value)}
                disabled={!departamentoId}
                required
                className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:opacity-50"
              >
                <option value="">-- Selecciona Puesto --</option>
                {puestosDisponibles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Pregunta:</label>
            <textarea
              rows="2"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Ej. ¿Qué librería de Python utiliza FastAPI para la validación de datos?"
              required
              className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-600">
              Opciones (Selecciona el radio button de la respuesta correcta):
            </label>
            {opciones.map((op, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="correcta"
                  checked={parseInt(opcionCorrecta) === idx}
                  onChange={() => setOpcionCorrecta(idx)}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                <input
                  type="text"
                  placeholder={`Opción ${idx + 1}`}
                  value={op}
                  onChange={(e) => handleOpcionChange(idx, e.target.value)}
                  required
                  className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>
            ))}
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 mb-1">Categoría / Tema:</label>
            <input
              type="text"
              placeholder="Ej. FastAPI, Git, Bases de Datos"
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              className="w-full p-2 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>

          <button
            type="submit"
            className={`w-full py-2.5 text-white font-semibold rounded-xl text-xs shadow-sm transition-colors ${
              idEditando 
                ? 'bg-amber-600 hover:bg-amber-700' 
                : 'bg-indigo-600 hover:bg-indigo-700'
            }`}
          >
            {idEditando ? "Actualizar Pregunta" : "Guardar Pregunta"}
          </button>
        </form>
      </div>

      {/* TABLA MEJORADA DE PREGUNTAS DIAGNÓSTICAS REGISTRADAS */}
      <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="text-base font-bold text-slate-900">
          Preguntas Registradas ({preguntas.length})
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-600">
            <thead className="bg-slate-50 text-slate-500 uppercase">
              <tr>
                <th className="px-4 py-3">Pregunta</th>
                <th className="px-4 py-3">Puesto Dirigido</th>
                <th className="px-4 py-3">Respuesta Correcta</th>
                <th className="px-4 py-3">Categoría</th>
                <th className="px-4 py-3 text-right">ACCIÓN</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {preguntas.map((p) => {
                const idxCorrecto = p.opcion_correcta ?? 0;
                const textoRespuestaCorrecta = p.opciones && p.opciones[idxCorrecto] 
                  ? p.opciones[idxCorrecto] 
                  : `Opción ${idxCorrecto + 1}`;

                return (
                  <tr key={p.id} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-medium text-slate-900 max-w-xs truncate" title={p.texto}>
                      {p.texto}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-700">
                      {obtenerNombrePuesto(p.puesto)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-md text-[11px] font-medium border border-emerald-200">
                        ✓ {textoRespuestaCorrecta}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-md text-[10px] font-semibold">
                        {p.categoria || 'General'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right space-x-2 whitespace-nowrap">
                      <button
                        onClick={() => handleEditar(p)}
                        className="px-3 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 rounded-lg text-xs font-semibold transition-colors"
                      >
                        Editar
                      </button>
                      <button
                        onClick={() => handleEliminar(p.id)}
                        className="px-3 py-1 bg-rose-50 hover:bg-rose-100 text-rose-600 rounded-lg text-xs font-semibold transition-colors"
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                );
              })}
              {preguntas.length === 0 && (
                <tr>
                  <td colSpan="5" className="text-center py-6 text-slate-400">
                    No hay preguntas diagnósticas registradas aún en PostgreSQL.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};