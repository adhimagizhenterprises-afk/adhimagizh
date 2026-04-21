/**
 * Ops Dashboard — Manifest Management
 * Create, seal, and dispatch manifests between hubs.
 */
import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";

const api = axios.create({ baseURL: process.env.REACT_APP_API_BASE_URL || "http://localhost:8000/api/v1" });
api.interceptors.request.use((c) => {
  const t = localStorage.getItem("access_token");
  if (t) c.headers.Authorization = `Bearer ${t}`;
  return c;
});

type ManifestStatus = "DRAFT" | "SEALED" | "DISPATCHED" | "RECEIVED" | "CLOSED";
type ManifestType = "PICKUP" | "FORWARD" | "DELIVERY" | "RTO";

interface Manifest {
  id: string;
  manifest_number: string;
  manifest_type: ManifestType;
  status: ManifestStatus;
  origin_hub_code: string;
  destination_hub_code: string;
  total_shipments: number;
  total_weight_kg: number;
  dispatched_at?: string;
  created_at: string;
  vehicle_number?: string;
  driver_name?: string;
}

const STATUS_BADGE: Record<ManifestStatus, string> = {
  DRAFT:      "bg-gray-100 text-gray-600",
  SEALED:     "bg-yellow-100 text-yellow-700",
  DISPATCHED: "bg-blue-100 text-blue-700",
  RECEIVED:   "bg-purple-100 text-purple-700",
  CLOSED:     "bg-green-100 text-green-700",
};

const TYPE_ICON: Record<ManifestType, string> = {
  PICKUP:   "📥",
  FORWARD:  "➡️",
  DELIVERY: "🛵",
  RTO:      "↩️",
};

const ManifestPage: React.FC = () => {
  const [manifests, setManifests] = useState<Manifest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<ManifestStatus | "ALL">("ALL");
  const [showCreate, setShowCreate] = useState(false);
  const [selectedManifest, setSelectedManifest] = useState<Manifest | null>(null);

  const fetchManifests = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get("/operations/manifests/", {
        params: filter !== "ALL" ? { status: filter } : {},
      });
      setManifests(res.data.items || res.data);
    } catch (err) {
      console.error("Failed to fetch manifests", err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { fetchManifests(); }, [fetchManifests]);

  const handleSeal = async (manifestNumber: string) => {
    try {
      await api.post(`/operations/manifests/${manifestNumber}/seal`);
      fetchManifests();
    } catch (err) {
      alert("Failed to seal manifest");
    }
  };

  const handleDispatch = async (manifestNumber: string, vehicleNumber: string, driverName: string) => {
    try {
      await api.post(`/operations/manifests/${manifestNumber}/dispatch`, {
        vehicle_number: vehicleNumber,
        driver_name: driverName,
      });
      fetchManifests();
    } catch (err) {
      alert("Failed to dispatch manifest");
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Manifests</h1>
          <p className="text-sm text-gray-500 mt-0.5">Manage shipment bags between hubs</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          + Create Manifest
        </button>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-5 gap-4 mb-6">
        {(["ALL", "DRAFT", "SEALED", "DISPATCHED", "RECEIVED"] as const).map((s) => {
          const count = s === "ALL" ? manifests.length : manifests.filter((m) => m.status === s).length;
          return (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`p-4 rounded-xl text-left border transition-all ${
                filter === s ? "border-blue-400 bg-blue-50" : "border-gray-100 bg-white hover:border-gray-200"
              }`}
            >
              <p className="text-2xl font-bold text-gray-800">{count}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s === "ALL" ? "Total" : s}</p>
            </button>
          );
        })}
      </div>

      {/* Manifests table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100">
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Manifest #</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Type</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Route</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Shipments</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Weight</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              <tr><td colSpan={7} className="text-center py-12 text-gray-400">Loading...</td></tr>
            ) : manifests.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-12 text-gray-400">No manifests found</td></tr>
            ) : (
              manifests.map((m) => (
                <tr key={m.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedManifest(m)}>
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{m.manifest_number}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1">
                      <span>{TYPE_ICON[m.manifest_type]}</span>
                      <span>{m.manifest_type}</span>
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {m.origin_hub_code} → {m.destination_hub_code || "—"}
                  </td>
                  <td className="px-4 py-3 text-center font-semibold">{m.total_shipments}</td>
                  <td className="px-4 py-3 text-center text-gray-600">{m.total_weight_kg?.toFixed(1)} kg</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${STATUS_BADGE[m.status]}`}>
                      {m.status}
                    </span>
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    {m.status === "DRAFT" && (
                      <button
                        onClick={() => handleSeal(m.manifest_number)}
                        className="px-3 py-1 text-xs bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 font-medium"
                      >
                        Seal
                      </button>
                    )}
                    {m.status === "SEALED" && (
                      <button
                        onClick={() => {
                          const vehicle = prompt("Vehicle number:");
                          const driver = prompt("Driver name:");
                          if (vehicle && driver) handleDispatch(m.manifest_number, vehicle, driver);
                        }}
                        className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 font-medium"
                      >
                        Dispatch
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ManifestPage;
