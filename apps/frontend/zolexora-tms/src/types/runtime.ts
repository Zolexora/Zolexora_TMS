export type ApplicationType = 'STANDARD' | 'CONFIGURED' | 'EXTENDED' | 'CUSTOM';

export interface RuntimeApplicationInfo {
  id: string;
  name: string;
  type: ApplicationType;
  version: string;
  status: string;
}

export interface RuntimeBranding {
  application_name: string;
  logo_url?: string | null;
  theme: Record<string, any>;
}

export interface RuntimeAction {
  name: string;
  enabled: boolean;
}

export interface RuntimePage {
  name: string;
  enabled: boolean;
  actions: Record<string, RuntimeAction>;
}

export interface RuntimeModule {
  name: string;
  enabled: boolean;
  pages: Record<string, RuntimePage>;
}

export interface RuntimeConfiguration {
  application: RuntimeApplicationInfo;
  branding: RuntimeBranding;
  modules: Record<string, RuntimeModule>;
  features: Record<string, any>;
  navigation: Record<string, any>[];
  terminology: Record<string, string>;
  forms: Record<string, any[]>;
  workflows: Record<string, any[]>;
  rules: Record<string, any[]>;
  approvals: Record<string, any[]>;
  dashboard: Record<string, any>;
  reports: Record<string, any>;
  notifications: Record<string, any>;
  documents: Record<string, any>;
  numbering: Record<string, any>;
  extensions: Record<string, any>;
}
