export interface Organisation {
  id: string;
  name: string;
  organisation_type: string;
  status: 'ACTIVE' | 'SUSPENDED' | 'ARCHIVED';
  created_at: string;
  updated_at: string;
}

export interface AuthMeResponse {
  user_id: string;
  email: string | null;
  organisation_id: string | null;
  role_code: string | null;
  permissions: string[];
}

export interface OrganisationMember {
  id: string;
  organisation_id: string;
  user_id: string;
  role_code: string;
  role_name: string;
  status: 'ACTIVE' | 'INVITED' | 'SUSPENDED';
  created_at: string;
}

export interface InviteMemberRequest {
  email: string;
  role_code: 'ADMIN' | 'DISPATCHER' | 'DRIVER' | 'VIEWER';
}

export interface Customer {
  id: string;
  organisation_id: string;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  billing_address?: string;
  gstin?: string;
  pan?: string;
  payment_terms_days: number;
  credit_limit: string;
  status: 'ACTIVE' | 'INACTIVE';
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  billing_address?: string;
  gstin?: string;
  pan?: string;
  payment_terms_days?: number;
  credit_limit?: string;
  notes?: string;
}

export interface Vendor {
  id: string;
  organisation_id: string;
  name: string;
  vendor_type: 'FLEET_SUPPLIER' | 'WORKSHOP' | 'FUEL_PARTNER' | 'BROKER' | 'OTHER';
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  gstin?: string;
  pan?: string;
  bank_account_name?: string;
  bank_account_number?: string;
  bank_ifsc?: string;
  bank_name?: string;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
  updated_at: string;
}

export interface VendorCreate {
  name: string;
  vendor_type: 'FLEET_SUPPLIER' | 'WORKSHOP' | 'FUEL_PARTNER' | 'BROKER' | 'OTHER';
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  gstin?: string;
  pan?: string;
  bank_account_name?: string;
  bank_account_number?: string;
  bank_ifsc?: string;
  bank_name?: string;
}

