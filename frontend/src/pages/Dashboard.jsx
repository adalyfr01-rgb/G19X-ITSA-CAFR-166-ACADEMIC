import React, { useState, useEffect, useRef } from 'react';
import { ModalExamen } from './ModalExamen';

export const Dashboard = ({ userProfile, score, setScore, onLogout }) => {
  const [cursosIA, setCursosIA] = useState([]);
  const [cursosCompletados, setCursosCompletados] = useState({});
  const [cargando, setCargando] = useState(true);
  const [errorIA, setErrorIA] = useState(null);

  // Estados para el Modal de Examen e Historial desde BD
  const [mostrarExamen, setMostrarExamen] = useState(false);
  const [datosExamen, setDatosExamen] = useState(null);
  const [intentosRestantes, setIntentosRestantes] = useState(3);
  const [resultadoExamen, setResultadoExamen] = useState(null);
  const [perfilDetalle, setPerfilDetalle] = useState(null);

  const solicitudEjecutada = useRef(false);

  useEffect(() => {
    if (solicitudEjecutada.current) return;
    solicitudEjecutada.current = true;

    cargarRutaEHistorial();
  }, [userProfile]);

  // Carga la ruta de aprendizaje y consulta la BD sobre el estado del examen del usuario
  const cargarRutaEHistorial = async () => {
    if (!userProfile?.id) {
      setCargando(false);
      return;
    }

    setCargando(true);
    setErrorIA(null);

    const usuarioId = userProfile.id;
    // Cargar puesto y departamento con sus nombres reales desde la BD
    try {
      const resPerfil = await fetch(`http://localhost:8000/api/usuarios/perfil/${usuarioId}`);
      if (resPerfil.ok) {
        const dataPerfil = await resPerfil.json();
        setPerfilDetalle(dataPerfil);
      }
    } catch (e) {
      console.warn("No se pudo cargar el detalle del perfil:", e);
    }

    try {
      // 1. Obtener la ruta de cursos del usuario
      let listaCursosFinal = [];
      const resGuardada = await fetch(`http://localhost:8000/api/rutas/usuario/${usuarioId}`);
      if (resGuardada.ok) {
        const dataGuardada = await resGuardada.json();
        let listaGuardada = dataGuardada.ruta || dataGuardada.recomendaciones || dataGuardada.cursos || dataGuardada;

        if (listaGuardada && typeof listaGuardada === 'object' && !Array.isArray(listaGuardada)) {
          listaGuardada = listaGuardada.cursos || listaGuardada.ruta || [];
        }

        if (Array.isArray(listaGuardada) && listaGuardada.length > 0) {
          listaCursosFinal = listaGuardada;
        }
      }

      if (listaCursosFinal.length === 0) {
        const resIA = await fetch('http://localhost:8000/api/rutas/generar-ia', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ usuario_id: usuarioId })
        });

        if (resIA.ok) {
          const dataIA = await resIA.json();
          let listaIA = dataIA.ruta || dataIA.recomendaciones || dataIA.cursos || dataIA;

          if (listaIA && typeof listaIA === 'object' && !Array.isArray(listaIA)) {
            listaIA = listaIA.cursos || listaIA.ruta || [];
          }

          if (Array.isArray(listaIA)) {
            listaCursosFinal = listaIA;
          }
        }
      }

      setCursosIA(listaCursosFinal);

      // 2. Cargar estado del progreso de cursos
      try {
        const resProgreso = await fetch(`http://localhost:8000/api/progreso/usuario/${usuarioId}`);
        if (resProgreso.ok) {
          const dataProgreso = await resProgreso.json();
          const listaProgreso = Array.isArray(dataProgreso)
            ? dataProgreso
            : (dataProgreso.progresos || dataProgreso.progreso || []);

          const mapaCompletados = {};
          if (Array.isArray(listaProgreso)) {
            listaProgreso.forEach((p) => {
              const estatus = String(p.estatus || p.status || p.estado || '').toLowerCase();
              const idReg = p.id_curso || p.curso_id || p.id;
              const esCompletado = estatus === 'completado' || estatus === 'completed' || p.completado === true;

              if (idReg && esCompletado) {
                mapaCompletados[idReg] = true;
                mapaCompletados[String(idReg)] = true;
                mapaCompletados[Number(idReg)] = true;
              }
            });
          }
          setCursosCompletados(mapaCompletados);
        }
      } catch (e) {
        console.warn('No se pudo obtener progreso previo:', e);
      }

      // 3. Consultar a la BD el último resultado de evaluación del usuario para RH
      try {
        const resExamen = await fetch(`http://localhost:8000/api/evaluaciones/ultimo/${usuarioId}`);
        if (resExamen.ok) {
          const dataExamenBD = await resExamen.json();
          if (dataExamenBD && dataExamenBD.id) {
            setResultadoExamen({
              puntaje: dataExamenBD.puntaje,
              aciertos: dataExamenBD.aciertos,
              totalPreguntas: dataExamenBD.total_preguntas,
              aprobado: dataExamenBD.aprobado
            });
            if (dataExamenBD.intentos_restantes !== undefined) {
              setIntentosRestantes(dataExamenBD.intentos_restantes);
            }
          }
        }
      } catch (e) {
        console.warn('No se encontró historial previo de examen en BD:', e);
      }

      // 4. Cargar Puntaje Diagnóstico si hace falta
      if (!score || score === 0) {
        const resDiag = await fetch(`http://localhost:8000/api/diagnostico/ultimo/${usuarioId}`);
        if (resDiag.ok) {
          const dataDiag = await resDiag.json();
          if (dataDiag && Number(dataDiag.puntaje) > 0 && typeof setScore === 'function') {
            setScore(Number(dataDiag.puntaje));
          }
        }
      }

    } catch (err) {
      console.error('Error al conectar con el servidor backend:', err);
      setErrorIA('Error al cargar la información.');
    } finally {
      setCargando(false);
    }
  };


  const obtenerLinkCurso = (curso) => {
    if (!curso) return null;
    if (typeof curso === 'string' && curso.startsWith('http')) return curso;
    if (typeof curso === 'object') {
      const urlDirecta = curso.url_contenido || curso.link || curso.url || curso.enlace;
      if (urlDirecta && String(urlDirecta).trim() !== '' && String(urlDirecta) !== 'null') {
        return String(urlDirecta).trim();
      }
    }
    return null;
  };

  // Función con integración xAPI completa
  const registrarProgresoXAPI = async (idCurso, accion) => {
    if (!idCurso) return;
    try {
      // 1. Actualizar en el endpoint de progreso local
      const res = await fetch('http://localhost:8000/api/progreso/actualizar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id_usuario: userProfile?.id,
          id_curso: idCurso,
          accion: accion
        })
      });

      if (res.ok && accion === 'completed') {
        setCursosCompletados((prev) => ({
          ...prev,
          [idCurso]: true,
          [String(idCurso)]: true,
          [Number(idCurso)]: true
        }));
      }

      // 2. Enviar evento xAPI al LRS / Backend xAPI
      await fetch('http://localhost:8000/api/xapi/statements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          usuario_id: userProfile?.id,
          verb: accion === 'completed' ? 'completed' : 'launched',
          object_id: `curso-${idCurso}`,
          statement_json: {
            curso_id: idCurso,
            accion: accion
          }
        })
      });
      console.log(`✅ Evento xAPI (${accion}) registrado para el curso ${idCurso}`);

    } catch (err) {
      console.error('Error al actualizar xAPI en curso:', err);
    }
  };

  const handleIrACursoDirecto = (curso, link) => {
    if (!link) return;
    const urlFinal = link.startsWith('http://') || link.startsWith('https://') ? link : `https://${link}`;
    window.open(urlFinal, '_blank', 'noopener,noreferrer');

    const idCurso = typeof curso === 'object' ? (curso.id_curso || curso.id) : null;
    if (idCurso) registrarProgresoXAPI(idCurso, 'launched');
  };

  const handleCompletarCurso = (curso) => {
    const idCurso = typeof curso === 'object' ? (curso.id_curso || curso.id) : null;
    if (idCurso) registrarProgresoXAPI(idCurso, 'completed');
  };

  // Validar si completó el 100% de los cursos
  const todosCompletados = cursosIA.length > 0 && cursosIA.every((curso, idx) => {
    const idCurso = typeof curso === 'object' && curso !== null 
      ? (curso.id_curso || curso.id || idx + 1)
      : (idx + 1);
    return Boolean(cursosCompletados[idCurso] || cursosCompletados[String(idCurso)]);
  });

  const abrirExamen = async () => {
    if (!userProfile?.id) return;

    try {
      setCargando(true);
      const res = await fetch('http://localhost:8000/api/evaluaciones/generar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          usuario_id: userProfile.id,
          cursos: cursosIA
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.evaluacion && data.evaluacion.preguntas) {
          setDatosExamen(data.evaluacion);
          setMostrarExamen(true);
        } else {
          alert("Error: La evaluación generada no tiene un formato válido.");
        }
      } else {
        alert("No se pudo generar la evaluación.");
      }
    } catch (err) {
      console.error("Error al conectar con la API de evaluaciones:", err);
    } finally {
      setCargando(false);
    }
  };

  // Guardar el examen directamente en la BD
  const manejarFinalizacion = async (resultado) => {
    setMostrarExamen(false);
    setResultadoExamen(resultado);

    const nuevosIntentos = resultado.aprobado ? intentosRestantes : Math.max(0, intentosRestantes - 1);
    setIntentosRestantes(nuevosIntentos);

    // Enviar el resultado al Backend para guardarlo en la tabla 'evaluaciones_resultados'
    try {
      await fetch('http://localhost:8000/api/evaluaciones/guardar-resultado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          usuario_id: userProfile.id,
          puntaje: resultado.puntaje,
          aciertos: resultado.aciertos,
          total_preguntas: resultado.totalPreguntas,
          aprobado: resultado.aprobado,
          intentos_restantes: nuevosIntentos
        })
      });
      console.log("✅ Resultado guardado en la Base de Datos para el área de RH.");
    } catch (error) {
      console.error("❌ Error al guardar el resultado en la BD:", error);
    }
  };
