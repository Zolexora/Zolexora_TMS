---
name: cloudinary-cli
description: Use when managing Cloudinary media, running the Cloudinary CLI (`cld`), querying Admin/Upload APIs, managing folders and tags, running AI agent commands (`cld agent`), or generating URLs from the terminal.
---

# Cloudinary CLI (`cld`) Skill

The official Cloudinary Command Line Interface (`cld`) provides terminal and agent access to Cloudinary's Upload API, Admin API, Provisioning API, and media workflows.

## Prerequisites & Authentication

Ensure Cloudinary credentials are set in the environment or configured via `cld config`:
- `CLOUDINARY_URL`: `cloudinary://<API_KEY>:<API_SECRET>@<CLOUD_NAME>`
- Or separate variables: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

Verify configuration:
```bash
cld config
```

## Common Workflows

### 1. Uploading Assets
- **Upload single file**:
  ```bash
  cld uploader upload /path/to/asset.png public_id=my_asset folder=products
  ```
- **Upload directory maintaining folder hierarchy**:
  ```bash
  cld upload_dir /path/to/images -f remote_folder_name
  ```
- **Sync local folder with remote Cloudinary folder**:
  ```bash
  cld sync --push /path/to/images remote_folder_name
  ```

### 2. Search & Retrieval
- **Search assets using Lucene query expressions**:
  ```bash
  cld search "resource_type:image AND tags=hero"
  ```
- **List and search folders**:
  ```bash
  cld search_folders "name:products"
  ```

### 3. Deleting Assets
- **Delete asset by public ID**:
  ```bash
  cld uploader destroy my_asset invalidate=True
  ```

### 4. URL & Transformation Generation
- **Generate Cloudinary delivery URL with transformations**:
  ```bash
  cld url my_asset -t w_500,c_fill,q_auto,f_auto
  ```

### 5. AI Agent Commands
- **Agent automated signup**:
  ```bash
  cld agent signup
  ```
  Commands specifically designated for autonomous agents operating on behalf of a user.

### 6. Widget & Template Generation
- **Generate widget implementation template**:
  ```bash
  cld make upload_widget
  ```
