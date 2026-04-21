/**
 * SwiftShip Ops Dashboard — App.tsx
 */
import React, { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import { Provider, useSelector } from "react-redux";
import { configureStore, createSlice, PayloadAction } from "@reduxjs/toolkit";

// ─── Minimal Redux store for ops dashboard ────────────────────────────────────
const authSlice = createSlice({
  name: "auth",
  initialState: { token: localStorage.getItem("ops_token") as string | null, user: null as any },
  reducers: {
    setAuth: (state, action: PayloadAction<{ token: string; user: any }>) => {
      state.token = action.payload.token;
      state.user = action.payload.user;
      localStorage.setItem("ops_token", action.payload.token);
    },
    logout: (state) => {
      state.token = null;
      state.user = null;
      localStorage.removeItem("ops_token");
    },
  },
});

const store = configureStore({ reducer: { auth: authSlice.reducer } });
type RootState = ReturnType<typeof store.getState>;

// ─── Lazy pages ───────────────────────────────────────────────────────────────
const LoginPage       = lazy(() => import("./pages/OpsLoginPage"));
const DashboardPage   = lazy(() => import("./pages/OpsDashboardPage"));
const ManifestPage    = lazy(() => import("./pages/ManifestPage"));
const DispatchPage    = lazy(() => import("./pages/DispatchPage"));
const HubsPage        = lazy(() => import("./pages/HubsPage"));
const ExceptionsPage  = lazy(() => import("./pages/ExceptionsPage"));
const ReportsPage     = lazy(() => import("./pages/ReportsPage"));

const Protected: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = useSelector((s: RootState) => s.auth.token);
  return token ? <>{children}</> : <Navigate to="/login" replace />;
};

const NAV = [
  { to: "/",           label: "Dashboard",  icon: "📊" },
  { to: "/manifests",  label: "Manifests",  icon: "📦" },
  { to: "/dispatch",   label: "Dispatch",   icon: "🚚" },
  { to: "/hubs",       label: "Hubs",       icon: "🏭" },
  { to: "/exceptions", label: "Exceptions", icon: "⚠️" },
  { to: "/reports",    label: "Reports",    icon: "📈" },
];

const Shell: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="min-h-screen bg-slate-50 flex">
    <nav className="w-56 bg-slate-900 text-slate-300 flex flex-col py-6 px-4 shrink-0">
      <div className="mb-8 px-2">
        <div className="text-white font-bold text-lg">SwiftShip</div>
        <div className="text-slate-500 text-xs mt-0.5">Operations Centre</div>
      </div>
      <div className="space-y-1 flex-1">
        {NAV.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            end={n.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive ? "bg-blue-600 text-white" : "hover:bg-slate-800 hover:text-white"
              }`
            }
          >
            <span className="text-base">{n.icon}</span>
            {n.label}
          </NavLink>
        ))}
      </div>
    </nav>
    <main className="flex-1 overflow-auto">
      <div className="p-6 max-w-7xl mx-auto">{children}</div>
    </main>
  </div>
);

const OpsApp: React.FC = () => (
  <Suspense fallback={<div className="flex h-screen items-center justify-center text-slate-400">Loading...</div>}>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={
        <Protected>
          <Shell>
            <Routes>
              <Route path="/"           element={<DashboardPage />} />
              <Route path="/manifests"  element={<ManifestPage />} />
              <Route path="/dispatch"   element={<DispatchPage />} />
              <Route path="/hubs"       element={<HubsPage />} />
              <Route path="/exceptions" element={<ExceptionsPage />} />
              <Route path="/reports"    element={<ReportsPage />} />
            </Routes>
          </Shell>
        </Protected>
      } />
    </Routes>
  </Suspense>
);

const App: React.FC = () => (
  <Provider store={store}>
    <BrowserRouter>
      <OpsApp />
    </BrowserRouter>
  </Provider>
);

export default App;
