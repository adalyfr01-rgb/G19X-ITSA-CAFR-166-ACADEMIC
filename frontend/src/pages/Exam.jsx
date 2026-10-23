import React, { useState, useEffect } from 'react';

export const Exam = ({ examData, userName = "Empleado", userProfile = {}, onComplete }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [isGeneratingPath, setIsGeneratingPath] = useState(false);

  const [timeLeft, setTimeLeft] = useState(180);

  // 1. Normalización de preguntas: detecta si viene un arreglo directo [...] o un objeto { preguntas: [...] }
  const questionsList = Array.isArray(examData) 
    ? examData 
    : (examData?.preguntas || []);

  const totalQuestions = questionsList.length;
  const currentQuestion = questionsList[currentIndex];
  const progressPercentage = totalQuestions > 0 ? Math.round(((currentIndex + 1) / totalQuestions) * 100) : 0;

  // 2. Temporizador protegido: SOLO se dispara al agotarse el tiempo SI ya existen preguntas cargadas
  useEffect(() => {
    if (submitted) return;

    if (timeLeft <= 0) {
      if (totalQuestions > 0) {
        handleFinalize();
      }
      return;
    }

    const timer = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    return () => clearInterval(timer);
  }, [timeLeft, submitted]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSelectOption = (optionIndex) => {
    if (!currentQuestion) return;
    setAnswers({
      ...answers,
      [currentQuestion.id]: optionIndex,
    });
  };

  const handleNext = () => {
    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      handleFinalize();
    }
  };

   const handleFinalize = async () => {
    if (submitted || totalQuestions === 0) return;

    setIsGeneratingPath(true);

    const activeUserId = userProfile?.id || 3;
    const puestoRaw = userProfile?.puesto_id || userProfile?.position || userProfile?.puesto || 'Gerente de Ventas / Business';

    // 1. Formatear las respuestas según el esquema EvaluarDiagnosticoRequest del backend
    const respuestasFormateadas = questionsList.map((q, idx) => ({
      pregunta_id: q.id,
      opcion_seleccionada: answers[q.id] !== undefined ? Number(answers[q.id]) : Number(answers[idx])
    }));

    try {
      // 2. Enviar a tu endpoint backend para que PostgreSQL evalúe el score real
      const resEval = await fetch('http://localhost:8000/api/evaluaciones/diagnostico/evaluar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          usuario_id: activeUserId,
          puesto_id: puestoRaw,
          respuestas: respuestasFormateadas
        }),
      });

      if (resEval.ok) {
        const dataEval = await resEval.json();
        console.log('✅ EVALUACIÓN DEL BACKEND EXITOSA:', dataEval);
        
        // Asignar el score real que calculó la Base de Datos (ej. 80%)
        setScore(dataEval.score);
        setSubmitted(true);

        // 3. Generar la ruta adaptativa con IA con el score correcto
        const resIA = await fetch('http://localhost:8000/api/rutas/generar-ia', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            puesto_id: puestoRaw,
            usuario_id: activeUserId,
            respuestas: answers,
          }),
        });

        if (resIA.ok) {
          const dataIA = await resIA.json();
          console.log('🤖 Ruta de IA generada:', dataIA);
        }
      } else {
        console.error('Error al evaluar en backend:', await resEval.text());
      }

    } catch (err) {
      console.error('❌ Error procesando el diagnóstico:', err);
    } finally {
      setIsGeneratingPath(false);
    }
  };

  const initialLetter = userName ? userName.charAt(0).toUpperCase() : 'U';

  // Si no hay preguntas listas en pantalla y aún no finaliza, muestra estado de carga
  if (!currentQuestion && !submitted) {
    return (
      <div className="min-h-screen w-full bg-slate-200 flex items-center justify-center p-6">
        <div className="bg-white p-8 rounded-xl shadow-lg text-center max-w-md">
          <h3 className="text-lg font-bold text-slate-800 mb-2">Cargando evaluación...</h3>
          <p className="text-xs text-slate-500">
            Obteniendo las preguntas diagnósticas configuradas por el administrador para tu puesto.
          </p>
        </div>
      </div>
    );
  }

  // Atributos de pregunta flexibles (soporta .texto o .pregunta)
  const textoPregunta = currentQuestion?.texto || currentQuestion?.pregunta || "Sin enunciado";
  const opcionesPregunta = currentQuestion?.opciones || [];

  return (
    <div className="min-h-screen w-full bg-slate-200 flex items-center justify-center p-6">
      <div className="w-full max-w-4xl bg-white rounded-lg shadow-2xl overflow-hidden flex flex-col min-h-[560px] relative border border-slate-100">
        
        {/* Franja Azul Superior con Logo y Nombre */}
        <div className="w-full bg-[#0E1E38] h-28 flex items-center justify-between px-8 z-20 relative">
          <div className="flex flex-col gap-2">
            <div className="bg-white px-4 py-2 rounded shadow-md flex items-center justify-center w-fit">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full border-4 border-slate-800 flex items-center justify-center font-bold text-slate-800 text-sm">
                  O
                </div>
                <div className="flex flex-col">
                  <span className="text-base font-bold text-slate-800 tracking-tight leading-none">pluriOne</span>
                  <span className="text-[6px] text-slate-400 tracking-widest uppercase">financial services</span>
                </div>
              </div>
            </div>

            {/* User Avatar & Name */}
            <div className="flex items-center gap-2 text-white">
              <div className="w-7 h-7 rounded-full bg-white text-slate-900 flex items-center justify-center font-extrabold text-xs shadow">
                {initialLetter}
              </div>
              <span className="text-xs font-semibold italic tracking-wide">
                {userName}
              </span>
            </div>
          </div>

          {/* Reloj */}
          {!submitted && (
            <div className="bg-slate-900/80 border border-slate-700 px-3 py-1.5 rounded-lg text-right">
              <span className="text-[10px] text-slate-400 block uppercase">Tiempo restante</span>
              <span className={`text-sm font-mono font-bold ${timeLeft < 120 ? 'text-red-400 animate-pulse' : 'text-emerald-400'}`}>
                {formatTime(timeLeft)}
              </span>
            </div>
          )}
        </div>

        {/* Cuerpo */}
        <div className="flex-1 flex relative">
          <div className="w-full lg:w-3/4 p-8 sm:p-10 z-10 flex flex-col justify-between bg-white">
            
            {!submitted ? (
              <div className="space-y-6">
                {/* Barra de Progreso */}
                <div className="space-y-1 max-w-lg">
                  <div className="flex justify-between items-center text-xs font-extrabold italic text-slate-900">
                    <span>Pregunta {currentIndex + 1} de {totalQuestions}</span>
                    <span className="text-blue-900">{progressPercentage}%</span>
                  </div>
                  <div className="w-full bg-blue-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-[#0E1E38] h-full transition-all duration-300"
                      style={{ width: `${progressPercentage}%` }}
                    ></div>
                  </div>
                </div>

                {/* Tarjeta de Pregunta */}
                <div className="border-2 border-slate-800 rounded-2xl p-6 sm:p-8 bg-white shadow-lg space-y-6 max-w-2xl">
                  <h2 className="text-lg sm:text-xl font-extrabold italic text-slate-900 text-center leading-snug">
                    {textoPregunta}
                  </h2>

                  {/* Opciones */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                    {opcionesPregunta.map((op, opIdx) => {
                      const isSelected = answers[currentQuestion.id] === opIdx;
                      return (
                        <button
                          key={opIdx}
                          type="button"
                          onClick={() => handleSelectOption(opIdx)}
                          className={`p-3 rounded-xl border-2 text-xs font-bold transition-all text-center flex items-center justify-center min-h-[52px] ${
                            isSelected
                              ? 'border-[#0E1E38] bg-[#0E1E38] text-white shadow-md scale-[1.02]'
                              : 'border-slate-800 bg-white text-slate-900 hover:bg-slate-50'
                          }`}
                        >
                          {op}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Botón Siguiente */}
                <div className="flex justify-end max-w-2xl pt-2">
                  <button
                    type="button"
                    onClick={handleNext}
                    disabled={answers[currentQuestion.id] === undefined}
                    className="bg-[#0A1326] text-white py-2.5 px-8 rounded-lg text-xs font-extrabold hover:bg-slate-800 transition-colors shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {currentIndex < totalQuestions - 1 ? 'Siguiente' : 'Finalizar'}
                  </button>
                </div>
              </div>
            ) : (
              /* Pantalla de Resultados */
              <div className="text-center space-y-4 py-8 my-auto">
                <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto text-2xl font-black shadow-inner ${
                  score >= 70 ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                }`}>
                  {score}%
                </div>
                <h2 className="text-2xl font-extrabold italic text-slate-900">
                  Diagnóstico Finalizado
                </h2>
                <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                  Tus respuestas se han guardado exitosamente. Con este resultado configuraremos tu ruta de aprendizaje personalizada.
                </p>

                <button
                  onClick={() => onComplete(score)}
                  disabled={isGeneratingPath}
                  className="mt-4 bg-[#0A1326] text-white py-2.5 px-6 rounded-lg text-xs font-bold hover:bg-slate-800 transition-colors shadow-md disabled:opacity-50"
                >
                  {isGeneratingPath ? 'Diseñando ruta con IA...' : 'Ver mi Plan de Desarrollo Personalizado'}
                </button>
              </div>
            )}

          </div>

          {/* Diagonal Visual Corporativa */}
          <div 
            className="hidden lg:block absolute -top-28 right-0 w-2/5 h-[calc(100%+7rem)] bg-[#0E1E38]"
            style={{ clipPath: 'polygon(45% 0, 100% 0, 100% 100%, 0% 100%)' }}
          >
            <div 
              className="w-full h-full bg-[#050B17] opacity-40"
              style={{ clipPath: 'polygon(60% 0, 100% 0, 100% 100%, 25% 100%)' }}
            ></div>
          </div>
        </div>

      </div>
    </div>
  );
};