// ExceptionsPage.tsx
import React from "react";
export default function ExceptionsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Exceptions</h1>
      <div className="bg-white border border-gray-100 rounded-xl p-8 text-center text-gray-400">
        <div className="text-4xl mb-3">⚠️</div>
        <p className="font-medium text-gray-600">Shipment Exceptions</p>
        <p className="text-sm mt-1">Resolve undelivered, damaged, or held shipments</p>
        <p className="text-xs mt-4 text-blue-500">API: GET /api/v1/operations/exceptions</p>
      </div>
    </div>
  );
}
