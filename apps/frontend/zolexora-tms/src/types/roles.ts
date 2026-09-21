export interface RolePermission {
  module_code: string;
  page_code: string;
  action_code: string;
}

export interface RoleResponse {
  id: string;
  organisation_id: string;
  name: string;
  description: string | null;
  source: string;
  status: string;
  current_version: number;
  platform_template_id: string | null;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
  current_permissions: RolePermission[];
  member_count: number;
}

export interface PlatformTemplateResponse {
  id: string;
  code: string;
  name: string;
  description: string | null;
  version: number;
  permissions: RolePermission[];
}

export interface MemberWithRoleResponse {
  member_id: string;
  user_id: string;
  organisation_id: string;
  status: string;
  is_commander: boolean;
  is_creator: boolean;
  role_id: string | null;
  role_name: string | null;
  role_status: string | null;
  created_at: string;
}

export interface EffectivePermissionsResponse {
  user_id: string;
  organisation_id: string;
  is_commander: boolean;
  role_id: string | null;
  role_name: string | null;
  role_version: number | null;
  permissions: string[];
  modules: Record<string, Record<string, string[]>>;
}

export interface AssignRoleRequest {
  role_id: string | null;
}

export interface OverrideCreateRequest {
  override_type: 'GRANT' | 'RESTRICT';
  module_code: string;
  page_code: string;
  action_code: string;
  reason?: string;
}

export interface OverrideResponse {
  id: string;
  member_id: string;
  override_type: string;
  module_code: string;
  page_code: string;
  action_code: string;
  reason: string | null;
}

export interface RoleCreateRequest {
  name: string;
  description?: string;
  permissions: RolePermission[];
  platform_template_id?: string;
  change_note?: string;
}

export interface RoleUpdateRequest {
  name?: string;
  description?: string;
  permissions?: RolePermission[];
  change_note?: string;
}

export interface ActionSchema {
  code: string;
  name: string;
}

export interface PageSchema {
  code: string;
  name: string;
  actions: ActionSchema[];
}

export interface ModuleSchema {
  code: string;
  name: string;
  pages: PageSchema[];
}

export interface CapabilityRegistryResponse {
  code: string;
  name: string;
  modules: ModuleSchema[];
}
