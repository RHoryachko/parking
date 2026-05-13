export type UserRole = "client" | "worker" | "admin";

export interface User {
  id: number;
  full_name: string;
  email: string;
  phone: string | null;
  role: UserRole;
  is_blocked: boolean;
  created_at: string;
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
