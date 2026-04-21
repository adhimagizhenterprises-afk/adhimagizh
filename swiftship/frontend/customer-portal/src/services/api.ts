/**
 * API service layer — all HTTP calls to the SwiftShip backend
 */
import axios from "axios";

const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000/api/v1";

// ─── Axios instance ────────────────────────────────────────────────────────────
const api = axios.create({ baseURL: BASE_URL });

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = localStorage.getItem("refresh_token");
        const res = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh });
        localStorage.setItem("access_token", res.data.access_token);
        original.headers.Authorization = `Bearer ${res.data.access_token}`;
        return api(original);
      } catch {
        localStorage.clear();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (username: string, password: string) =>
    api.post("/auth/login", new URLSearchParams({ username, password }), {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }),
  register: (data: { name: string; email: string; phone: string; password: string }) =>
    api.post("/auth/register", data),
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },
};

// ─── Bookings ─────────────────────────────────────────────────────────────────
export const bookingApi = {
  create: (data: CreateBookingPayload) => api.post("/bookings/", data),
  list: (params?: BookingListParams) => api.get("/bookings/", { params }),
  get: (awb: string) => api.get(`/bookings/${awb}`),
  cancel: (awb: string, reason: string) => api.post(`/bookings/${awb}/cancel`, { reason }),
  bulkCreate: (bookings: CreateBookingPayload[]) => api.post("/bookings/bulk", { bookings }),
  getLabel: (awb: string) => api.get(`/bookings/${awb}/label`),
  calculatePrice: (data: PriceCalcPayload) => api.post("/pricing/calculate", data),
  checkServiceability: (pincode: string) => api.get(`/pricing/serviceability/${pincode}`),
};

// ─── Tracking ─────────────────────────────────────────────────────────────────
export const trackingApi = {
  track: (awb: string) => api.get(`/tracking/${awb}`),
  getETA: (awb: string) => api.get(`/tracking/eta/${awb}`),
  search: (q: string) => api.get("/tracking/search/", { params: { q } }),
};

// ─── Addresses ────────────────────────────────────────────────────────────────
export const addressApi = {
  list: () => api.get("/addresses/"),
  create: (data: AddressPayload) => api.post("/addresses/", data),
  update: (id: string, data: Partial<AddressPayload>) => api.put(`/addresses/${id}`, data),
  delete: (id: string) => api.delete(`/addresses/${id}`),
  setDefault: (id: string) => api.patch(`/addresses/${id}/default`),
};

// ─── Payments ─────────────────────────────────────────────────────────────────
export const paymentApi = {
  createOrder: (awb: string, amount: number) =>
    api.post("/payments/create-order", { awb_number: awb, amount }),
  verifyPayment: (data: RazorpayVerifyPayload) => api.post("/payments/verify", data),
  getHistory: () => api.get("/payments/"),
};

// ─── Types ────────────────────────────────────────────────────────────────────
export interface CreateBookingPayload {
  sender_name: string;
  sender_phone: string;
  sender_email?: string;
  sender_address_line1: string;
  sender_address_line2?: string;
  sender_city: string;
  sender_state: string;
  sender_pincode: string;
  receiver_name: string;
  receiver_phone: string;
  receiver_email?: string;
  receiver_address_line1: string;
  receiver_address_line2?: string;
  receiver_city: string;
  receiver_state: string;
  receiver_pincode: string;
  weight_kg: number;
  length_cm?: number;
  width_cm?: number;
  height_cm?: number;
  declared_value?: number;
  contents_description: string;
  service_type: "EXPRESS" | "PRIORITY" | "STANDARD" | "ECONOMY";
  payment_mode: "PREPAID" | "COD";
  cod_amount?: number;
  reference_number?: string;
  instructions?: string;
  is_fragile?: boolean;
  pickup_date: string;
}

export interface BookingListParams {
  page?: number;
  page_size?: number;
  status?: string;
  from_date?: string;
  to_date?: string;
}

export interface PriceCalcPayload {
  sender_pincode: string;
  receiver_pincode: string;
  weight_kg: number;
  length_cm?: number;
  width_cm?: number;
  height_cm?: number;
  service_type: string;
  payment_mode: string;
  declared_value?: number;
  cod_amount?: number;
}

export interface AddressPayload {
  label?: string;
  name: string;
  phone: string;
  email?: string;
  address_line1: string;
  address_line2?: string;
  city: string;
  state: string;
  pincode: string;
  is_default?: boolean;
}

export interface RazorpayVerifyPayload {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export default api;
