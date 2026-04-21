/**
 * All Shipments Page — paginated list with filters
 */
import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { bookingApi } from "../services/api";
import toast from "react-hot-toast";

const STATUSES = ["All", "BOOKING_CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED", "RTO_INITIATED"];

const STATUS_COLOR: Record<string, string> = {
  BOOKING_CREATED:    "bg-blue-100 text-blue-700",
  PICKED_UP:          "bg-purple-100 text-purple-700",
  IN_TRANSIT:         "bg-yellow-100 text-yellow-700",
  AT_HUB:             "bg-orange-100 text-orange-700",
  OUT_FOR_DELIVERY:   "bg-indigo-100 text-indigo-700",
  DELIVERED:          "bg-green-100 text-green-700",
  CANCELLED:          "bg-gray-100 text-gray-500",
  RTO_INITIATED:      "bg-red-100 text-red-600",
};

const ShipmentsPage: React.FC = () => {
  const [shipments, setShipments] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const PAGE_SIZE = 15;

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: PAGE_SIZE };
      if (statusFilter !== "All") params.status = statusFilter;
      const res = await bookingApi.list(params);
      setShipments(res.data.items);
      setTotal(res.data.total);
    } catch {
      toast.error("Failed to load shipments");
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => { fetch(); }, [fetch]);

  const handleDownloadLabel = async (awb: string) => {
    try {
      const res = await bookingApi.getLabel(awb);
      window.open(res.data.label_url, "_blank");
    } catch {
      toast.error("Label not available yet");
    }
  };

  const handleCancel = async (awb: string) => {
    if (!window.confirm(`Cancel shipment ${awb}?`)) return;
    try {
      await bookingApi.cancel(awb, "Customer requested cancellation");
      toast.success("Shipment cancelled");
      fetch();
    } catch (e: any) {
      toast.error(e.response?.data?.detail || "Cannot cancel this shipment");
    }
  };

  const pages = Math.ceil(total / PAGE_SIZE);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Shipments</h1>
          <p className="text-sm text-gray-400 mt-0.5">{total} total shipments</p>
        </div>
        <Link
          to="/book"
          className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors"
        >
          + New Booking
        </Link>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-1">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => { setStatusFilter(s); setPage(1); }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
              statusFilter === s
                ? "bg-blue-600 text-white"
                : "bg-white border border-gray-100 text-gray-600 hover:border-gray-200"
            }`}
          >
            {s === "All" ? "All" : s.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100">
              {["AWB", "Destination", "Service", "Weight", "Charge", "Status", "Date", "Actions"].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              <tr><td colSpan={8} className="text-center py-12 text-gray-400">Loading...</td></tr>
            ) : shipments.length === 0 ? (
              <tr><td colSpan={8} className="text-center py-12 text-gray-400">No shipments found</td></tr>
            ) : (
              shipments.map((s) => (
                <tr key={s.awb_number} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-blue-600">
                    <Link to={`/track/${s.awb_number}`} className="hover:underline">
                      {s.awb_number}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    <div>{s.receiver_name}</div>
                    <div className="text-xs text-gray-400">{s.receiver_city} - {s.receiver_pincode}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{s.service_type}</td>
                  <td className="px-4 py-3 text-gray-600">{s.chargeable_weight_kg} kg</td>
                  <td className="px-4 py-3 font-semibold text-gray-700">₹{s.total_charge}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${STATUS_COLOR[s.status] || "bg-gray-100 text-gray-600"}`}>
                      {s.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {new Date(s.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleDownloadLabel(s.awb_number)}
                        title="Download Label"
                        className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      >
                        🏷️
                      </button>
                      {["BOOKING_CREATED", "PICKUP_SCHEDULED"].includes(s.status) && (
                        <button
                          onClick={() => handleCancel(s.awb_number)}
                          title="Cancel"
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-50">
            <p className="text-sm text-gray-400">
              Page {page} of {pages} — {total} shipments
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 text-xs font-medium border border-gray-100 rounded-lg hover:bg-gray-50 disabled:opacity-40"
              >
                ← Prev
              </button>
              <button
                onClick={() => setPage((p) => Math.min(pages, p + 1))}
                disabled={page === pages}
                className="px-3 py-1.5 text-xs font-medium border border-gray-100 rounded-lg hover:bg-gray-50 disabled:opacity-40"
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShipmentsPage;
