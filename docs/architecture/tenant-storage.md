# Tenant Storage Architecture

## Media Plane (Cloudinary)
Used exclusively for images and publicly cacheable visual media.
- Organisation Logos
- Customer/Vendor Logos
- Driver Profile Photos
- Vehicle Photos

Storage Prefix: `zolexora/organisations/{organisation_id}/...`

## Document Plane (Cloudflare R2)
Used exclusively for private, sensitive, business and legal documents.
- Compliance Documents (RC, DL, Insurance, permits)
- Financial PDFs (Invoices, Settlements)

Storage Prefix: `organisations/{organisation_id}/...`

Access is strictly controlled via temporary pre-signed URLs managed by the backend. No static public access is allowed.
