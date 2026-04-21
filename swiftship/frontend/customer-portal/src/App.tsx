/**
 * SwiftShip Customer Portal — App.tsx
 * Main router and layout
 */
import React, { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate, NavLink } from "react-router-dom";
import { Provider, useSelector } from "react-redux";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import { store, RootState } from "./store";

// Lazy-loaded pages
const LoginPage     = lazy(() => import("./pages/LoginPage"));
const RegisterPage  = lazy(() => import("./pages/RegisterPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const BookingPage   = lazy(() => import("./pages/BookingPage"));
const TrackingPage  = lazy(() => import("./pages/TrackingPage"));
const ShipmentsPage = lazy(() => import("./pages/ShipmentsPage"));
const ProfilePage   = lazy(() => import("./pages/ProfilePage"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

// ─── Protected route ──────────────────────────────────────────────────────────
const Protected: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = useSelector((s: RootState) => s.auth.token);
  return token ? <>{children}</> : <Navigate to="/login" replace />;
};

// ─── App shell layout ─────────────────────────────────────────────────────────
const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const user = useSelector((s: RootState) => s.auth.user);
  const navItems = [
    { to: "/",          label: "Dashboard",  icon: "🏠" },
    { to: "/book",      label: "New Booking", icon: "📦" },
    { to: "/track",     label: "Track",       icon: "🔍" },
    { to: "/shipments", label: "Shipments",   icon: "📋" },
    { to: "/profile",   label: "Profile",     icon: "👤" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <nav className="w-56 bg-white border-r border-gray-100 flex flex-col py-6 px-4 shrink-0">
        <div className="mb-8 px-2">
          <span className="text-xl font-bold text-blue-600">Swift</span>
          <span className="text-xl font-bold text-gray-800">Ship</span>
          <p className="text-xs text-gray-400 mt-0.5">Logistics Platform</p>
        </div>
        <div className="space-y-1 flex-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-800"
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </div>
        {user && (
          <div className="px-3 py-2 border-t border-gray-50 mt-4">
            <p className="text-sm font-medium text-gray-700 truncate">{user.name}</p>
            <p className="text-xs text-gray-400 truncate">{user.email}</p>
          </div>
        )}
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-5xl mx-auto p-8">{children}</div>
      </main>
    </div>
  );
};

// ─── Root App ─────────────────────────────────────────────────────────────────
const AppRoutes: React.FC = () => (
  <Suspense fallback={<div className="flex items-center justify-center h-screen text-gray-400">Loading...</div>}>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/track/:awb?" element={<TrackingPage />} />
      <Route
        path="/*"
        element={
          <Protected>
            <AppShell>
              <Routes>
                <Route path="/"          element={<DashboardPage />} />
                <Route path="/book"      element={<BookingPage />} />
                <Route path="/shipments" element={<ShipmentsPage />} />
                <Route path="/profile"   element={<ProfilePage />} />
              </Routes>
            </AppShell>
          </Protected>
        }
      />
    </Routes>
  </Suspense>
);

const App: React.FC = () => (
  <Provider store={store}>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster position="top-right" />
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  </Provider>
);

export default App;
