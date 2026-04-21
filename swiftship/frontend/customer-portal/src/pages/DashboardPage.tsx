/**
 * Dashboard Page — quick stats + recent shipments
 */
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useSelector } from "react-redux";
import { RootState } from "../store";
import { bookingApi } from "../services/api";

interface Stats {
  total: number;
  active: number;
  delivered: number;
  pending_payment: number;
}

interface RecentShipment {
  awb_number: string;
  status: string;
  receiver_city: string;
  receiver_name: string;
  service_type: string;
  total_charge: number;
  created_at: string;
}

const STATUS_COLOR: Record<string, string> = {
  BOOKING_CREATED:    "bg-blue-100 text-blue-700",
  PICKED_UP:          "bg-purple-100 text-purple-700",
  IN_TRANSIT:         "bg-yellow-100 text-yellow-700",
  OUT_FOR_DELIVERY:   "bg-indigo-100 text-indigo-700",
  DELIVERED:          "bg-green-100 text-green-700",
  CANCELLED:          "bg-gray-100 text-gray-500",
  RTO_INITIATED:      "bg-red-100 text-red-600",
};

const DashboardPage: React.FC = () => {
  const user = useSelector((s: RootState) => s.auth.user);
  const [recent, setRecent] = useState<RecentShipment[]>([]);
  const [stats, setStats] = useState<Stats>({ total: 0, active: 0, delivered: 0, pending_payment: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await bookingApi.list({ page: 1, page_size: 5 });
        const items: RecentShipment[] = res.data.items;
        setRecent(items);
        setStats({
          total: res.data.total,
          active: items.filter((s) =>
            ["BOOKING_CREATED", "PICKED_UP", "IN_TRANSIT", "OUT_FOR_DELIVERY"].includes(s.status)
          ).length,
          delivered: items.filter((s) => s.status === "DELIVERED").length,
          pending_payment: 0,
        });
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return "Good morning";
    if (h < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          {greeting()}, {user?.name?.split(" ")[0]} 👋
        </h1>
        <p className="text-gray-500 text-sm mt-1">Here's what's happening with your shipments today.</p>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Link
          to="/book"
          className="p-5 bg-blue-600 text-white rounded-2xl hover:bg-blue-700 transition-colors group"
        >
          <div className="text-2xl mb-2">📦</div>
          <div className="font-semibold">New Booking</div>
          <div className="text-blue-200 text-xs mt-0.5">Ship a package</div>
        </Link>
        <Link
          to="/track"
          className="p-5 bg-white border border-gray-100 rounded-2xl hover:border-gray-200 transition-colors"
        >
          <div className="text-2xl mb-2">🔍</div>
          <div className="font-semibold text-gray-800">Track</div>
          <div className="text-gray-400 text-xs mt-0.5">Check shipment status</div>
        </Link>
        <Link
          to="/shipments"
          className="p-5 bg-white border border-gray-100 rounded-2xl hover:border-gray-200 transition-colors"
        >
          <div className="text-2xl mb-2">📋</div>
          <div className="font-semibold text-gray-800">All Shipments</div>
          <div className="text-gray-400 text-xs mt-0.5">View history</div>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {[
          { label: "Total Shipments", value: stats.total, color: "text-gray-800" },
          { label: "Active",          value: stats.active, color: "text-blue-600" },
          { label: "Delivered",       value: stats.delivered, color: "text-green-600" },
          { label: "Avg. Delivery",   value: "3.2 days", color: "text-purple-600" },
        ].map((s) => (
          <div key={s.label} className="bg-white border border-gray-100 rounded-xl p-4">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{s.label}</p>
            <p className={`text-2xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Recent shipments */}
      <div className="bg-white rounded-2xl border border-gray-100">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-50">
          <h2 className="font-semibold text-gray-800">Recent Shipments</h2>
          <Link to="/shipments" className="text-sm text-blue-600 hover:underline">
            View all →
          </Link>
        </div>

        {loading ? (
          <div className="py-12 text-center text-gray-400 text-sm">Loading...</div>
        ) : recent.length === 0 ? (
          <div className="py-12 text-center">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-gray-500 text-sm">No shipments yet.</p>
            <Link to="/book" className="text-blue-600 text-sm font-medium hover:underline mt-1 inline-block">
              Create your first booking →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {recent.map((s) => (
              <div key={s.awb_number} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center text-xl">
                    📦
                  </div>
                  <div>
                    <p className="text-sm font-mono font-semibold text-gray-700">{s.awb_number}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      To {s.receiver_name}, {s.receiver_city}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${STATUS_COLOR[s.status] || "bg-gray-100 text-gray-600"}`}>
                    {s.status.replace(/_/g, " ")}
                  </span>
                  <span className="text-sm font-semibold text-gray-700">₹{s.total_charge}</span>
                  <span className="text-xs text-gray-400">
                    {new Date(s.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short" })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