console.log("Perfil recibido en Dashboard:", userProfile);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Información del Perfil */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            ¡Hola, {perfilDetalle?.nombre || userProfile?.name || userProfile?.nombre || 'Empleado'}!
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Puesto: <strong className="text-slate-700">{perfilDetalle?.puesto_nombre || userProfile?.position || 'General'}</strong> | 
            Departamento: <strong className="text-slate-700">{perfilDetalle?.departamento_nombre || userProfile?.department || 'General'}</strong>
          </p>
        </div>

        <div className="bg-indigo-50 border border-indigo-100 p-4 rounded-xl text-center min-w-[160px]">
          <span className="text-xs uppercase font-semibold text-indigo-600 tracking-wider">Resultado Diagnóstico</span>
          <div className="text-3xl font-extrabold text-indigo-700 mt-1">{score || 0} pts</div>
        </div>
      </div>

      {/* Cursos Recomendados */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-600"></span>
            </span>
            Plan de Capacitación Personalizado
          </h2>
          <p className="text-slate-500 text-sm">
            Cursos asignados según tu nivel y diagnóstico inicial
          </p>
        </div>

        {cargando ? (
          <div className="bg-white p-12 text-center rounded-2xl border border-slate-200 space-y-3">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-600 border-t-transparent"></div>
            <p className="text-slate-600 font-medium text-sm">Sincronizando información...</p>
          </div>
        ) : errorIA ? (
          <div className="bg-rose-50 border border-rose-200 p-8 rounded-2xl text-center space-y-3">
            <p className="text-rose-700 font-semibold text-base">{errorIA}</p>
            <button 
              onClick={cargarRutaEHistorial}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-lg transition-colors"
            >
              Reintentar
            </button>
          </div>
        ) : cursosIA.length === 0 ? (
          <div className="bg-white p-8 text-center rounded-2xl border border-slate-200 text-slate-500">
            No se encontraron cursos en tu plan.
          </div>
        ) : (
          <>
            {console.log("🔍 ESTRUCTURA DE CURSOS IA:", cursosIA)}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {cursosIA.map((curso, idx) => {
                const esObjeto = typeof curso === 'object' && curso !== null;
                const idCurso = esObjeto ? (curso.id_curso || curso.id || idx + 1) : (idx + 1);
                const titulo = esObjeto ? (curso.nombre || curso.titulo || curso.title) : String(curso);
                const categoria = esObjeto ? (curso.categoria || curso.category || 'Capacitación') : 'Recomendado';
                const duracion = esObjeto ? (curso.duracion || curso.duration || 'Flexible') : 'Flexible';
                
                // ✅ Mapeo de justificación desde BD y eliminación de valor estático por defecto
                const descripcion = esObjeto ? (
                  curso.justificacion || curso.descripcion || curso.description || curso.desc || ''
                ) : '';

                const nivel = esObjeto ? (curso.nivel || curso.level || 'General') : 'General';
                const linkUrl = obtenerLinkCurso(curso);
                const tieneLink = Boolean(linkUrl && String(linkUrl).trim() !== '');
                const estaCompletado = Boolean(
                  cursosCompletados[idCurso] || 
                  cursosCompletados[String(idCurso)] || 
                  cursosCompletados[Number(idCurso)]
                );

                return (
                  <div 
                    key={idCurso || idx} 
                    className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between h-full"
                  >
                    <div className="space-y-3">
                      <div className="flex justify-between items-center text-xs">
                        <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 rounded-lg font-semibold">
                          {categoria}
                        </span>
                        <span className="text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded-md">
                          ⏱️ {duracion}
                        </span>
                      </div>

                      <h3 className="font-bold text-slate-900 text-base leading-snug">
                        {titulo}
                      </h3>

                      {/* ✅ Renderizado condicional de la descripción/justificación */}
                      {descripcion && (
                        <p className="text-slate-600 text-xs leading-relaxed border-t border-slate-100 pt-2 mt-2 line-clamp-3">
                          {descripcion}
                        </p>
                      )}
                    </div>

                    <div className="pt-4 mt-4 border-t border-slate-100 flex flex-col gap-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-400">Nivel: <strong className="text-slate-600">{nivel}</strong></span>
                        
                        {tieneLink ? (
                          <button
                            type="button"
                            onClick={() => handleIrACursoDirecto(curso, linkUrl)}
                            className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition-all shadow-sm flex items-center gap-1.5 cursor-pointer active:scale-95"
                          >
                            <span>Ir a curso</span>
                            <span className="text-sm">↗</span>
                          </button>
                        ) : (
                          <span className="px-3 py-1.5 bg-slate-100 border border-slate-200 text-slate-400 text-xs font-medium rounded-xl flex items-center gap-1 select-none">
                            <span className="text-xs">🔒</span> Sin enlace
                          </span>
                        )}
                      </div>

                      {estaCompletado ? (
                        <div className="w-full py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-bold rounded-xl text-center flex items-center justify-center gap-1">
                          <span>✓</span> Completado
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleCompletarCurso(curso)}
                          className="w-full py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition-all cursor-pointer border border-slate-200"
                        >
                          Marcar como completado
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Módulo de Evaluación Final */}
            <div className="mt-8 text-center bg-slate-50 p-6 rounded-2xl border border-slate-200">
              <h3 className="text-lg font-bold text-slate-800 mb-2">Evaluación Final de la Ruta</h3>
              
              <p className="text-xs text-slate-500 mb-4">
                {resultadoExamen?.aprobado
                  ? "¡Has aprobado la evaluación! Tu resultado ya está registrado para RH."
                  : intentosRestantes === 0
                    ? "Has agotado tus 3 intentos permitidos para esta evaluación."
                    : !todosCompletados
                      ? "Completa todos los cursos asignados para desbloquear la evaluación final."
                      : `Tienes ${intentosRestantes} intento(s) disponible(s).`}
              </p>

              <button
                disabled={!todosCompletados || intentosRestantes === 0 || resultadoExamen?.aprobado}
                onClick={abrirExamen}
                className="px-6 py-3 rounded-xl font-bold text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed shadow-md transition-all cursor-pointer"
              >
                {resultadoExamen?.aprobado
                  ? "🎉 Evaluación Aprobada"
                  : intentosRestantes === 0
                    ? "🚫 Sin Intentos Restantes"
                    : "📝 Rendir Evaluación Final"}
              </button>

              {/* Registro de Calificación Visible */}
              {resultadoExamen && (
                <div className={`mt-4 p-4 rounded-xl border text-center ${
                  resultadoExamen.aprobado 
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800' 
                    : 'bg-rose-50 border-rose-200 text-rose-800'
                }`}>
                  <h4 className="font-bold text-base">
                    {resultadoExamen.aprobado ? '🎉 ¡Evaluación Aprobada!' : '❌ Evaluación No Aprobada'}
                  </h4>
                  <p className="text-sm mt-1">
                    Puntaje: <strong>{resultadoExamen.puntaje} pts</strong> | 
                    Aciertos: <strong>{resultadoExamen.aciertos} / {resultadoExamen.totalPreguntas}</strong>
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Renderizado del Modal de Examen pasándole la prop usuarioId */}
      {mostrarExamen && (
        <ModalExamen
          examenData={datosExamen}
          intentosRestantes={intentosRestantes}
          onClose={() => setMostrarExamen(false)}
          FinalizarExamen={manejarFinalizacion}
          usuarioId={userProfile?.id}
        />
      )}
    </div>
  );
};