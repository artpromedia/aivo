import { http, HttpResponse } from 'msw';

/**
 * User Management MSW Handlers
 */

const mockUsers = [
  {
    id: 'user_001',
    username: 'john.doe',
    email: 'john@example.com',
    role: 'admin',
    status: 'active',
    lastLogin: '2024-09-09T08:30:00Z',
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    id: 'user_002',
    username: 'jane.smith',
    email: 'jane.smith@example.com',
    role: 'teacher',
    status: 'active',
    lastLogin: '2024-09-08T14:20:00Z',
    createdAt: '2024-01-15T00:00:00Z',
  },
  {
    id: 'user_003',
    username: 'mike.johnson',
    email: 'mike.johnson@example.com',
    role: 'teacher',
    status: 'pending',
    lastLogin: null,
    createdAt: '2024-02-01T00:00:00Z',
  },
];

export const userHandlers = [
  // Get users
  http.get('http://localhost:8000/admin/users', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedUsers = mockUsers.slice(startIndex, endIndex);

    return HttpResponse.json({
      users: paginatedUsers,
      total: mockUsers.length,
      page,
      totalPages: Math.ceil(mockUsers.length / limit),
    });
  }),

  // Update user role
  http.put(
    'http://localhost:8000/admin/users/:userId/role',
    async ({ params, request }) => {
      const { userId } = params;
      const body = (await request.json()) as { role: string };

      const user = mockUsers.find(u => u.id === userId);
      if (user) {
        user.role = body.role;
      }

      return HttpResponse.json({ success: true });
    }
  ),

  // Deactivate user
  http.post(
    'http://localhost:8000/admin/users/:userId/deactivate',
    ({ params }) => {
      const { userId } = params;

      const user = mockUsers.find(u => u.id === userId);
      if (user) {
        user.status = 'inactive';
      }

      return HttpResponse.json({ success: true });
    }
  ),
];
