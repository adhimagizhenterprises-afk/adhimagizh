/**
 * Redux Toolkit store — SwiftShip Customer Portal
 */
import { configureStore, createSlice, createAsyncThunk, PayloadAction } from "@reduxjs/toolkit";
import { authApi } from "../services/api";

// ─── Auth Slice ───────────────────────────────────────────────────────────────
interface AuthState {
  user: { id: string; name: string; email: string; phone: string; role: string } | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

const initialAuthState: AuthState = {
  user: null,
  token: localStorage.getItem("access_token"),
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  "auth/login",
  async ({ username, password }: { username: string; password: string }, { rejectWithValue }) => {
    try {
      const res = await authApi.login(username, password);
      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("refresh_token", res.data.refresh_token);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || "Login failed");
    }
  }
);

export const register = createAsyncThunk(
  "auth/register",
  async (
    data: { name: string; email: string; phone: string; password: string },
    { rejectWithValue }
  ) => {
    try {
      const res = await authApi.register(data);
      return res.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || "Registration failed");
    }
  }
);

const authSlice = createSlice({
  name: "auth",
  initialState: initialAuthState,
  reducers: {
    logout(state) {
      state.user = null;
      state.token = null;
      localStorage.clear();
    },
    setUser(state, action: PayloadAction<AuthState["user"]>) {
      state.user = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload.access_token;
        state.user = action.payload.user;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(register.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(register.fulfilled, (state) => { state.loading = false; })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  },
});

export const { logout, setUser } = authSlice.actions;

// ─── Booking Slice ────────────────────────────────────────────────────────────
interface Shipment {
  id: string;
  awb_number: string;
  status: string;
  sender_city: string;
  receiver_city: string;
  receiver_name: string;
  service_type: string;
  total_charge: number;
  created_at: string;
  expected_delivery_date: string;
}

interface BookingState {
  shipments: Shipment[];
  total: number;
  page: number;
  loading: boolean;
  selectedShipment: Shipment | null;
}

const bookingSlice = createSlice({
  name: "booking",
  initialState: { shipments: [], total: 0, page: 1, loading: false, selectedShipment: null } as BookingState,
  reducers: {
    setShipments(state, action: PayloadAction<{ items: Shipment[]; total: number; page: number }>) {
      state.shipments = action.payload.items;
      state.total = action.payload.total;
      state.page = action.payload.page;
    },
    setSelectedShipment(state, action: PayloadAction<Shipment | null>) {
      state.selectedShipment = action.payload;
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
    prependShipment(state, action: PayloadAction<Shipment>) {
      state.shipments.unshift(action.payload);
      state.total += 1;
    },
  },
});

export const { setShipments, setSelectedShipment, setLoading, prependShipment } = bookingSlice.actions;

// ─── Store ────────────────────────────────────────────────────────────────────
export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    booking: bookingSlice.reducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
