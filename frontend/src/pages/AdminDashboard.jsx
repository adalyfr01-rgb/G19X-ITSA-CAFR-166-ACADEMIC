import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, AreaChart, Area
} from 'recharts';
import { apiFetch } from '../api';

const COLORS = ['#10B981', '#F59E0B', '#4F46E5', '#EF4444', '#8B5CF6'];

export const AdminDashboard = () => {
  const [metricas, setMetricas] = useState(null);
  const [estructura, setEstructura] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    setCargando(true);
    setError(null);
    try {
      // Cargamos métricas y estructura usando apiFetch (inyecta el token automáticamente)
      const [resMetricas, resEstructura] = await Promise.all([
        apiFetch('/api/admin/metrics'),
        apiFetch('/api/admin/estructura')
      ]);

      if (!resMetricas.ok) {
        throw new Error(`Error en el servidor: ${resMetricas.status}`);
      }

      const dataMetricas = await resMetricas.json();
      setMetricas(dataMetricas);

      if (resEstructura.ok) {
        const dataEstructura = await resEstructura.json();
        setEstructura(dataEstructura);
      }
    } catch (err) {
      console.error('Error cargando métricas:', err);
      setError('No se pudieron obtener los datos de la base de datos.');
    } finally {
      setCargando(false);
    }
  };

  // Función para obtener el nombre del puesto
  const obtenerNombrePuesto = (puestoId) => {
    for (const dep of estructura) {
      const puesto = dep.puestos?.find((p) => String(p.id) === String(puestoId));
      if (puesto) return puesto.nombre;
    }
    return `Puesto #${puestoId}`;
  };

  if (cargando) {
    return (
      <div className="p-12 text-center text-slate-600">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent mb-3"></div>
        <p className="font-medium text-sm">Cargando métricas en tiempo real...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 bg-rose-50 border border-rose-200 rounded-2xl text-center space-y-3 max-w-xl mx-auto mt-6">
        <p className="text-rose-700 font-semibold">{error}</p>
        <button
          onClick={cargarDatos}
          className="px-4 py-2 bg-rose-600 text-white text-xs font-bold rounded-lg hover:bg-rose-700 transition-colors"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const kpis = metricas?.kpis || {};

  // 1. Mapeamos los departamentos basándonos en la ESTRUCTURA REAL:
  const datosDepartamento = estructura
    .filter((dep) => dep.nombre !== 'Recursos Humanos')
    .map((dep) => {
      const metricaDep = (metricas?.graficos?.por_departamento || []).find(
        (item) => String(item.departamento || item.departamento_id) === String(dep.id)
      );

      return {
        departamentoNombre: dep.nombre,
        promedio: metricaDep ? metricaDep.promedio : 0
      };
    });

  // 2. Mapeamos los nombres reales de los puestos
  const datosPuesto = (metricas?.graficos?.por_puesto || []).map((item) => ({
    ...item,
    puestoNombre: item.puesto_nombre || obtenerNombrePuesto(item.puesto || item.puesto_id)
  }));

  const datosEstatusCursos = metricas?.graficos?.estatus_cursos || [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Panel de Administración / RH</h1>

      {/* Tarjetas KPI */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Empleados</span>
          <p className="text-3xl font-extrabold text-slate-900 mt-2">{kpis.total_empleados ?? 0}</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Prom. Diagnóstico</span>
          <p className="text-3xl font-extrabold text-indigo-600 mt-2">{kpis.promedio_diagnostico ?? 0} pts</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Cursos Completados</span>
          <p className="text-3xl font-extrabold text-emerald-600 mt-2">{kpis.cursos_completados ?? 0}</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tasa de Aprobación</span>
          <p className="text-3xl font-extrabold text-amber-600 mt-2">{kpis.tasa_aprobacion ?? 0}%</p>
        </div>
      </div>

      {/* Gráficos Recharts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Promedio por Departamento */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Promedio Diagnóstico por Departamento</h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={datosDepartamento}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="departamentoNombre" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => [`${value} pts`, 'Promedio']} />
                <Bar dataKey="promedio" fill="#4F46E5" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Estatus Cursos */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Estatus Global de Cursos</h2>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={datosEstatusCursos}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {datosEstatusCursos.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [value, 'Cursos']} />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Empleados por Puesto */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Empleados por Puesto</h2>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart 
                layout="vertical" 
                data={datosPuesto}
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals={false} />
                <YAxis dataKey="puestoNombre" type="category" width={180} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(value) => [value, 'Cantidad']} />
                <Bar dataKey="cantidad" fill="#8B5CF6" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Evolución del Aprendizaje */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-lg font-bold text-slate-900">Evolución del Aprendizaje en el Tiempo</h2>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metricas?.graficos?.evolucion_aprendizaje || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="mes" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip formatter={(val) => [val, 'Interacciones xAPI']} />
                <Area type="monotone" dataKey="actividades" stroke="#10B981" fill="#D1FAE5" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};