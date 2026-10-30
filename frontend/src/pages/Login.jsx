import React, { useState, useEffect } from 'react';
import { apiFetch } from '../api';

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [usuariosSimulador, setUsuariosSimulador] = useState([]);

  // Cargar lista del simulador ÚNICAMENTE para autocompletar el correo en la demo
  useEffect(() => {
    apiFetch('/api/usuarios/simulador')
      .then((res) => res.json())
      .then((data) => setUsuariosSimulador(data))
      .catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      // Iniciar sesión llamando a la API mediante apiFetch
      const res = await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || 'Correo o contraseña incorrectos');
        return;
      }

      // /api/auth/login retorna la información del usuario y su nuevo access_token
      onLogin({ ...data.user, access_token: data.access_token });
    } catch (err) {
      setError('Error al conectar con el servidor');
    }
  };

  const handleSelectSimulador = (e) => {
    setEmail(e.target.value);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Iniciar Sesión</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
            {error}
          </div>
        )}

        {/* Ayuda visual para la demo (solo rellena el correo) */}
        {usuariosSimulador.length > 0 && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Demo: Seleccionar usuario para autocompletar correo
            </label>
            <select
              onChange={handleSelectSimulador}
              className="w-full p-2 border rounded-md text-sm bg-gray-50"
            >
              <option value="">-- Selecciona un usuario --</option>
              {usuariosSimulador.map((u) => (
                <option key={u.id} value={u.email}>
                  {u.nombre} ({u.rol}) - {u.email}
                </option>
              ))}
            </select>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Correo electrónico</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 border rounded-md"
              placeholder="ana.rojas@plurione.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Contraseña</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 border rounded-md"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700 font-semibold"
          >
            Entrar
          </button>
        </form>
      </div>
    </div>
  );
}