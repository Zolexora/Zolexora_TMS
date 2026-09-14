# Tenant Storage (R2 & Cloudinary)
R2 handles documents (RC, DL, Insurance, Invoices, Settlements).
Cloudinary handles visual media (logos, profile photos, thumbnails).
Both use strict isolation prefixes, e.g., `organisations/{organisation_id}/...`.
