import { http, HttpResponse } from 'msw';

/**
 * Authentication Service MSW Handlers
 * Based on OpenAPI specification and expected auth flows
 */

const mockAuthData = {
  login: {
    access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    refresh_token: 'refresh_token_example',
    token_type: 'Bearer',
    expires_in: 3600,
    user: {
      id: 'user_123',
      email: 'admin@acme.com',
      name: 'John Admin',
      role: 'admin',
      tenant_id: 'tenant_123',
      permissions: ['admin', 'billing', 'team_management'],
    },
  },
  profile: {
    id: 'user_123',
    email: 'admin@acme.com',
    name: 'John Admin',
    role: 'admin',
    tenant_id: 'tenant_123',
    permissions: ['admin', 'billing', 'team_management'],
    created_at: '2024-01-01T00:00:00Z',
    last_login: '2024-09-02T09:15:00Z',
    preferences: {
      theme: 'light',
      language: 'en',
      notifications: true,
    },
  },
};

export const authHandlers = [
  // Login
  http.post('*/auth/v1/login', async ({ request }) => {
    const body = (await request.json()) as {
      email?: string;
      password?: string;
    };

    if (!body.email || !body.password) {
      return HttpResponse.json(
        {
          error: 'Bad Request',
          message: 'Email and password are required',
        },
        { status: 400 }
      );
    }

    // Mock authentication logic
    if (body.email === 'admin@acme.com' && body.password === 'password') {
      return HttpResponse.json(mockAuthData.login, {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      });
    }

    return HttpResponse.json(
      {
        error: 'Unauthorized',
        message: 'Invalid credentials',
      },
      { status: 401 }
    );
  }),

  // Refresh Token
  http.post('*/auth/v1/refresh', async ({ request }) => {
    const body = (await request.json()) as { refresh_token?: string };

    if (!body.refresh_token) {
      return HttpResponse.json(
        {
          error: 'Bad Request',
          message: 'Refresh token is required',
        },
        { status: 400 }
      );
    }

    return HttpResponse.json(
      {
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9_new...',
        token_type: 'Bearer',
        expires_in: 3600,
      },
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }),

  // User Profile
  http.get('*/auth/v1/profile', ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        {
          error: 'Unauthorized',
          message: 'Valid authentication required',
        },
        { status: 401 }
      );
    }

    return HttpResponse.json(mockAuthData.profile, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Logout
  http.post('*/auth/v1/logout', ({ request }) => {
    const authHeader = request.headers.get('authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        {
          error: 'Unauthorized',
          message: 'Valid authentication required',
        },
        { status: 401 }
      );
    }

    return HttpResponse.json(
      {
        message: 'Successfully logged out',
      },
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }),

  // Health Check
  http.get('*/auth/v1/health', () => {
    return HttpResponse.json(
      {
        status: 'healthy',
        service: 'auth-svc',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
      },
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }),
];
