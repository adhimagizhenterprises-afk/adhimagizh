// ReportsPage.tsx
import React from "react";
export default function ReportsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Reports &amp; MIS</h1>
      <div className="grid grid-cols-2 gap-4">
        {[
          { title: "Daily Summary",        icon: "📊", desc: "Bookings, pickups, deliveries per day" },
          { title: "Agent Performance",    icon: "👤", desc: "Delivery rate, attempts, avg time" },
          { title: "Hub Throughput",       icon: "🏭", desc: "Volume processed per hub" },
          { title: "COD Remittance",       icon: "💰", desc: "Pending and completed COD payouts" },
          { title: "Exception Analysis",   icon: "⚠️", desc: "Exception types, resolution time" },
          { title: "Zone-wise Revenue",    icon: "🗺️", desc: "Revenue breakdown by delivery zone" },
        ].map((r) => (
          <div key={r.title} className="bg-white border border-gray-100 rounded-xl p-5 hover:border-gray-200 cursor-pointer transition-all">
            <div className="text-2xl mb-2">{r.icon}</div>
            <div className="font-semibold text-gray-800 text-sm">{r.title}</div>
            <div className="text-xs text-gray-400 mt-0.5">{r.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
