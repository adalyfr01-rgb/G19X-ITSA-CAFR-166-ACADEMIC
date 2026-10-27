import React, { useState, useEffect } from 'react';
import Login from './pages/Login';
import { Exam } from './pages/Exam';
import { Dashboard } from './pages/Dashboard';
import { PanelRRHH } from './pages/PanelRRHH';

export default function App() {
  const [step, setStep] = useState(1); 
  const [currentUser, setCurrentUser] = useState(null); 
  const [userProfile, setUserProfile] = useState(null);
  const [examData, setExamData] = useState(null);
  const [finalScore, setFinalScore] = useState(0);

  // Restaurar sesión automáticamente al dar F5
  useEffect(() => {
    const savedUser = localStorage.getItem('pluriUser');
    if (savedUser) {
      try {
        const user = JSON.parse(savedUser);
        handleLogin(user);
      } catch (err) {
        console.error('Error restaurando sesión:', err);
      }
    }
  }, []);

  const handleLogin = async (user) => {
    console.log("DATOS DEL USUARIO LOGUEADO:", user);
    setCurrentUser(user);
    localStorage.setItem('pluriUser', JSON.stringify(user));

  if (user?.access_token){
    localStorage.setItem('token', user.access_token);
  }

   if (user?.rol === 'rh' || user?.rol === 'rrhh' || user?.rol === 'admin') {
     setStep(5);
     return;
    }

    const userId = user?.id;
    const puestoMapeado = String(user?.puesto || user?.puesto_id || 'recruiter');
    const deptoMapeado = String(user?.departamento || 'Marketing');

    const perfilActualizado = {
      id: userId,
      name: user.nombre || user.email,
      position: puestoMapeado,
      puesto_id: puestoMapeado,
      department: deptoMapeado
    };

    setUserProfile(perfilActualizado);

    try {
      // 1. Consultar el último diagnóstico completado en la BD
      const resDiag = await fetch(`http://localhost:8000/api/diagnostico/ultimo/${userId}`);
      
      if (resDiag.ok) {
        const dataDiag = await resDiag.json();
        const puntajeObtenido = Number(dataDiag?.score || dataDiag?.puntaje || 0);

        // Si el usuario ya completó un examen previamente con score > 0, va al Dashboard
        if (puntajeObtenido > 0) {
          setFinalScore(puntajeObtenido);
          setStep(4); // Dashboard
          return;
        }
      }

      // 2. Si no tiene examen previo, pedimos las preguntas guardadas por RH en BD
      const resExam = await fetch(`http://localhost:8000/api/evaluaciones/diagnostico/${puestoMapeado}`);

      if (resExam.ok) {
        const dataBD = await resExam.json();
        const listaPreguntasBD = dataBD.preguntas || dataBD;

        if (Array.isArray(listaPreguntasBD) && listaPreguntasBD.length > 0) {
          const preguntasFormateadas = listaPreguntasBD.map(p => ({
            id: p.id,
            texto: p.pregunta || p.texto,
            opciones: p.opciones
          }));

          setExamData({
            titulo: `Evaluación Diagnóstica: ${puestoMapeado}`,
            duracion_minutos: 10,
            preguntas: preguntasFormateadas
          });
          setStep(3); 
          return;
        }
      }

      // Si no hay preguntas registradas en BD, ir al examen de todas formas
      setStep(3);

    } catch (err) {
      console.error('Error durante la verificación del usuario:', err);
      setStep(3);
    }
  };

  const handleExamComplete = (calculatedScore) => {
    const puntajeValido = Number(calculatedScore) || 0;
    setFinalScore(puntajeValido);
    setStep(4);
  };

  const handleLogout = () => {
    localStorage.removeItem('pluriUser');
    setCurrentUser(null);
    setUserProfile(null);
    setExamData(null);
    setFinalScore(0);
    setStep(1);
  };

  const esRRHH = currentUser?.rol === 'rh' || currentUser?.rol === 'rrhh' || currentUser?.rol === 'admin';

  return (
    <div className="min-h-screen bg-slate-100 font-sans">
      {currentUser && (
        <nav className="bg-slate-800 text-white px-6 py-3 flex justify-between items-center text-sm shadow-md">
          <span className="font-bold text-lg cursor-pointer" onClick={() => setStep(4)}>
            PluriOne Capacitaciones
          </span>
          
          <div className="flex gap-4 items-center">
            <span className="text-slate-300">
              Usuario: <strong>{currentUser.nombre || currentUser.email}</strong> ({currentUser.rol})
            </span>

            <button 
              onClick={() => setStep(4)} 
              className={`px-3 py-1 rounded transition-colors ${step === 4 ? 'bg-blue-600 font-bold' : 'hover:bg-slate-700'}`}
            >
              Mi Ruta
            </button>

            {esRRHH && (
              <button 
                onClick={() => setStep(5)} 
                className={`px-3 py-1 rounded transition-colors ${step === 5 ? 'bg-blue-600 font-bold' : 'hover:bg-slate-700'}`}
              >
                Panel RRHH
              </button>
            )}

            <button 
              onClick={handleLogout} 
              className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded font-bold transition-colors"
            >
              Cerrar Sesión
            </button>
          </div>
        </nav>
      )}

      {step === 1 && <Login onLogin={handleLogin} />}

      {step === 3 && (
        <Exam
          examData={examData}
          userName={currentUser?.nombre || currentUser?.email || "Empleado"}
          userProfile={userProfile || currentUser}
          onComplete={handleExamComplete}
        />
      )}

      {step === 4 && (
        <Dashboard
          userProfile={userProfile || currentUser}
          score={finalScore}
          setScore={setFinalScore}
          onLogout={handleLogout}
        />
      )}

      {/* Step 5: Modulo Completo de RRHH */}
      {step === 5 && (
        <div>
          {esRRHH ? (
            <PanelRRHH />
          ) : (
            <div className="text-center py-10">
              <h2 className="text-2xl font-bold text-red-600">Acceso Denegado</h2>
            </div>
          )}
        </div>
      )}
    </div>
  );
}