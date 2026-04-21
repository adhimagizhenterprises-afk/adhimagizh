/**
 * Booking Page — wraps BookingForm component
 */
import React from "react";
import { BookingForm } from "../components/booking/BookingForm";

const BookingPage: React.FC = () => (
  <div>
    <div className="mb-6">
      <h1 className="text-2xl font-bold text-gray-900">New Booking</h1>
      <p className="text-sm text-gray-400 mt-0.5">Create a new shipment in under 2 minutes</p>
    </div>
    <BookingForm />
  </div>
);

export default BookingPage;
