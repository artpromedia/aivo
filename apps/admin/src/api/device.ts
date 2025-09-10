import { apiRequest } from './base';

export interface Device {
  id: string;
  serial_number: string;
  device_type: string;
  status: 'online' | 'offline' | 'pending' | 'error';
  last_seen: string;
  firmware_version: string;
  hardware_version: string;
  location?: string;
  enrolled_at: string;
  enrollment_status: 'pending' | 'approved' | 'rejected';
}

export interface DeviceEnrollment {
  serial_number: string;
  device_type: string;
  location?: string;
  metadata?: Record<string, unknown>;
}

export interface DevicePolicyAssignment {
  device_id: string;
  policy_id: string;
  assigned_at: string;
}

export class DeviceAPI {
  static async getDevices(params?: {
    page?: number;
    limit?: number;
    status?: string;
    device_type?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.status) queryParams.set('status', params.status);
    if (params?.device_type) queryParams.set('device_type', params.device_type);

    return apiRequest<{
      devices: Device[];
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/devices?${queryParams.toString()}`);
  }

  static async getDevice(deviceId: string) {
    return apiRequest<Device>(`/admin/devices/${deviceId}`);
  }

  static async enrollDevice(enrollment: DeviceEnrollment) {
    return apiRequest<Device>('/admin/devices/enroll', {
      method: 'POST',
      body: JSON.stringify(enrollment),
    });
  }

  static async approveEnrollment(deviceId: string) {
    return apiRequest<Device>(`/admin/devices/${deviceId}/approve`, {
      method: 'POST',
    });
  }

  static async rejectEnrollment(deviceId: string, reason?: string) {
    return apiRequest<Device>(`/admin/devices/${deviceId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  static async deactivateDevice(deviceId: string) {
    return apiRequest<void>(`/admin/devices/${deviceId}/deactivate`, {
      method: 'POST',
    });
  }

  static async getDeviceHeartbeats(deviceId: string, limit = 50) {
    return apiRequest<{
      heartbeats: Array<{
        timestamp: string;
        battery_level: number;
        network_strength: number;
        storage_usage: number;
        app_version: string;
        location?: { lat: number; lng: number };
      }>;
    }>(`/admin/devices/${deviceId}/heartbeats?limit=${limit}`);
  }
}
