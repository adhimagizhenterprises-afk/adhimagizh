// DispatchPage.tsx
import React from "react";
export default function DispatchPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dispatch Management</h1>
      <div className="bg-white border border-gray-100 rounded-xl p-8 text-center text-gray-400">
        <div className="text-4xl mb-3">🚚</div>
        <p className="font-medium text-gray-600">Route Planning &amp; Agent Assignment</p>
        <p className="text-sm mt-1">Create delivery routes and assign shipments to agents</p>
        <p className="text-xs mt-4 text-blue-500">API: POST /api/v1/operations/dispatch/routes</p>
      </div>
    </div>
  );
}
