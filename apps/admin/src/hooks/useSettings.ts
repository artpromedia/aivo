import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Settings API endpoints
const SETTINGS_API_BASE = '/admin/settings';

// Types for settings
export interface OrgSettings {
  brand_name?: string;
  logo_url?: string;
  primary_color?: string;
  support_email?: string;
  website_url?: string;
  privacy_policy_url?: string;
  terms_of_service_url?: string;
}

export interface LocaleSettings {
  default_locale?: string;
  time_zone?: string;
  date_format?: string;
  currency?: string;
  grade_scheme?: string;
  first_day_of_week?: number;
}

export interface ResidencySettings {
  region?: string;
  processing_purposes?: string[];
  data_retention_days?: number;
  cross_border_transfer?: boolean;
  compliance_framework?: string;
}

export interface ConsentSettings {
  media_default?: boolean;
  analytics_opt_in?: boolean;
  retention_days?: number;
  parental_consent_required?: boolean;
  consent_expiry_days?: number;
  withdrawal_process?: string;
}

export interface SettingsResponse {
  id: string;
  settings: Record<string, unknown>;
  updated_by: string;
  updated_at: string;
}

export interface AllSettings {
  org: OrgSettings;
  locale: LocaleSettings;
  residency: ResidencySettings;
  consent: ConsentSettings;
}

// API functions
const settingsApi = {
  // Organization settings
  getOrgSettings: async (): Promise<SettingsResponse> => {
    const response = await fetch(`${SETTINGS_API_BASE}/org`);
    if (!response.ok) throw new Error('Failed to get organization settings');
    return response.json();
  },

  updateOrgSettings: async (
    settings: Partial<OrgSettings>
  ): Promise<SettingsResponse> => {
    const response = await fetch(`${SETTINGS_API_BASE}/org`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error('Failed to update organization settings');
    return response.json();
  },

  // Locale settings
  getLocaleSettings: async (): Promise<SettingsResponse> => {
    const response = await fetch(`${SETTINGS_API_BASE}/locale`);
    if (!response.ok) throw new Error('Failed to get locale settings');
    return response.json();
  },

  updateLocaleSettings: async (
    settings: Partial<LocaleSettings>
  ): Promise<SettingsResponse> => {
    const response = await fetch(`${SETTINGS_API_BASE}/locale`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error('Failed to update locale settings');
    return response.json();
  },

  // Residency settings
  getResidencySettings: async (): Promise<SettingsResponse> => {
    const response = await fetch(`${SETTINGS_API_BASE}/residency`);
    if (!response.ok) throw new Error('Failed to get residency settings');
    return response.json();
  },

  updateResidencySettings: async (
    settings: Partial<ResidencySettings>
  ): Promise<SettingsResponse> => {
    const response = await fetch(`${SETTINGS_API_BASE}/residency`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error('Failed to update residency settings');
    return response.json();
  },

  // Consent settings
  getConsentSettings: async (): Promise<SettingsResponse> => {
    const response = await fetch(`${SETTINGS_API_BASE}/consent`);
    if (!response.ok) throw new Error('Failed to get consent settings');
    return response.json();
  },

  updateConsentSettings: async (
    settings: Partial<ConsentSettings>
  ): Promise<SettingsResponse> => {
    const response = await fetch(`${SETTINGS_API_BASE}/consent`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error('Failed to update consent settings');
    return response.json();
  },

  // All settings
  getAllSettings: async (): Promise<AllSettings> => {
    const response = await fetch(`${SETTINGS_API_BASE}/all`);
    if (!response.ok) throw new Error('Failed to get all settings');
    return response.json();
  },
};

// React Query hooks
export const useOrgSettings = () => {
  return useQuery({
    queryKey: ['settings', 'org'],
    queryFn: settingsApi.getOrgSettings,
  });
};

export const useUpdateOrgSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: settingsApi.updateOrgSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'org'] });
      queryClient.invalidateQueries({ queryKey: ['settings', 'all'] });
    },
  });
};

export const useLocaleSettings = () => {
  return useQuery({
    queryKey: ['settings', 'locale'],
    queryFn: settingsApi.getLocaleSettings,
  });
};

export const useUpdateLocaleSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: settingsApi.updateLocaleSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'locale'] });
      queryClient.invalidateQueries({ queryKey: ['settings', 'all'] });
    },
  });
};

export const useResidencySettings = () => {
  return useQuery({
    queryKey: ['settings', 'residency'],
    queryFn: settingsApi.getResidencySettings,
  });
};

export const useUpdateResidencySettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: settingsApi.updateResidencySettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'residency'] });
      queryClient.invalidateQueries({ queryKey: ['settings', 'all'] });
    },
  });
};

export const useConsentSettings = () => {
  return useQuery({
    queryKey: ['settings', 'consent'],
    queryFn: settingsApi.getConsentSettings,
  });
};

export const useUpdateConsentSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: settingsApi.updateConsentSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'consent'] });
      queryClient.invalidateQueries({ queryKey: ['settings', 'all'] });
    },
  });
};

export const useAllSettings = () => {
  return useQuery({
    queryKey: ['settings', 'all'],
    queryFn: settingsApi.getAllSettings,
  });
};
