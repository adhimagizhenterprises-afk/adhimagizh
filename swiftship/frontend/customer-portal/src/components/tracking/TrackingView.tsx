/**
 * Shipment Tracking Component
 * Shows scan event timeline, current status, ETA.
 * Connects via WebSocket for live updates.
 */
import React, { useState, useEffect, useRef } from "react";
import { trackingApi } from "../../services/api";

interface TrackingEvent {
  status: string;
  location: string;
  hub_code?: string;
  remarks?: string;
  event_time: string;
}

interface TrackingData {
  awb_number: string;
  current_status: string;
  current_location: string;
  origin: string;
  destination: string;
  expected_delivery: string;
  last_updated: string;
  events: TrackingEvent[];
}

const STATUS_STEPS = [
  { key: "BOOKING_CREATED",    label: "Booked",           icon: "📋" },
  { key: "PICKED_UP",          label: "Picked Up",        icon: "🚚" },
  { key: "IN_TRANSIT",         label: "In Transit",       icon: "🏭" },
  { key: "OUT_FOR_DELIVERY",   label: "Out for Delivery", icon: "🛵" },
  { key: "DELIVERED",          label: "Delivered",        icon: "✅" },
];

const STATUS_COLORS: Record<string, string> = {
  BOOKING_CREATED:    "bg-blue-100 text-blue-700",
  PICKED_UP:          "bg-purple-100 text-purple-700",
  IN_TRANSIT:         "bg-yellow-100 text-yellow-700",
  AT_HUB:             "bg-orange-100 text-orange-700",
  OUT_FOR_DELIVERY:   "bg-indigo-100 text-indigo-700",
  DELIVERED:          "bg-green-100 text-green-700",
  DELIVERY_ATTEMPTED: "bg-orange-100 text-orange-700",
  RTO_INITIATED:      "bg-red-100 text-red-700",
  CANCELLED:          "bg-gray-100 text-gray-600",
};

export const TrackingView: React.FC<{ awbNumber?: string }> = ({ awbNumber: propAwb }) => {
  const [query, setQuery] = useState(propAwb || "");
  const [tracking, setTracking] = useState<TrackingData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const fetchTracking = async (awb: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await trackingApi.track(awb);
      setTracking(res.data);
      connectWebSocket(awb);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Shipment not found");
      setTracking(null);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = (awb: string) => {
    if (wsRef.current) wsRef.current.close();
    const wsUrl = `ws://localhost:8000/ws/tracking/${awb}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type !== "ping") {
        // Live status update received
        setTracking((prev) =>
          prev
            ? {
                ...prev,
                current_status: data.status || prev.current_status,
                current_location: data.location || prev.current_location,
                events: data.event ? [data.event, ...prev.events] : prev.events,
              }
            : prev
        );
      }
    };

    ws.onerror = () => {}; // Silent fail on WS — REST data is still shown
    wsRef.current = ws;
  };

  useEffect(() => {
    if (propAwb) fetchTracking(propAwb);
    return () => wsRef.current?.close();
  }, [propAwb]);

  const currentStepIndex = STATUS_STEPS.findIndex((s) => s.key === tracking?.current_status);

  return (
    <div className="max-w-2xl mx-auto">
      {/* Search bar */}
      <div className="flex gap-3 mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && fetchTracking(query.trim())}
          placeholder="Enter AWB number (e.g. SS20241215100527)"
          className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => fetchTracking(query.trim())}
          disabled={!query || loading}
          className="px-5 py-3 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "..." : "Track"}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm mb-6">
          {error}
        </div>
      )}

      {tracking && (
        <div className="space-y-5">
          {/* Status header */}
          <div className="p-5 bg-white rounded-2xl border border-gray-100 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-xs text-gray-400 font-mono mb-1">{tracking.awb_number}</p>
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${STATUS_COLORS[tracking.current_status] || "bg-gray-100 text-gray-600"}`}>
                  {tracking.current_status.replace(/_/g, " ")}
                </span>
              </div>
              <div className="text-right text-sm">
                <p className="text-gray-400">Expected delivery</p>
                <p className="font-semibold text-gray-800">
                  {tracking.expected_delivery
                    ? new Date(tracking.expected_delivery).toLocaleDateString("en-IN", { day: "numeric", month: "short" })
                    : "—"}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="font-medium">{tracking.origin}</span>
              <span className="flex-1 border-t-2 border-dashed border-gray-200 mx-2 relative">
                <span className="absolute -top-2 left-1/2 -translate-x-1/2 text-base">📦</span>
              </span>
              <span className="font-medium">{tracking.destination}</span>
            </div>
          </div>

          {/* Progress stepper */}
          {tracking.current_status !== "CANCELLED" && tracking.current_status !== "RTO_INITIATED" && (
            <div className="p-5 bg-white rounded-2xl border border-gray-100 shadow-sm">
              <div className="flex items-center justify-between relative">
                <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-100 z-0" />
                {STATUS_STEPS.map((step, i) => {
                  const done = i <= currentStepIndex;
                  const active = i === currentStepIndex;
                  return (
                    <div key={step.key} className="flex flex-col items-center z-10 relative">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg border-2 transition-all ${
                        done ? "bg-white border-green-400" : "bg-gray-50 border-gray-200"
                      } ${active ? "ring-4 ring-green-100" : ""}`}>
                        {step.icon}
                      </div>
                      <p className={`text-xs mt-2 text-center font-medium ${done ? "text-green-700" : "text-gray-400"}`}>
                        {step.label}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Current location */}
          <div className="p-4 bg-blue-50 rounded-xl flex items-center gap-3">
            <span className="text-xl">📍</span>
            <div>
              <p className="text-xs text-blue-500 font-medium">Current Location</p>
              <p className="text-sm text-blue-800 font-semibold">{tracking.current_location}</p>
            </div>
            <p className="ml-auto text-xs text-blue-400">
              {new Date(tracking.last_updated).toLocaleString("en-IN")}
            </p>
          </div>

          {/* Event timeline */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-50">
              <h3 className="font-semibold text-gray-800 text-sm">Shipment History</h3>
            </div>
            <div className="divide-y divide-gray-50">
              {tracking.events.map((event, i) => (
                <div key={i} className="px-5 py-4 flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className={`w-2.5 h-2.5 rounded-full mt-1 ${i === 0 ? "bg-green-500" : "bg-gray-300"}`} />
                    {i < tracking.events.length - 1 && <div className="w-0.5 flex-1 bg-gray-100 mt-1" />}
                  </div>
                  <div className="flex-1 pb-1">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-800">{event.status.replace(/_/g, " ")}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{event.location}</p>
                        {event.remarks && <p className="text-xs text-gray-400 mt-0.5 italic">{event.remarks}</p>}
                      </div>
                      <p className="text-xs text-gray-400 whitespace-nowrap">
                        {new Date(event.event_time).toLocaleString("en-IN", {
                          day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
