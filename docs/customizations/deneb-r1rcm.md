# Deneb - R1 RCM Global Private Limited

## Entities
- **Organisation (Tenant):** Deneb
- **Customer:** R1 RCM Global Private Limited

## Locations
- GGN Sec-21
- Tikri
- Sec-48 GGN
- Hyderabad
- Chennai

## Workflow Overview
R1 RCM uses a bulk Excel import workflow to generate bookings. The workflow strictly separates the Excel upload from the authoritative Booking record.

**Lifecycle:**
1. Upload Excel
2. Read & Map Columns
3. Validate (Identify duplicates, missing employees, missing vehicles, missing vendors)
4. Preview Validation Results (Errors vs Warnings)
5. User Confirmation
6. System generates normalized Booking, Trip, and Duty records in D1.

## Roles & Access Control
**Role:** `OPERATIONS_SUPERVISOR`
- Allowed: `route.view`, `route.import`, `booking.view`, `booking.create`, `booking.edit`, `vehicle.view`, `vehicle.assign`, `driver.view`, `driver.assign`, `duty.view`, `duty.dispatch`, `duty.track`, `duty.complete`, `duty.cancel`, `trip.view`, `exception.view`, `compliance.view`
- Denied: `invoice.create`, `invoice.approve`, `payment.record`, `payment.allocate`, `organisation.settings`, other customer data, other location data.

Access is strictly scoped by `customer_id` and `location`. Backend API verifies these parameters against the authenticated user's assigned scopes before interacting with D1.

## Rules & Configuration
- **Penalties:** Delay > 30 mins, rash driving, vehicle damage, missing uniform.
- **Deductions:** Mapped to Trip Cancellation, No Show, SLA Deduction, Rate Difference.
- **Billing:** Rate card matching based on `vehicle_type`, `route_number`, and `cab_type`.

## Extensions
- Excel Parser Service (`r1rcm_import`) for extracting specific columns.
- R1 Duty validation wrapper around core `duties.service`.
