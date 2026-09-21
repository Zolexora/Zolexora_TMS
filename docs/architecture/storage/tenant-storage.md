# Tenant Storage Architecture

Zolexora TMS splits blob storage into Document Storage (Cloudflare R2) and Visual Media Storage (Cloudinary).

## Cloudflare R2
- **Bucket**: `zolexora-tms-dev` (Private)
- **Use Case**: Statutory documents (RC, Driving Licence, Insurance, PUC), Invoices, Settlements, Compliance reports.
- **Isolation**: Objects are isolated via prefixes: `organisations/{organisation_id}/...`
- **Future Integration**: Metadata indexing via R2 Data Catalog for analytics.

## Cloudinary
- **Use Case**: Visual media requiring edge transformations (Logos, Profile photos, Thumbnails).
- **Isolation**: `zolexora/organisations/{organisation_id}/...`
- **Security**: Credentials remain strictly on the backend. No frontend direct uploads without signed payloads.
