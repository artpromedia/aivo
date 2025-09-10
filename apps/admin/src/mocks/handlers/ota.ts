import { http, HttpResponse } from 'msw';

/**
 * OTA (Over-the-Air Update) MSW Handlers
 */

const mockOTAUpdates = [
  {
    id: 'update_001',
    version: '2.1.0',
    description: 'Bug fixes and performance improvements',
    release_notes:
      'Fixed rendering issues, improved battery life, added new features.',
    file_url: 'https://cdn.example.com/firmware/v2.1.0.bin',
    file_size: 1048576,
    checksum: 'sha256:abc123def456',
    target_device_types: ['tablet', 'chromebook'],
    canary_percentage: 5,
    early_percentage: 25,
    broad_percentage: 75,
    production_percentage: 100,
    status: 'active',
    created_at: '2024-09-01T10:00:00Z',
    deployment_stats: {
      total_devices: 1000,
      successful: 750,
      failed: 25,
      in_progress: 225,
    },
  },
  {
    id: 'update_002',
    version: '2.0.5',
    description: 'Security patch update',
    release_notes: 'Critical security fixes for CVE-2024-1234.',
    file_url: 'https://cdn.example.com/firmware/v2.0.5.bin',
    file_size: 524288,
    checksum: 'sha256:def456ghi789',
    target_device_types: ['tablet'],
    canary_percentage: 5,
    early_percentage: 25,
    broad_percentage: 75,
    production_percentage: 100,
    status: 'completed',
    created_at: '2024-08-15T14:30:00Z',
    deployment_stats: {
      total_devices: 500,
      successful: 495,
      failed: 5,
      in_progress: 0,
    },
  },
] as Array<{
  id: string;
  version: string;
  description: string;
  release_notes: string;
  file_url: string;
  file_size: number;
  checksum: string;
  target_device_types: string[];
  canary_percentage: number;
  early_percentage: number;
  broad_percentage: number;
  production_percentage: number;
  status: string;
  created_at: string;
  deployment_stats: {
    total_devices: number;
    successful: number;
    failed: number;
    in_progress: number;
  };
}>;

export const otaHandlers = [
  // Get OTA updates
  http.get('http://localhost:8000/device-ota-svc/updates', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '20');
    const status = url.searchParams.get('status');

    let filteredUpdates = [...mockOTAUpdates];

    if (status) {
      filteredUpdates = filteredUpdates.filter(u => u.status === status);
    }

    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedUpdates = filteredUpdates.slice(startIndex, endIndex);

    return HttpResponse.json({
      updates: paginatedUpdates,
      total: filteredUpdates.length,
      page,
      limit,
      pages: Math.ceil(filteredUpdates.length / limit),
    });
  }),

  // Create OTA update
  http.post(
    'http://localhost:8000/device-ota-svc/updates',
    async ({ request }) => {
      const body = (await request.json()) as {
        version: string;
        description: string;
        release_notes: string;
        file_url: string;
        file_size: number;
        checksum: string;
        target_device_types: string;
        canary_percentage: number;
        early_percentage: number;
        broad_percentage: number;
        production_percentage: number;
      };

      const newUpdate = {
        id: `update_${Date.now()}`,
        version: body.version,
        description: body.description,
        release_notes: body.release_notes,
        file_url: body.file_url,
        file_size: body.file_size,
        checksum: body.checksum,
        target_device_types: body.target_device_types
          .split(',')
          .map(t => t.trim()),
        canary_percentage: body.canary_percentage,
        early_percentage: body.early_percentage,
        broad_percentage: body.broad_percentage,
        production_percentage: body.production_percentage,
        status: 'draft',
        created_at: new Date().toISOString(),
        deployment_stats: {
          total_devices: 0,
          successful: 0,
          failed: 0,
          in_progress: 0,
        },
      };

      mockOTAUpdates.push(newUpdate);

      return HttpResponse.json(newUpdate, { status: 201 });
    }
  ),

  // Get update progress
  http.get(
    'http://localhost:8000/device-ota-svc/updates/:updateId/progress',
    ({ params }) => {
      const update = mockOTAUpdates.find(u => u.id === params.updateId);

      if (!update) {
        return new HttpResponse(null, { status: 404 });
      }

      return HttpResponse.json({
        update_id: params.updateId,
        progress: {
          canary: {
            total: 50,
            successful: 48,
            failed: 1,
            in_progress: 1,
          },
          early: {
            total: 250,
            successful: 240,
            failed: 5,
            in_progress: 5,
          },
          broad: {
            total: 750,
            successful: 700,
            failed: 20,
            in_progress: 30,
          },
          production: {
            total: 1000,
            successful: 950,
            failed: 25,
            in_progress: 25,
          },
        },
      });
    }
  ),

  // Deploy update
  http.post(
    'http://localhost:8000/device-ota-svc/updates/:updateId/deploy',
    ({ params }) => {
      const update = mockOTAUpdates.find(u => u.id === params.updateId);

      if (update) {
        update.status = 'active';
      }

      return HttpResponse.json({
        update_id: params.updateId,
        deployment_id: `deployment_${Date.now()}`,
        status: 'initiated',
      });
    }
  ),

  // Pause/Resume update
  http.post(
    'http://localhost:8000/device-ota-svc/updates/:updateId/pause',
    ({ params }) => {
      const update = mockOTAUpdates.find(u => u.id === params.updateId);

      if (update) {
        update.status = 'paused';
      }

      return HttpResponse.json({ success: true });
    }
  ),

  http.post(
    'http://localhost:8000/device-ota-svc/updates/:updateId/resume',
    ({ params }) => {
      const update = mockOTAUpdates.find(u => u.id === params.updateId);

      if (update) {
        update.status = 'active';
      }

      return HttpResponse.json({ success: true });
    }
  ),
];
