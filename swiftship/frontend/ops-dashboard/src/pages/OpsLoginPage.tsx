// OpsLoginPage.tsx
import React, { useState } from "react";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const BASE = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000/api/v1";

const OpsLoginPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await axios.post(`${BASE}/auth/login`,
        new URLSearchParams({ username: form.username, password: form.password }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );
      if (!["OPS", "ADMIN"].includes(res.data.user.role)) {
        setError("Access denied. Ops or Admin role required.");
        return;
      }
      dispatch({ type: "auth/setAuth", payload: { token: res.data.access_token, user: res.data.user } });
      navigate("/");
    } catch {
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="text-white text-2xl font-bold">SwiftShip</div>
          <div className="text-slate-400 text-sm mt-1">Operations Centre</div>
        </div>
        <form onSubmit={handleSubmit} className="bg-slate-800 rounded-2xl p-6 space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide block mb-1.5">Email</label>
            <input type="text" value={form.username} onChange={e => setForm(f => ({...f, username: e.target.value}))}
              className="w-full px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="ops@swiftship.in" required />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wide block mb-1.5">Password</label>
            <input type="password" value={form.password} onChange={e => setForm(f => ({...f, password: e.target.value}))}
              className="w-full px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              placeholder="••••••••" required />
          </div>
          {error && <div className="text-red-400 text-sm p-2 bg-red-900/30 rounded-lg">{error}</div>}
          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg font-semibold text-sm hover:bg-blue-700 disabled:opacity-60">
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default OpsLoginPage;
