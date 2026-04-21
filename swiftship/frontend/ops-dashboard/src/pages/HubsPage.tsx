// HubsPage.tsx
import React from "react";
export default function HubsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Hub Management</h1>
      <div className="bg-white border border-gray-100 rounded-xl p-8 text-center text-gray-400">
        <div className="text-4xl mb-3">🏭</div>
        <p className="font-medium text-gray-600">Hub &amp; Branch Network</p>
        <p className="text-sm mt-1">View and manage all origin, transit and destination hubs</p>
        <p className="text-xs mt-4 text-blue-500">API: GET /api/v1/operations/hubs</p>
      </div>
    </div>
  );
}
