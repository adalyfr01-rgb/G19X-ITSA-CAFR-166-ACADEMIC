import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api';

export const GestionCursos = () => {
  const [cursos, setCursos] = useState([]);
  const [estructura, setEstructura] = useState([]); 
  const [departamentoId, setDepartamentoId] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);

  // Estado para saber si estamos editando un curso
  const [cursoEditandoId, setCursoEditandoId] = useState(null);

  const [form, setForm] = useState({
    titulo: '',
    descripcion: '',
    duracion: '',
    nivel: 'Básico',
    categoria: '',
    puesto_id: '',
    url_contenido: '',
    tipo_contenido: 'link'
  });

  useEffect(() => {
    obtenerCursos();
    obtenerEstructura();
  }, []);

  const obtenerEstructura = async () => {
    try {
      const res = await apiFetch('/api/admin/estructura');
      if (res.ok) {
        const data = await res.json();
        setEstructura(data);
      }
    } catch (error) {
      console.error('Error al cargar la estructura:', error);
    }
  };

  const obtenerCursos = async () => {
    try {
      const res = await apiFetch('/api/cursos');
      const data = await res.json();
      if (res.ok) setCursos(data.cursos || data || []);
    } catch (error) {
      console.error('Error al cargar cursos:', error);
    }
  };

  // Función para obtener el nombre del puesto a partir de su ID
  const obtenerNombrePuesto = (puestoId) => {
    if (!puestoId) return 'N/A';
    for (const dep of estructura) {
      const puesto = dep.puestos?.find((p) => String(p.id) === String(puestoId));
      if (puesto) return puesto.nombre;
    }
    return `Puesto #${puestoId}`;
  };

  // Encontrar qué departamento contiene determinado puesto
  const encontrarDepartamentoPorPuesto = (puestoId) => {
    for (const dep of estructura) {
      const puesto = dep.puestos?.find((p) => String(p.id) === String(puestoId));
      if (puesto) return String(dep.id);
    }
    return '';
  };

  // Puestos pertenecientes al departamento seleccionado
  const deptoSeleccionado = estructura.find((d) => String(d.id) === String(departamentoId));
  const puestosDisponibles = deptoSeleccionado ? deptoSeleccionado.puestos : [];

  const handleDepartamentoChange = (e) => {
    const depId = e.target.value;
    setDepartamentoId(depId);
    setForm({ ...form, puesto_id: '' }); 
  };

  // Cargar datos en el formulario para editar
  const handleCargarEdicion = (curso) => {
    setCursoEditandoId(curso.id);
    setForm({
      titulo: curso.titulo || '',
      descripcion: curso.descripcion || '',
      duracion: curso.duracion || '',
      nivel: curso.nivel || 'Básico',
      categoria: curso.categoria || '',
      puesto_id: String(curso.puesto_id || ''),
      url_contenido: curso.url_contenido || '',
      tipo_contenido: curso.tipo_contenido || 'link'
    });

    const depId = encontrarDepartamentoPorPuesto(curso.puesto_id);
    setDepartamentoId(depId);

    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const resetFormulario = () => {
    setForm({
      titulo: '',
      descripcion: '',
      duracion: '',
      nivel: 'Básico',
      categoria: '',
      puesto_id: '',
      url_contenido: '',
      tipo_contenido: 'link'
    });
    setDepartamentoId('');
    setCursoEditandoId(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.puesto_id) {
      alert('Por favor selecciona un puesto dirigido.');
      return;
    }
    setLoading(true);

    try {
      const payload = {
        titulo: form.titulo,
        descripcion: form.descripcion || '',
        duracion: form.duracion,
        nivel: form.nivel,
        categoria: form.categoria,
        puesto_id: String(form.puesto_id),
        url_contenido: form.url_contenido || 'https://ejemplo.com',
        tipo_contenido: form.tipo_contenido || 'link'
      };

      const ruta = cursoEditandoId
        ? `/api/cursos/${cursoEditandoId}`
        : '/api/cursos';
      
      const method = cursoEditandoId ? 'PUT' : 'POST';

      const res = await apiFetch(ruta, {
        method: method,
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        alert(cursoEditandoId ? '¡Curso actualizado con éxito!' : '¡Curso guardado con éxito!');
        resetFormulario();
        obtenerCursos();
      } else {
        const errorData = await res.json();
        alert(`Error al guardar: ${JSON.stringify(errorData.detail || 'Verifica los campos')}`);
      }
    } catch (error) {
      console.error('Error al guardar curso:', error);
      alert('No se pudo conectar con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  const handleEliminar = async (id) => {
    if (!window.confirm('¿Seguro que deseas eliminar este curso?')) return;
    try {
      const res = await apiFetch(`/api/cursos/${id}`, { method: 'DELETE' });
      if (res.ok) obtenerCursos();
    } catch (error) {
      console.error('Error al eliminar curso:', error);
    }
  };

  const cursosFiltrados = cursos.filter(
    (c) =>
      c.titulo?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.categoria?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 bg-slate-50 min-h-screen text-slate-800">
      <div className="max-w-6xl mx-auto space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Módulo RRHH: Gestión de Cursos</h1>
          <p className="text-slate-500 text-sm">Administra y asigna el catálogo de capacitación de tu empresa</p>
        </div>

        {/* Formulario */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${cursoEditandoId ? 'bg-amber-500' : 'bg-indigo-600'}`}></span>
            {cursoEditandoId ? 'Editar Curso' : 'Agregar Nuevo Curso'}
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Título del curso *</label>
                <input
                  name="titulo"
                  placeholder="Ej. APIs REST con FastAPI"
                  value={form.titulo}
                  onChange={(e) => setForm({ ...form, titulo: e.target.value })}
                  required
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">URL del material / vídeo</label>
                <input
                  name="url_contenido"
                  placeholder="https://..."
                  value={form.url_contenido}
                  onChange={(e) => setForm({ ...form, url_contenido: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Descripción</label>
              <textarea
                name="descripcion"
                placeholder="Breve resumen de los temas a tratar..."
                value={form.descripcion}
                onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Duración *</label>
                <input
                  name="duracion"
                  placeholder="Ej. 4h"
                  value={form.duracion}
                  onChange={(e) => setForm({ ...form, duracion: e.target.value })}
                  required
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Categoría *</label>
                <input
                  name="categoria"
                  placeholder="Ej. APIs, Analytics"
                  value={form.categoria}
                  onChange={(e) => setForm({ ...form, categoria: e.target.value })}
                  required
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Nivel</label>
                <select
                  name="nivel"
                  value={form.nivel}
                  onChange={(e) => setForm({ ...form, nivel: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                >
                  <option value="Básico">Básico</option>
                  <option value="Intermedio">Intermedio</option>
                  <option value="Avanzado">Avanzado</option>
                </select>
              </div>

              {/* Selector 1: Departamento */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Departamento</label>
                <select
                  value={departamentoId}
                  onChange={handleDepartamentoChange}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                >
                  <option value="">-- Departamento --</option>
                  {estructura.map((dep) => (
                    <option key={dep.id} value={dep.id}>
                      {dep.nombre}
                    </option>
                  ))}
                </select>
              </div>

              {/* Selector 2: Puesto Dirigido */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase mb-1">Puesto Dirigido *</label>
                <select
                  name="puesto_id"
                  value={form.puesto_id}
                  onChange={(e) => setForm({ ...form, puesto_id: e.target.value })}
                  disabled={!departamentoId}
                  required
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 disabled:opacity-50"
                >
                  <option value="">-- Selecciona Puesto --</option>
                  {puestosDisponibles.map((puesto) => (
                    <option key={puesto.id} value={puesto.id}>
                      {puesto.nombre}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="pt-2 flex justify-end gap-2">
              {cursoEditandoId && (
                <button
                  type="button"
                  onClick={resetFormulario}
                  className="bg-slate-200 hover:bg-slate-300 text-slate-700 px-4 py-2.5 rounded-xl font-medium text-sm transition-all"
                >
                  Cancelar
                </button>
              )}

              <button
                type="submit"
                disabled={loading}
                className={`${
                  cursoEditandoId ? 'bg-amber-600 hover:bg-amber-700' : 'bg-indigo-600 hover:bg-indigo-700'
                } text-white px-5 py-2.5 rounded-xl font-medium shadow-sm transition-all text-sm disabled:opacity-50`}
              >
                {loading
                  ? 'Guardando...'
                  : cursoEditandoId
                  ? 'Actualizar Curso'
                  : 'Guardar Curso'}
              </button>
            </div>
          </form>
        </div>

        {/* Tabla */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row gap-3 justify-between items-center">
            <h3 className="font-semibold text-slate-900 text-base">
              Catálogo de Cursos en Base de Datos ({cursos.length})
            </h3>
            <input
              type="text"
              placeholder="Buscar por título o categoría..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 w-full sm:w-64"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="p-4 pl-6">Título</th>
                  <th className="p-4">Puesto Dirigido</th>
                  <th className="p-4">Categoría</th>
                  <th className="p-4">Nivel</th>
                  <th className="p-4">Duración</th>
                  <th className="p-4 pr-6 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {cursosFiltrados.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center p-6 text-slate-400">
                      No hay cursos registrados o coincidentes con la búsqueda.
                    </td>
                  </tr>
                ) : (
                  cursosFiltrados.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="p-4 pl-6 font-medium text-slate-900">{c.titulo}</td>
                      <td className="p-4 text-slate-600 font-medium">
                        {obtenerNombrePuesto(c.puesto_id)}
                      </td>
                      <td className="p-4 text-slate-600">
                        <span className="px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium">
                          {c.categoria}
                        </span>
                      </td>
                      <td className="p-4 text-slate-600">{c.nivel}</td>
                      <td className="p-4 text-slate-600">{c.duracion}</td>
                      <td className="p-4 pr-6">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => handleCargarEdicion(c)}
                            className="px-2.5 py-1 bg-amber-50 text-amber-700 hover:bg-amber-100 rounded-lg text-xs font-semibold transition-colors"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => handleEliminar(c.id)}
                            className="px-2.5 py-1 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg text-xs font-semibold transition-colors"
                          >
                            Eliminar
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};