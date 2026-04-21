/**
 * Multi-step booking form component
 * Steps: Sender → Receiver → Package → Service → Review & Pay
 */
import React, { useState, useEffect } from "react";
import { useDispatch } from "react-redux";
import { bookingApi, CreateBookingPayload } from "../../services/api";
import { prependShipment } from "../../store";
import toast from "react-hot-toast";

type Step = 1 | 2 | 3 | 4 | 5;

interface FormData extends Partial<CreateBookingPayload> {}

const SERVICE_TYPES = [
  { value: "EXPRESS",  label: "Express",  desc: "Next day delivery",  icon: "⚡" },
  { value: "PRIORITY", label: "Priority", desc: "2-day delivery",      icon: "🚀" },
  { value: "STANDARD", label: "Standard", desc: "3-5 days",            icon: "📦" },
  { value: "ECONOMY",  label: "Economy",  desc: "5-7 days",            icon: "🌿" },
];

const STEPS = ["Sender", "Receiver", "Package", "Service", "Review"];

export const BookingForm: React.FC = () => {
  const dispatch = useDispatch();
  const [step, setStep] = useState<Step>(1);
  const [formData, setFormData] = useState<FormData>({
    payment_mode: "PREPAID",
    is_fragile: false,
    service_type: "STANDARD",
    pickup_date: new Date(Date.now() + 86400000).toISOString().split("T")[0],
  });
  const [priceQuote, setPriceQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const update = (fields: Partial<FormData>) =>
    setFormData((prev) => ({ ...prev, ...fields }));

  // Recalculate price when relevant fields change
  useEffect(() => {
    const { sender_pincode, receiver_pincode, weight_kg, service_type } = formData;
    if (sender_pincode?.length === 6 && receiver_pincode?.length === 6 && weight_kg) {
      bookingApi
        .calculatePrice({
          sender_pincode,
          receiver_pincode,
          weight_kg,
          length_cm: formData.length_cm,
          width_cm: formData.width_cm,
          height_cm: formData.height_cm,
          service_type: service_type || "STANDARD",
          payment_mode: formData.payment_mode || "PREPAID",
          cod_amount: formData.cod_amount,
        })
        .then((res) => setPriceQuote(res.data))
        .catch(() => {});
    }
  }, [
    formData.sender_pincode,
    formData.receiver_pincode,
    formData.weight_kg,
    formData.service_type,
    formData.payment_mode,
  ]);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const res = await bookingApi.create(formData as CreateBookingPayload);
      dispatch(prependShipment(res.data));
      toast.success(`Booking created! AWB: ${res.data.awb_number}`);

      if (formData.payment_mode === "PREPAID" && (window as any).Razorpay) {
        const orderRes = await bookingApi.calculatePrice({
          sender_pincode: formData.sender_pincode!,
          receiver_pincode: formData.receiver_pincode!,
          weight_kg: formData.weight_kg!,
          service_type: formData.service_type!,
          payment_mode: "PREPAID",
        });
        // Razorpay checkout handled by parent page
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Booking failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-100">
      {/* Step indicator */}
      <div className="flex items-center px-8 pt-6 pb-4 gap-2">
        {STEPS.map((label, i) => (
          <React.Fragment key={label}>
            <div className="flex flex-col items-center gap-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${
                  i + 1 === step
                    ? "bg-blue-600 text-white"
                    : i + 1 < step
                    ? "bg-green-500 text-white"
                    : "bg-gray-100 text-gray-400"
                }`}
              >
                {i + 1 < step ? "✓" : i + 1}
              </div>
              <span className={`text-xs ${i + 1 === step ? "text-blue-600 font-medium" : "text-gray-400"}`}>
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mt-[-12px] ${i + 1 < step ? "bg-green-400" : "bg-gray-100"}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      <div className="px-8 pb-8">
        {/* Step 1 — Sender */}
        {step === 1 && (
          <StepSection title="Sender Details">
            <AddressFields prefix="sender" data={formData} onChange={update} />
          </StepSection>
        )}

        {/* Step 2 — Receiver */}
        {step === 2 && (
          <StepSection title="Receiver Details">
            <AddressFields prefix="receiver" data={formData} onChange={update} />
          </StepSection>
        )}

        {/* Step 3 — Package */}
        {step === 3 && (
          <StepSection title="Package Details">
            <div className="grid grid-cols-2 gap-4">
              <InputField label="Weight (kg)" type="number" step="0.1" min="0.1"
                value={formData.weight_kg || ""} onChange={(v) => update({ weight_kg: parseFloat(v) })} />
              <InputField label="Declared Value (₹)" type="number"
                value={formData.declared_value || ""} onChange={(v) => update({ declared_value: parseFloat(v) })} />
              <InputField label="Length (cm)" type="number"
                value={formData.length_cm || ""} onChange={(v) => update({ length_cm: parseFloat(v) })} />
              <InputField label="Width (cm)" type="number"
                value={formData.width_cm || ""} onChange={(v) => update({ width_cm: parseFloat(v) })} />
              <InputField label="Height (cm)" type="number"
                value={formData.height_cm || ""} onChange={(v) => update({ height_cm: parseFloat(v) })} />
              <InputField label="Contents" type="text"
                value={formData.contents_description || ""} onChange={(v) => update({ contents_description: v })} />
            </div>
            <label className="flex items-center gap-2 mt-4 cursor-pointer">
              <input type="checkbox" checked={formData.is_fragile}
                onChange={(e) => update({ is_fragile: e.target.checked })}
                className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-700">Fragile item — handle with care</span>
            </label>
            {priceQuote && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                Chargeable weight: <strong>{priceQuote.chargeable_weight_kg} kg</strong>
                {priceQuote.chargeable_weight_kg > formData.weight_kg! && (
                  <span className="ml-2 text-orange-600">(volumetric weight applied)</span>
                )}
              </div>
            )}
          </StepSection>
        )}

        {/* Step 4 — Service & Payment */}
        {step === 4 && (
          <StepSection title="Service & Payment">
            <div className="grid grid-cols-2 gap-3 mb-6">
              {SERVICE_TYPES.map((s) => (
                <div
                  key={s.value}
                  onClick={() => update({ service_type: s.value as any })}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    formData.service_type === s.value
                      ? "border-blue-500 bg-blue-50"
                      : "border-gray-100 hover:border-gray-200"
                  }`}
                >
                  <div className="text-2xl mb-1">{s.icon}</div>
                  <div className="font-semibold text-gray-800">{s.label}</div>
                  <div className="text-xs text-gray-500">{s.desc}</div>
                  {priceQuote?.services?.[s.value] && (
                    <div className="text-sm font-bold text-blue-600 mt-1">
                      ₹{priceQuote.services[s.value].total}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex gap-4 mb-4">
              {(["PREPAID", "COD"] as const).map((mode) => (
                <label key={mode} className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" value={mode} checked={formData.payment_mode === mode}
                    onChange={() => update({ payment_mode: mode })} />
                  <span className="text-sm font-medium">{mode === "COD" ? "Cash on Delivery" : "Prepaid"}</span>
                </label>
              ))}
            </div>

            {formData.payment_mode === "COD" && (
              <InputField label="COD Amount (₹)" type="number"
                value={formData.cod_amount || ""} onChange={(v) => update({ cod_amount: parseFloat(v) })} />
            )}

            <InputField label="Pickup Date" type="date"
              value={formData.pickup_date || ""} onChange={(v) => update({ pickup_date: v })} />
          </StepSection>
        )}

        {/* Step 5 — Review */}
        {step === 5 && (
          <StepSection title="Review & Confirm">
            <ReviewRow label="From" value={`${formData.sender_name}, ${formData.sender_city} - ${formData.sender_pincode}`} />
            <ReviewRow label="To" value={`${formData.receiver_name}, ${formData.receiver_city} - ${formData.receiver_pincode}`} />
            <ReviewRow label="Weight" value={`${formData.weight_kg} kg`} />
            <ReviewRow label="Service" value={formData.service_type || ""} />
            <ReviewRow label="Payment" value={formData.payment_mode || ""} />
            <ReviewRow label="Pickup Date" value={formData.pickup_date || ""} />
            {priceQuote && (
              <div className="mt-4 p-4 bg-gray-50 rounded-xl">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Freight</span>
                  <span>₹{priceQuote.freight_charge}</span>
                </div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Fuel surcharge</span>
                  <span>₹{priceQuote.fuel_surcharge}</span>
                </div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-500">GST (18%)</span>
                  <span>₹{priceQuote.gst_amount}</span>
                </div>
                <div className="flex justify-between font-bold text-blue-700 text-base border-t pt-2">
                  <span>Total</span>
                  <span>₹{priceQuote.total_charge}</span>
                </div>
              </div>
            )}
          </StepSection>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <button
            onClick={() => setStep((s) => Math.max(1, s - 1) as Step)}
            className={`px-5 py-2.5 rounded-lg border border-gray-200 text-sm font-medium text-gray-600 hover:bg-gray-50 ${step === 1 ? "invisible" : ""}`}
          >
            ← Back
          </button>
          {step < 5 ? (
            <button
              onClick={() => setStep((s) => Math.min(5, s + 1) as Step)}
              className="px-6 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
            >
              Continue →
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-6 py-2.5 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 disabled:opacity-60 transition-colors"
            >
              {loading ? "Creating booking..." : "Confirm Booking ✓"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ─── Sub-components ────────────────────────────────────────────────────────────
const StepSection: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div>
    <h2 className="text-lg font-semibold text-gray-800 mb-5">{title}</h2>
    {children}
  </div>
);

const InputField: React.FC<{ label: string; type?: string; value: any; onChange: (v: string) => void; step?: string; min?: string }> =
  ({ label, type = "text", value, onChange, step, min }) => (
    <div className="mb-4">
      <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">{label}</label>
      <input
        type={type} step={step} min={min} value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );

const AddressFields: React.FC<{ prefix: "sender" | "receiver"; data: FormData; onChange: (v: Partial<FormData>) => void }> =
  ({ prefix, data, onChange }) => (
    <div className="grid grid-cols-2 gap-4">
      <div className="col-span-2">
        <InputField label="Full Name" value={(data as any)[`${prefix}_name`] || ""} onChange={(v) => onChange({ [`${prefix}_name`]: v })} />
      </div>
      <InputField label="Phone" value={(data as any)[`${prefix}_phone`] || ""} onChange={(v) => onChange({ [`${prefix}_phone`]: v })} />
      <InputField label="Email" value={(data as any)[`${prefix}_email`] || ""} onChange={(v) => onChange({ [`${prefix}_email`]: v })} />
      <div className="col-span-2">
        <InputField label="Address Line 1" value={(data as any)[`${prefix}_address_line1`] || ""} onChange={(v) => onChange({ [`${prefix}_address_line1`]: v })} />
      </div>
      <InputField label="City" value={(data as any)[`${prefix}_city`] || ""} onChange={(v) => onChange({ [`${prefix}_city`]: v })} />
      <InputField label="State" value={(data as any)[`${prefix}_state`] || ""} onChange={(v) => onChange({ [`${prefix}_state`]: v })} />
      <InputField label="Pincode" value={(data as any)[`${prefix}_pincode`] || ""} onChange={(v) => onChange({ [`${prefix}_pincode`]: v })} />
    </div>
  );

const ReviewRow: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div className="flex justify-between py-2 border-b border-gray-50 text-sm">
    <span className="text-gray-500">{label}</span>
    <span className="font-medium text-gray-800 text-right max-w-xs">{value}</span>
  </div>
);
