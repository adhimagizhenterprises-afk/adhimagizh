/**
 * Ops Dashboard Overview — live operational metrics
 */
import React, { useEffect, useState } from "react";

const METRICS = [
  { label: "Booked Today",       key: "booked",        color: "text-blue-400",   bg: "bg-blue-900/30",   icon: "📋" },
  { label: "Picked Up",          key: "picked_up",     color: "text-purple-400", bg: "bg-purple-900/30", icon: "📥" },
  { label: "In Transit",         key: "in_transit",    color: "text-yellow-400", bg: "bg-yellow-900/30", icon: "🚛" },
  { label: "Out for Delivery",   key: "ofd",           color: "text-indigo-400", bg: "bg-indigo-900/30", icon: "🛵" },
  { label: "Delivered",          key: "delivered",     color: "text-green-400",  bg: "bg-green-900/30",  icon: "✅" },
  { label: "Exceptions",         key: "exceptions",    color: "text-red-400",    bg: "bg-red-900/30",    icon: "⚠️" },
];

const ACTIVE_MANIFESTS = [
  { number: "MFT-CHN-20241215-1201", type: "FORWARD", route: "CHN → BLR", shipments: 48, status: "DISPATCHED", vehicle: "TN01AB1234" },
  { number: "MFT-CHN-20241215-1204", type: "DELIVERY", route: "CHN Hub", shipments: 32, status: "SEALED",     vehicle: "—" },
  { number: "MFT-BLR-20241215-0901", type: "PICKUP",  route: "BLR Hub",  shipments: 15, status: "RECEIVED",  vehicle: "KA05CD5678" },
];

const STATUS_COLOR: Record<string, string> = {
  DRAFT: "bg-slate-700 text-slate-300",
  SEALED: "bg-yellow-900/50 text-yellow-400",
  DISPATCHED: "bg-blue-900/50 text-blue-400",
  RECEIVED: "bg-purple-900/50 text-purple-400",
  CLOSED: "bg-green-900/50 text-green-400",
};

const OpsDashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<Record<string, number>>({
    booked: 0, picked_up: 0, in_transit: 0, ofd: 0, delivered: 0, exceptions: 0,
  });
  const [tick, setTick] = useState(0);

  // Simulate live metrics (replace with real API call in production)
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics({
        booked: 342 + Math.floor(Math.random() * 5),
        picked_up: 287 + Math.floor(Math.random() * 3),
        in_transit: 1240 + Math.floor(Math.random() * 8),
        ofd: 186 + Math.floor(Math.random() * 4),
        delivered: 134 + Math.floor(Math.random() * 6),
        exceptions: 12 + Math.floor(Math.random() * 2),
      });
      setTick((t) => t + 1);
    }, 5000);
    setMetrics({ booked: 342, picked_up: 287, in_transit: 1240, ofd: 186, delivered: 134, exceptions: 12 });
    return () => clearInterval(interval);
  }, []);

  const deliveryPct = metrics.delivered && metrics.ofd
    ? Math.round((metrics.delivered / (metrics.delivered + metrics.ofd + metrics.exceptions)) * 100)
    : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Operations Overview</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
            <span className="ml-3 text-xs text-green-500 font-medium">● Live</span>
          </p>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-6 gap-4 mb-8">
        {METRICS.map((m) => (
          <div key={m.key} className="bg-white border border-gray-100 rounded-xl p-4">
            <div className="text-xl mb-2">{m.icon}</div>
            <div className="text-2xl font-bold text-gray-800">{metrics[m.key] || 0}</div>
            <div className="text-xs text-gray-400 mt-0.5 leading-tight">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Delivery performance bar */}
      <div className="bg-white border border-gray-100 rounded-xl p-5 mb-6">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-semibold text-gray-700">Today's Delivery Rate</span>
          <span className="text-lg font-bold text-green-600">{deliveryPct}%</span>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-400 to-green-500 rounded-full transition-all duration-1000"
            style={{ width: `${deliveryPct}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-2">
          <span>{metrics.delivered} delivered</span>
          <span>{metrics.ofd} pending</span>
          <span>{metrics.exceptions} exceptions</span>
        </div>
      </div>

      {/* Active manifests */}
      <div className="bg-white border border-gray-100 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-50 flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Active Manifests</h2>
          <a href="/manifests" className="text-xs text-blue-600 hover:underline">View all →</a>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100">
              {["Manifest #", "Type", "Route", "Shipments", "Vehicle", "Status"].map((h) => (
                <th key={h} className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {ACTIVE_MANIFESTS.map((m) => (
              <tr key={m.number} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs text-gray-700">{m.number}</td>
                <td className="px-4 py-3 text-gray-600">{m.type}</td>
                <td className="px-4 py-3 text-gray-600">{m.route}</td>
                <td className="px-4 py-3 font-semibold text-center">{m.shipments}</td>
                <td className="px-4 py-3 font-mono text-xs text-gray-500">{m.vehicle}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${STATUS_COLOR[m.status] || "bg-gray-100 text-gray-600"}`}>
                    {m.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OpsDashboardPage;
