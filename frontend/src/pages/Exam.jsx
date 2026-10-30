import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api';

export const Exam = ({ examData, userName = "Empleado", userProfile = {}, onComplete }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);
  const [isGeneratingPath, setIsGeneratingPath] = useState(false);

  const [timeLeft, setTimeLeft] = useState(180);

  // 1. Normalización de preguntas
  const questionsList = Array.isArray(examData) 
    ? examData 
    : (examData?.preguntas || []);

  const totalQuestions = questionsList.length;
  const currentQuestion = questionsList[currentIndex];
  const progressPercentage = totalQuestions > 0 ? Math.round(((currentIndex + 1) / totalQuestions) * 100) : 0;

  // 2. Temporizador protegido
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
  }, [timeLeft, submitted, totalQuestions]);

  const handleSelectOption = (questionId, optionIndex) => {
    if (submitted) return;
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionIndex
    }));
  };

  const handleNext = () => {
    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  };

  const handleFinalize = async () => {
    if (submitted) return;
    setSubmitted(true);

    let aciertos = 0;
    questionsList.forEach((q) => {
      if (answers[q.id] === q.opcion_correcta) {
        aciertos += 1;
      }
    });

    const calculatedScore = totalQuestions > 0 ? Math.round((aciertos / totalQuestions) * 100) : 0;
    setScore(calculatedScore);

    // Guardar diagnóstico usando apiFetch
    try {
      await apiFetch('/api/diagnostico/guardar', {
        method: 'POST',
        body: JSON.stringify({
          usuario_id: userProfile?.id,
          puesto_id: userProfile?.puesto_id || userProfile?.position || 1,
          score: calculatedScore
        })
      });
    } catch (err) {
      console.error("Error guardando el diagnóstico:", err);
    }

    if (onComplete) {
      onComplete(calculatedScore);
    }
  };

  if (totalQuestions === 0) {
    return (
      <div className="p-8 bg-white rounded-2xl border border-slate-200 text-center space-y-3">
        <p className="text-slate-600 font-medium">No hay preguntas disponibles para este diagnóstico.</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
      {/* Encabezado con tiempo y progreso */}
      <div className="flex justify-between items-center pb-4 border-b border-slate-100">
        <div>
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Pregunta {currentIndex + 1} de {totalQuestions}
          </span>
          <div className="w-32 bg-slate-100 h-2 rounded-full mt-1 overflow-hidden">
            <div 
              className="bg-indigo-600 h-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
        </div>

        <div className="text-right">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tiempo Restante</span>
          <p className="text-sm font-bold text-slate-700">
            {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
          </p>
        </div>
      </div>

      {/* Cuerpo de la Pregunta */}
      {currentQuestion && (
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-slate-900">
            {currentQuestion.pregunta || currentQuestion.texto}
          </h3>

          <div className="space-y-2">
            {(currentQuestion.opciones || []).map((opcion, idx) => {
              const isSelected = answers[currentQuestion.id] === idx;
              return (
                <button
                  key={idx}
                  onClick={() => handleSelectOption(currentQuestion.id, idx)}
                  className={`w-full text-left p-4 rounded-xl border text-sm font-medium transition-all ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50 text-indigo-900 shadow-sm'
                      : 'border-slate-200 hover:border-slate-300 bg-white text-slate-700'
                  }`}
                >
                  {opcion}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Botones de Navegación */}
      <div className="flex justify-between items-center pt-4 border-t border-slate-100">
        <button
          onClick={handlePrev}
          disabled={currentIndex === 0}
          className="px-4 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Anterior
        </button>

        {currentIndex === totalQuestions - 1 ? (
          <button
            onClick={handleFinalize}
            disabled={submitted}
            className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
          >
            Finalizar Diagnóstico
          </button>
        ) : (
          <button
            onClick={handleNext}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
          >
            Siguiente
          </button>
        )}
      </div>
    </div>
  );
};