export interface Driver {
  id: string;
  organisation_id: string;
  vendor_id?: string;
  full_name: string;
  phone: string;
  alternate_phone?: string;
  email?: string;
  license_number: string;
  license_type: string;
  license_expiry?: string;
  badge_number?: string;
  aadhaar_last4?: string;
  pan?: string;
  driver_type: 'PERMANENT' | 'CONTRACT' | 'MARKET';
  status: 'AVAILABLE' | 'ON_DUTY' | 'ON_LEAVE' | 'INACTIVE';
  avatar_url?: string;
  documents: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface DriverCreate {
  vendor_id?: string;
  full_name: string;
  phone: string;
  alternate_phone?: string;
  email?: string;
  license_number: string;
  license_type?: string;
  license_expiry?: string;
  badge_number?: string;
  aadhaar_last4?: string;
  pan?: string;
  driver_type?: 'PERMANENT' | 'CONTRACT' | 'MARKET';
}

export interface Vehicle {
  id: string;
  organisation_id: string;
  vendor_id?: string;
  registration_number: string;
  vehicle_type: 'TRUCK' | 'TRAILER' | 'CONTAINER' | 'TANKER' | 'TIPPER' | 'TEMPO' | 'PICKUP' | 'OTHER';
  ownership_type: 'OWNED' | 'LEASED' | 'ATTACHED';
  make?: string;
  model?: string;
  year?: number;
  fuel_type: 'DIESEL' | 'CNG' | 'ELECTRIC' | 'PETROL';
  payload_capacity_kg?: string;
  volume_cft?: string;
  odometer_km: string;
  fastag_id?: string;
  gps_device_id?: string;
  rc_number?: string;
  rc_expiry?: string;
  fitness_expiry?: string;
  permit_expiry?: string;
  insurance_expiry?: string;
  puc_expiry?: string;
  status: 'AVAILABLE' | 'ON_DUTY' | 'MAINTENANCE' | 'DECOMMISSIONED';
  documents: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface VehicleCreate {
  vendor_id?: string;
  registration_number: string;
  vehicle_type: 'TRUCK' | 'TRAILER' | 'CONTAINER' | 'TANKER' | 'TIPPER' | 'TEMPO' | 'PICKUP' | 'OTHER';
  ownership_type: 'OWNED' | 'LEASED' | 'ATTACHED';
  make?: string;
  model?: string;
  year?: number;
  fuel_type?: 'DIESEL' | 'CNG' | 'ELECTRIC' | 'PETROL';
  payload_capacity_kg?: string;
  volume_cft?: string;
  odometer_km?: string;
  fastag_id?: string;
  gps_device_id?: string;
  rc_number?: string;
}

// -------------------------------------------------------------
// Phase 4: Core Operational Engine Types
// -------------------------------------------------------------

export type BookingType =
  | 'ETS'
  | 'SPOT'
  | 'FIXED'
  | 'RENTAL'
  | 'AIRPORT'
  | 'LOCAL'
  | 'OUTSTATION'
  | 'CORPORATE'
  | 'CONTRACT'
  | 'RECURRING';

export type BookingServiceType = 'PASSENGER' | 'CARGO';

export type BookingRequestStatus = 'DRAFT' | 'REQUESTED' | 'CONFIRMED' | 'CANCELLED';

export type BookingOperationalStatus = 'CONFIRMED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export type DutyLifecycleStatus =
  | 'ALLOCATED'
  | 'DISPATCHED'
  | 'ARRIVED_PICKUP'
  | 'IN_TRANSIT'
  | 'ARRIVED_DROP'
  | 'DUTY_COMPLETED'
  | 'CANCELLED';

export type TripLifecycleStatus = 'NOT_STARTED' | 'IN_TRANSIT' | 'COMPLETED' | 'CANCELLED';

export interface BookingRequest {
  id: string;
  request_number: string;
  organisation_id: string;
  customer_id: string;
  booking_type: BookingType;
  service_type: BookingServiceType;
  pickup_address: string;
  pickup_lat?: number;
  pickup_lng?: number;
  drop_address: string;
  drop_lat?: number;
  drop_lng?: number;
  pickup_datetime: string;
  expected_completion_datetime?: string;
  passenger_info: Record<string, any>;
  cargo_info: Record<string, any>;
  vehicle_requirements: Record<string, any>;
  special_instructions?: string;
  source: string;
  estimated_pricing?: string;
  status: BookingRequestStatus;
  created_at: string;
  updated_at: string;
}

export interface BookingRequestCreate {
  customer_id: string;
  booking_type?: BookingType;
  service_type?: BookingServiceType;
  pickup_address: string;
  drop_address: string;
  pickup_datetime: string;
  expected_completion_datetime?: string;
  passenger_info?: Record<string, any>;
  cargo_info?: Record<string, any>;
  vehicle_requirements?: Record<string, any>;
  special_instructions?: string;
  estimated_pricing?: string;
}

export interface Booking {
  id: string;
  booking_number: string;
  booking_request_id?: string;
  organisation_id: string;
  customer_id: string;
  booking_type: BookingType;
  service_type: BookingServiceType;
  pickup_address: string;
  pickup_lat?: number;
  pickup_lng?: number;
  drop_address: string;
  drop_lat?: number;
  drop_lng?: number;
  pickup_datetime: string;
  expected_completion_datetime?: string;
  passenger_info: Record<string, any>;
  cargo_info: Record<string, any>;
  vehicle_requirements: Record<string, any>;
  driver_requirements: Record<string, any>;
  status: BookingOperationalStatus;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface BookingCreate {
  customer_id: string;
  booking_type?: BookingType;
  service_type?: BookingServiceType;
  pickup_address: string;
  drop_address: string;
  pickup_datetime: string;
  expected_completion_datetime?: string;
  passenger_info?: Record<string, any>;
  cargo_info?: Record<string, any>;
  vehicle_requirements?: Record<string, any>;
  driver_requirements?: Record<string, any>;
  operational_instructions?: string;
}

export interface Duty {
  id: string;
  duty_number: string;
  organisation_id: string;
  booking_id: string;
  driver_id?: string;
  vehicle_id?: string;
  scheduled_start_time: string;
  scheduled_end_time: string;
  actual_start_time?: string;
  actual_end_time?: string;
  status: DutyLifecycleStatus;
  notes?: string;
  dispatched_at?: string;
  dispatched_by_user_id?: string;
  created_at: string;
  updated_at: string;
}

export interface DutyCreate {
  booking_id: string;
  scheduled_start_time: string;
  scheduled_end_time: string;
  driver_id?: string;
  vehicle_id?: string;
  notes?: string;
}

export interface DutyAssignRequest {
  driver_id: string;
  vehicle_id: string;
}

export interface TripStartRequest {
  start_odometer: number | string;
  start_location?: Record<string, any>;
}

export interface TripCompleteRequest {
  end_odometer: number | string;
  end_location?: Record<string, any>;
  toll_amount?: number | string;
  fuel_amount?: number | string;
  parking_amount?: number | string;
  waiting_minutes?: number;
  pod_attachment_url?: string;
  pod_notes?: string;
  notes?: string;
}

export interface Trip {
  id: string;
  trip_number: string;
  organisation_id: string;
  duty_id: string;
  driver_id: string;
  vehicle_id: string;
  start_odometer: string;
  end_odometer?: string;
  total_distance_km?: string;
  start_timestamp?: string;
  end_timestamp?: string;
  start_location: Record<string, any>;
  end_location: Record<string, any>;
  toll_amount: string;
  fuel_amount: string;
  parking_amount: string;
  waiting_minutes: number;
  status: TripLifecycleStatus;
  pod_attachment_url?: string;
  pod_notes?: string;
  operational_receipts: Array<Record<string, any>>;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface DispatchBoardItem {
  id: string;
  duty_number: string;
  booking_id: string;
  booking_number: string;
  customer_name?: string;
  driver_id?: string;
  driver_name?: string;
  driver_phone?: string;
  vehicle_id?: string;
  vehicle_registration?: string;
  vehicle_type?: string;
  pickup_address: string;
  drop_address: string;
  scheduled_start_time: string;
  scheduled_end_time: string;
  actual_start_time?: string;
  status: DutyLifecycleStatus;
}

