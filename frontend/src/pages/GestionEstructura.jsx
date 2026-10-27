import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api';

export const GestionEstructura = () => {
  const [estructura, setEstructura] = useState([]);
  const [cargando, setCargando] = useState(true);
  
  // Estados para nuevo departamento
  const [nombreDepto, setNombreDepto] = useState('');
  const [descDepto, setDescDepto] = useState('');

  // Estados para nuevo puesto
  const [deptoSeleccionado, setDeptoSeleccionado] = useState('');
  const [nombrePuesto, setNombrePuesto] = useState('');

  // Mensajes de estado
  const [mensaje, setMensaje] = useState({ tipo: '', texto: '' });

  useEffect(() => {
    cargarEstructura();
  }, []);

  const cargarEstructura = async () => {
    try {
      const res = await apiFetch('/api/admin/estructura');
      if (res.ok) {
        const data = await res.json();
        setEstructura(data);
      }
    } catch (err) {
      console.error('Error al cargar la estructura:', err);
    } finally {
      setCargando(false);
    }
  };

  // 1. Crear Departamento
  const handleCrearDepartamento = async (e) => {
    e.preventDefault();
    if (!nombreDepto.trim()) return;

    try {
      const res = await apiFetch('/api/admin/departamentos', {
        method: 'POST',
        body: JSON.stringify({ nombre: nombreDepto, descripcion: descDepto })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error al crear departamento');

      setMensaje({ tipo: 'exito', texto: `Departamento "${nombreDepto}" creado exitosamente.` });
      setNombreDepto('');
      setDescDepto('');
      cargarEstructura();
    } catch (err) {
      setMensaje({ tipo: 'error', texto: err.message });
    }
  };

  // 2. Agregar Puesto a un Departamento
  const handleAgregarPuesto = async (e) => {
    e.preventDefault();
    if (!deptoSeleccionado || !nombrePuesto.trim()) return;

    try {
      const res = await apiFetch(`/api/admin/departamentos/${deptoSeleccionado}/puestos`, {
        method: 'POST',
        body: JSON.stringify({ nombre: nombrePuesto })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error al agregar puesto');

      setMensaje({ tipo: 'exito', texto: `Puesto "${nombrePuesto}" agregado correctamente.` });
      setNombrePuesto('');
      cargarEstructura();
    } catch (err) {
      setMensaje({ tipo: 'error', texto: err.message });
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      <h1 className="text-2xl font-bold text-slate-900">Gestión de Estructura Organizacional</h1>

      {/* Alerta de feedback */}
      {mensaje.texto && (
        <div className={`p-4 rounded-xl text-sm font-medium ${
          mensaje.tipo === 'exito' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'
        }`}>
          {mensaje.texto}
        </div>
      )}

      {/* Grid de Formulario */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Formulario 1: Crear Departamento */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Nuevo Departamento</h2>
          <form onSubmit={handleCrearDepartamento} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Nombre del Departamento</label>
              <input
                type="text"
                value={nombreDepto}
                onChange={(e) => setNombreDepto(e.target.value)}
                placeholder="ej. Marketing, Finanzas..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Descripción (Opcional)</label>
              <textarea
                value={descDepto}
                onChange={(e) => setDescDepto(e.target.value)}
                placeholder="Breve descripción del departamento"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                rows={2}
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 bg-indigo-600 text-white font-semibold text-sm rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Crear Departamento
            </button>
          </form>
        </div>

        {/* Formulario 2: Agregar Puesto */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Agregar Puesto</h2>
          <form onSubmit={handleAgregarPuesto} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Seleccionar Departamento</label>
              <select
                value={deptoSeleccionado}
                onChange={(e) => setDeptoSeleccionado(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="">-- Selecciona un departamento --</option>
                {estructura.map((d) => (
                  <option key={d.id} value={d.id}>{d.nombre}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Nombre del Puesto</label>
              <input
                type="text"
                value={nombrePuesto}
                onChange={(e) => setNombrePuesto(e.target.value)}
                placeholder="ej. Diseñador UI/UX, Contador..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 bg-emerald-600 text-white font-semibold text-sm rounded-lg hover:bg-emerald-700 transition-colors"
            >
              Agregar Puesto
            </button>
          </form>
        </div>

      </div>

      {/* Vista previa de la Estructura Organizacional */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Estructura Actual</h2>
        {cargando ? (
          <p className="text-sm text-slate-500">Cargando estructura...</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {estructura.map((depto) => (
              <div key={depto.id} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <h3 className="font-bold text-slate-800">{depto.nombre}</h3>
                {depto.descripcion && <p className="text-xs text-slate-500">{depto.descripcion}</p>}
                <div className="pt-2 border-t border-slate-200">
                  <span className="text-xs font-semibold text-slate-400 uppercase">Puestos:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {depto.puestos.length > 0 ? (
                      depto.puestos.map((p) => (
                        <span key={p.id} className="text-xs bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-md font-medium">
                          {p.nombre}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-400 italic">Sin puestos registrados</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};