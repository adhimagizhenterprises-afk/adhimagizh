/**
 * Tracking Page — public, no auth required
 */
import React from "react";
import { useParams } from "react-router-dom";
import { TrackingView } from "../components/tracking/TrackingView";

const TrackingPage: React.FC = () => {
  const { awb } = useParams<{ awb?: string }>();
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <span className="text-3xl font-bold text-blue-600">Swift</span>
          <span className="text-3xl font-bold text-gray-800">Ship</span>
          <p className="text-gray-400 text-sm mt-1">Track your shipment</p>
        </div>
        <TrackingView awbNumber={awb} />
      </div>
    </div>
  );
};

export default TrackingPage;
