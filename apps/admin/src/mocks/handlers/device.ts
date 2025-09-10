import { http, HttpResponse } from 'msw';

/**
 * Device Management MSW Handlers
 */

const mockDevices = [
  {
    id: 'device_001',
    serial_number: 'TABLET-001',
    device_type: 'tablet',
    status: 'online',
    enrollment_status: 'approved',
    location: 'Classroom 101',
    enrolled_at: '2024-09-01T10:00:00Z',
    last_seen: '2024-09-09T08:30:00Z',
  },
  {
    id: 'device_002',
    serial_number: 'CHROMEBOOK-002',
    device_type: 'chromebook',
    status: 'offline',
    enrollment_status: 'approved',
    location: 'Lab 203',
    enrolled_at: '2024-09-02T11:00:00Z',
    last_seen: '2024-09-08T16:45:00Z',
  },
  {
    id: 'device_003',
    serial_number: 'TABLET-003',
    device_type: 'tablet',
    status: 'offline',
    enrollment_status: 'pending',
    location: null,
    enrolled_at: '2024-09-09T09:00:00Z',
    last_seen: null,
  },
] as Array<{
  id: string;
  serial_number: string;
  device_type: string;
  status: string;
  enrollment_status: string;
  location: string | null;
  enrolled_at: string;
  last_seen: string | null;
}>;

export const deviceHandlers = [
  // Get devices
  http.get('http://localhost:8000/admin/devices', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '20');
    const status = url.searchParams.get('status');
    const deviceType = url.searchParams.get('device_type');

    let filteredDevices = [...mockDevices];

    if (status) {
      filteredDevices = filteredDevices.filter(d => d.status === status);
    }

    if (deviceType) {
      filteredDevices = filteredDevices.filter(
        d => d.device_type === deviceType
      );
    }

    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedDevices = filteredDevices.slice(startIndex, endIndex);

    return HttpResponse.json({
      devices: paginatedDevices,
      total: filteredDevices.length,
      page,
      limit,
      pages: Math.ceil(filteredDevices.length / limit),
    });
  }),

  // Enroll device
  http.post(
    'http://localhost:8000/admin/devices/enroll',
    async ({ request }) => {
      const body = (await request.json()) as {
        serial_number: string;
        device_type: string;
        location?: string;
      };

      const newDevice = {
        id: `device_${Date.now()}`,
        serial_number: body.serial_number,
        device_type: body.device_type,
        status: 'offline',
        enrollment_status: 'pending',
        location: body.location || null,
        enrolled_at: new Date().toISOString(),
        last_seen: null,
      };

      mockDevices.push(newDevice);

      return HttpResponse.json(newDevice, { status: 201 });
    }
  ),

  // Approve enrollment
  http.post(
    'http://localhost:8000/admin/devices/:deviceId/approve',
    ({ params }) => {
      const device = mockDevices.find(d => d.id === params.deviceId);
      if (device) {
        device.enrollment_status = 'approved';
      }
      return HttpResponse.json({ success: true });
    }
  ),

  // Reject enrollment
  http.post(
    'http://localhost:8000/admin/devices/:deviceId/reject',
    ({ params }) => {
      const device = mockDevices.find(d => d.id === params.deviceId);
      if (device) {
        device.enrollment_status = 'rejected';
      }
      return HttpResponse.json({ success: true });
    }
  ),

  // Deactivate device
  http.post(
    'http://localhost:8000/admin/devices/:deviceId/deactivate',
    ({ params }) => {
      const device = mockDevices.find(d => d.id === params.deviceId);
      if (device) {
        device.status = 'offline';
      }
      return HttpResponse.json({ success: true });
    }
  ),
];
