import { apiRequest } from './base';

export interface FirmwareUpdate {
  id: string;
  version: string;
  description: string;
  release_notes: string;
  file_url: string;
  file_size: number;
  checksum: string;
  target_device_types: string[];
  deployment_config: {
    canary_percentage: number;
    early_percentage: number;
    broad_percentage: number;
    production_percentage: number;
  };
  rollout_status: {
    canary: { deployed: number; successful: number; failed: number };
    early: { deployed: number; successful: number; failed: number };
    broad: { deployed: number; successful: number; failed: number };
    production: { deployed: number; successful: number; failed: number };
  };
  created_at: string;
  is_active: boolean;
}

export interface UpdateProgress {
  device_id: string;
  update_id: string;
  status: 'pending' | 'downloading' | 'installing' | 'completed' | 'failed';
  progress_percentage: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface CreateFirmwareUpdateRequest {
  version: string;
  description: string;
  release_notes: string;
  file_url: string;
  file_size: number;
  checksum: string;
  target_device_types: string[];
  deployment_config: {
    canary_percentage: number;
    early_percentage: number;
    broad_percentage: number;
    production_percentage: number;
  };
}

export interface DeploymentRequest {
  update_id: string;
  ring: 'canary' | 'early' | 'broad' | 'production';
  device_ids?: string[];
}

export class OTAAPI {
  static async getFirmwareUpdates(params?: {
    page?: number;
    limit?: number;
    is_active?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.is_active !== undefined)
      queryParams.set('is_active', params.is_active.toString());

    return apiRequest<{
      updates: FirmwareUpdate[];
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/firmware/updates?${queryParams.toString()}`);
  }

  static async getFirmwareUpdate(updateId: string) {
    return apiRequest<FirmwareUpdate>(`/admin/firmware/updates/${updateId}`);
  }

  static async createFirmwareUpdate(update: CreateFirmwareUpdateRequest) {
    return apiRequest<FirmwareUpdate>('/admin/firmware/updates', {
      method: 'POST',
      body: JSON.stringify(update),
    });
  }

  static async deployUpdate(deployment: DeploymentRequest) {
    return apiRequest<{
      deployment_id: string;
      devices_targeted: number;
    }>(`/admin/firmware/updates/${deployment.update_id}/deploy`, {
      method: 'POST',
      body: JSON.stringify({
        ring: deployment.ring,
        device_ids: deployment.device_ids,
      }),
    });
  }

  static async rollbackUpdate(updateId: string, ring?: string) {
    return apiRequest<{
      rollback_id: string;
      devices_affected: number;
    }>(`/admin/firmware/updates/${updateId}/rollback`, {
      method: 'POST',
      body: JSON.stringify({ ring }),
    });
  }

  static async getRolloutStatus(updateId: string) {
    return apiRequest<FirmwareUpdate['rollout_status']>(
      `/admin/firmware/updates/${updateId}/rollout-status`
    );
  }

  static async getUpdateProgress(updateId: string) {
    return apiRequest<{
      progress: UpdateProgress[];
    }>(`/admin/firmware/updates/${updateId}/progress`);
  }

  static async getDeviceUpdates(deviceId: string) {
    return apiRequest<{
      updates: UpdateProgress[];
    }>(`/admin/devices/${deviceId}/updates`);
  }

  static async pauseUpdate(updateId: string) {
    return apiRequest<void>(`/admin/firmware/updates/${updateId}/pause`, {
      method: 'POST',
    });
  }

  static async resumeUpdate(updateId: string) {
    return apiRequest<void>(`/admin/firmware/updates/${updateId}/resume`, {
      method: 'POST',
    });
  }
}
