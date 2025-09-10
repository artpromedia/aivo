import { GraphQLError, GraphQLResolveInfo } from 'graphql';
import jwt from 'jsonwebtoken';

import { JWTPayload, User, UserRole, GraphQLContext } from '../types';

export interface JWTConfig {
  secret: string;
  issuer: string;
  audience: string;
}

// Define HTTP request interface for token extraction
interface _HttpRequest {
  headers: {
    authorization?: string;
    cookie?: string;
  };
  cookies?: Record<string, string>;
  query?: Record<string, string | string[]>;
}

export class JWTAuthService {
  private config: JWTConfig;

  constructor(config: JWTConfig) {
    this.config = config;
  }

  verifyToken(token: string): JWTPayload {
    try {
      const payload = jwt.verify(token, this.config.secret, {
        issuer: this.config.issuer,
        audience: this.config.audience,
      }) as JWTPayload;

      return payload;
    } catch {
      throw new GraphQLError('Invalid or expired token', {
        extensions: { code: 'UNAUTHENTICATED' }
      });
    }
  }

  extractUserFromPayload(payload: JWTPayload): User {
    return {
      id: payload.sub,
      email: payload.email,
      role: payload.role,
      tenantId: payload.tenantId,
      scopes: payload.scopes || [],
    };
  }

  validateScopes(userScopes: string[], requiredScopes: string[]): boolean {
    if (requiredScopes.length === 0) return true;
    return requiredScopes.every(scope => userScopes.includes(scope));
  }

  validateRole(userRole: UserRole, allowedRoles: UserRole[]): boolean {
    if (allowedRoles.length === 0) return true;
    return allowedRoles.includes(userRole);
  }

  hasAdminAccess(user: User): boolean {
    return [UserRole.DISTRICT_ADMIN, UserRole.SYSTEM_ADMIN].includes(user.role);
  }

  hasStaffAccess(user: User): boolean {
    return [UserRole.STAFF, UserRole.TEACHER, UserRole.DISTRICT_ADMIN, UserRole.SYSTEM_ADMIN].includes(
      user.role
    );
  }

  canAccessTenant(user: User, tenantId?: string): boolean {
    // System admin can access all tenants
    if (user.role === UserRole.SYSTEM_ADMIN) return true;
    
    // If no tenant specified, allow access
    if (!tenantId) return true;
    
    // User must belong to the same tenant
    return user.tenantId === tenantId;
  }

  canAccessLearnerData(user: User, learnerId: string, tenantId?: string): boolean {
    // Check tenant access first
    if (!this.canAccessTenant(user, tenantId)) return false;

    // System and district admins can access all learner data in their tenant
    if (this.hasAdminAccess(user)) return true;

    // Staff can access learner data in their tenant
    if (this.hasStaffAccess(user)) return true;

    // Students can only access their own data
    if (user.role === UserRole.STUDENT) {
      return user.id === learnerId;
    }

    return false;
  }

  canModifyIep(user: User, iep: { studentId: string; tenantId: string }): boolean {
    // Check tenant access
    if (!this.canAccessTenant(user, iep.tenantId)) return false;

    // Only staff and admins can modify IEPs
    return this.hasStaffAccess(user);
  }

  canApproveIep(user: User, iep: { tenantId: string }): boolean {
    // Check tenant access
    if (!this.canAccessTenant(user, iep.tenantId)) return false;

    // Only staff with approval scope can approve IEPs
    return (
      this.hasStaffAccess(user) && 
      (user.scopes.includes('iep:approve') || this.hasAdminAccess(user))
    );
  }

  canViewAnalytics(user: User, tenantId?: string): boolean {
    // Check tenant access
    if (!this.canAccessTenant(user, tenantId)) return false;

    // Staff and admins can view analytics
    return this.hasStaffAccess(user) || user.scopes.includes('analytics:read');
  }

  canViewDashboard(user: User, tenantId?: string): boolean {
    // Check tenant access
    if (!this.canAccessTenant(user, tenantId)) return false;

    // Staff and admins can view dashboard
    return this.hasStaffAccess(user) || user.scopes.includes('dashboard:read');
  }
}

export function extractTokenFromRequest(req: _HttpRequest): string | null {
  // Try Authorization header first
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  // Try query parameter
  const queryToken = req.query?.token;
  if (queryToken && typeof queryToken === 'string') {
    return queryToken;
  }

  return null;
}

// Directive for requiring authentication
export function requireAuth(allowedRoles: UserRole[] = [], requiredScopes: string[] = []) {
  return <TParent = unknown, TArgs = Record<string, unknown>, TResult = unknown>(
    resolver: (parent: TParent, args: TArgs, context: GraphQLContext, info: GraphQLResolveInfo) => TResult | Promise<TResult>
  ) => {
    return (parent: TParent, args: TArgs, context: GraphQLContext, info: GraphQLResolveInfo) => {
      if (!context.user) {
        throw new GraphQLError('Authentication required', { extensions: { code: 'UNAUTHENTICATED' } });
      }

      // Validate roles
      if (allowedRoles.length > 0) {
        const authService = new JWTAuthService({
          secret: process.env.JWT_SECRET || '',
          issuer: process.env.JWT_ISSUER || '',
          audience: process.env.JWT_AUDIENCE || '',
        });

        if (!authService.validateRole(context.user.role, allowedRoles)) {
          throw new GraphQLError('Insufficient role permissions', { extensions: { code: 'UNAUTHENTICATED' } });
        }
      }

      // Validate scopes
      if (requiredScopes.length > 0) {
        const authService = new JWTAuthService({
          secret: process.env.JWT_SECRET || '',
          issuer: process.env.JWT_ISSUER || '',
          audience: process.env.JWT_AUDIENCE || '',
        });

        if (!authService.validateScopes(context.user.scopes, requiredScopes)) {
          throw new GraphQLError('Insufficient scope permissions', { extensions: { code: 'UNAUTHENTICATED' } });
        }
      }

      return resolver(parent, args, context, info);
    };
  };
}

// Directive for requiring admin access
export const requireAdmin = requireAuth([UserRole.DISTRICT_ADMIN, UserRole.SYSTEM_ADMIN]);

// Directive for requiring staff access
export const requireStaff = requireAuth([
  UserRole.STAFF,
  UserRole.TEACHER,
  UserRole.DISTRICT_ADMIN,
  UserRole.SYSTEM_ADMIN,
]);

// Tenant access validation
export function requireTenantAccess<TArgs = Record<string, unknown>>(
  getTenantId: (args: TArgs, context: GraphQLContext) => string
) {
  return <TParent = unknown, TResult = unknown>(
    resolver: (parent: TParent, args: TArgs, context: GraphQLContext, info: GraphQLResolveInfo) => TResult | Promise<TResult>
  ) => {
    return (parent: TParent, args: TArgs, context: GraphQLContext, info: GraphQLResolveInfo) => {
      if (!context.user) {
        throw new GraphQLError('Authentication required', { extensions: { code: 'UNAUTHENTICATED' } });
      }

      const tenantId = getTenantId(args, context);
      const authService = new JWTAuthService({
        secret: process.env.JWT_SECRET || '',
        issuer: process.env.JWT_ISSUER || '',
        audience: process.env.JWT_AUDIENCE || '',
      });

      if (!authService.canAccessTenant(context.user, tenantId)) {
        throw new GraphQLError('Insufficient tenant permissions', { extensions: { code: 'UNAUTHENTICATED' } });
      }

      return resolver(parent, args, context, info);
    };
  };
}
