export type UserRole = "client" | "worker" | "admin";

export interface User {
  id: number;
  full_name: string;
  email: string;
  phone: string | null;
  role: UserRole;
  is_blocked: boolean;
  created_at: string;
  /** Present on GET /admin/workers */
  assigned_parking_ids?: number[];
}

export type WorkMode = "manual" | "ai";
export type SpotStatus = "free" | "reserved" | "occupied" | "inactive";

export interface Parking {
  id: number;
  name: string;
  city: string;
  address: string;
  capacity: number;
  latitude: number;
  longitude: number;
  work_mode: WorkMode;
  created_at: string;
}

export interface TariffNested {
  id: number;
  price_per_hour: string;
}

export interface ParkingDetail extends Parking {
  tariffs: TariffNested[];
}

export interface ParkingSpot {
  id: number;
  parking_id: number;
  code: string;
  status: SpotStatus;
}

export type BookingStatus = "created" | "paid" | "canceled" | "expired" | "used";

export interface Booking {
  id: number;
  user_id: number;
  vehicle_id: number;
  parking_id: number;
  spot_id: number;
  tariff_id: number;
  planned_start_time: string;
  planned_end_time: string;
  status: BookingStatus;
  created_at: string;
}

export interface PaymentInfo {
  id: number;
  amount: string;
  status: string;
  paid_at: string | null;
}

export interface BookingWithPayments extends Booking {
  payments: PaymentInfo[];
}

export interface Vehicle {
  id: number;
  user_id: number;
  plate_number: string;
  brand: string | null;
  model: string | null;
  color: string | null;
}

export interface WorkerSpotBoardItem {
  spot: ParkingSpot;
  vehicle: Vehicle | null;
  booking: BookingWithPayments | null;
  session: ParkingSession | null;
  overstay_minutes: number | null;
}

export interface Tariff {
  id: number;
  parking_id: number;
  price_per_hour: string;
}

export interface AdminStats {
  parkings_count: number;
  spots_total: number;
  bookings_total: number;
  active_sessions: number;
  revenue_today: string;
}

export interface BarrierLog {
  id: number;
  parking_id: number;
  vehicle_id: number | null;
  worker_id: number | null;
  action: "open" | "close";
  created_at: string;
}

export interface AiLog {
  id: number;
  parking_id: number;
  vehicle_id: number | null;
  recognized_plate: string;
  access_allowed: boolean;
  created_at: string;
}

export interface ParkingSession {
  id: number;
  booking_id: number;
  entry_time: string;
  exit_time: string | null;
  total_price: string | null;
  status: "active" | "completed";
}

export interface WorkerEntryRequest {
  parking_id: number;
  plate_number: string;
}

export interface WorkerExitRequest {
  session_id: number;
}
