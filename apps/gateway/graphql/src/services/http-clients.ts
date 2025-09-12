import axios, { AxiosInstance, AxiosResponse } from 'axios';

import {
  LearnerService,
  IepService,
  AnalyticsService,
  AdminPortalService,
  ServiceResponse,
  Learner,
  IepDoc,
  LearnerAnalytics,
  DashboardMetrics,
  Guardian,
  Goal,
  Accommodation,
  SubjectGrade,
  GoalProgress,
  GetLearnersParams,
  GetIepsParams,
  LearnerInput,
  GuardianInput,
  IepDocInput,
  GoalInput,
  AccommodationInput,
  CrdtOperationInput,
} from '@/types';

abstract class BaseService {
  protected client: AxiosInstance;

  constructor(baseURL: string, timeout = 5000) {
    this.client = axios.create({
      baseURL,
      timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for consistent error handling
    this.client.interceptors.response.use(
      response => response,
      error => {
        console.error(`Service error: ${error.message}`, {
          url: error.config?.url,
          status: error.response?.status,
          data: error.response?.data,
        });
        return Promise.reject(error);
      }
    );
  }

  protected async handleRequest<T>(
    request: Promise<AxiosResponse<T>>
  ): Promise<ServiceResponse<T>> {
    try {
      const response = await request;
      return {
        data: response.data,
        status: response.status,
      };
    } catch (error: any) {
      return {
        error: error.response?.data?.message || error.message || 'Service error',
        status: error.response?.status || 500,
      };
    }
  }

  setAuthToken(token: string): void {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }
}

export class HTTPLearnerService extends BaseService implements LearnerService {
  constructor(baseURL: string) {
    super(baseURL);
  }

  async getLearner(id: string): Promise<ServiceResponse<Learner>> {
    return this.handleRequest(this.client.get<Learner>(`/learners/${id}`));
  }

  async getLearners(params: GetLearnersParams): Promise<ServiceResponse<Learner[]>> {
    return this.handleRequest(this.client.get<Learner[]>('/learners', { params }));
  }

  async createLearner(input: LearnerInput): Promise<ServiceResponse<Learner>> {
    return this.handleRequest(this.client.post<Learner>('/learners', input));
  }

  async updateLearner(id: string, input: LearnerInput): Promise<ServiceResponse<Learner>> {
    return this.handleRequest(this.client.put<Learner>(`/learners/${id}`, input));
  }

  async addGuardian(
    learnerId: string,
    guardian: GuardianInput
  ): Promise<ServiceResponse<Guardian>> {
    return this.handleRequest(
      this.client.post<Guardian>(`/learners/${learnerId}/guardians`, guardian)
    );
  }

  async getGuardians(learnerId: string): Promise<ServiceResponse<Guardian[]>> {
    return this.handleRequest(this.client.get<Guardian[]>(`/learners/${learnerId}/guardians`));
  }
}

export class HTTPIepService extends BaseService implements IepService {
  constructor(baseURL: string) {
    super(baseURL);
  }

  async getIep(id: string): Promise<ServiceResponse<IepDoc>> {
    return this.handleRequest(this.client.get<IepDoc>(`/ieps/${id}`));
  }

  async getIeps(params: GetIepsParams): Promise<ServiceResponse<IepDoc[]>> {
    return this.handleRequest(this.client.get<IepDoc[]>('/ieps', { params }));
  }

  async createIep(input: IepDocInput): Promise<ServiceResponse<IepDoc>> {
    return this.handleRequest(this.client.post<IepDoc>('/ieps', input));
  }

  async saveDraft(
    iepId: string,
    operations: CrdtOperationInput[]
  ): Promise<ServiceResponse<IepDoc>> {
    return this.handleRequest(this.client.post<IepDoc>(`/ieps/${iepId}/draft`, { operations }));
  }

  async submitForApproval(iepId: string): Promise<ServiceResponse<IepDoc>> {
    return this.handleRequest(this.client.post<IepDoc>(`/ieps/${iepId}/submit-approval`));
  }

  async addGoal(iepId: string, goal: GoalInput): Promise<ServiceResponse<Goal>> {
    return this.handleRequest(this.client.post<Goal>(`/ieps/${iepId}/goals`, goal));
  }

  async addAccommodation(
    iepId: string,
    accommodation: AccommodationInput
  ): Promise<ServiceResponse<Accommodation>> {
    return this.handleRequest(
      this.client.post<Accommodation>(`/ieps/${iepId}/accommodations`, accommodation)
    );
  }

  async getStudentIeps(studentId: string): Promise<ServiceResponse<IepDoc[]>> {
    return this.handleRequest(this.client.get<IepDoc[]>(`/students/${studentId}/ieps`));
  }

  async getActiveIeps(tenantId?: string): Promise<ServiceResponse<IepDoc[]>> {
    const params = tenantId ? { tenantId } : {};
    return this.handleRequest(this.client.get<IepDoc[]>('/ieps/active', { params }));
  }

  async getPendingApprovals(tenantId?: string): Promise<ServiceResponse<IepDoc[]>> {
    const params = tenantId ? { tenantId } : {};
    return this.handleRequest(this.client.get<IepDoc[]>('/ieps/pending-approvals', { params }));
  }
}

export class HTTPAnalyticsService extends BaseService implements AnalyticsService {
  constructor(baseURL: string) {
    super(baseURL);
  }

  async getLearnerAnalytics(learnerId: string): Promise<ServiceResponse<LearnerAnalytics>> {
    return this.handleRequest(
      this.client.get<LearnerAnalytics>(`/analytics/learners/${learnerId}`)
    );
  }

  async getDashboardMetrics(tenantId?: string): Promise<ServiceResponse<DashboardMetrics>> {
    const params = tenantId ? { tenantId } : {};
    return this.handleRequest(
      this.client.get<DashboardMetrics>('/analytics/dashboard', { params })
    );
  }

  async getAcademicTrends(
    tenantId?: string,
    timeframe = '30d'
  ): Promise<ServiceResponse<SubjectGrade[]>> {
    const params = { timeframe, ...(tenantId && { tenantId }) };
    return this.handleRequest(
      this.client.get<SubjectGrade[]>('/analytics/academic-trends', { params })
    );
  }

  async getGoalProgressSummary(
    tenantId?: string,
    timeframe = 'current'
  ): Promise<ServiceResponse<GoalProgress[]>> {
    const params = { timeframe, ...(tenantId && { tenantId }) };
    return this.handleRequest(
      this.client.get<GoalProgress[]>('/analytics/goal-progress', { params })
    );
  }
}

export class HTTPAdminPortalService extends BaseService implements AdminPortalService {
  constructor(baseURL: string) {
    super(baseURL);
  }

  async getDashboardData(tenantId?: string): Promise<ServiceResponse<DashboardMetrics>> {
    const params = tenantId ? { tenantId } : {};
    return this.handleRequest(this.client.get<DashboardMetrics>('/dashboard', { params }));
  }

  async getSystemHealth(): Promise<
    ServiceResponse<{ status: string; services: Record<string, string> }>
  > {
    return this.handleRequest(this.client.get('/health'));
  }
}

// Service factory for creating service instances
export class ServiceFactory {
  private static instance: ServiceFactory;
  private learnerService?: LearnerService;
  private iepService?: IepService;
  private analyticsService?: AnalyticsService;
  private adminPortalService?: AdminPortalService;

  private constructor() {}

  static getInstance(): ServiceFactory {
    if (!ServiceFactory.instance) {
      ServiceFactory.instance = new ServiceFactory();
    }
    return ServiceFactory.instance;
  }

  createLearnerService(): LearnerService {
    if (!this.learnerService) {
      const baseURL = process.env.LEARNER_SERVICE_URL || 'http://localhost:8000';
      this.learnerService = new HTTPLearnerService(baseURL);
    }
    return this.learnerService;
  }

  createIepService(): IepService {
    if (!this.iepService) {
      const baseURL = process.env.IEP_SERVICE_URL || 'http://localhost:8001';
      this.iepService = new HTTPIepService(baseURL);
    }
    return this.iepService;
  }

  createAnalyticsService(): AnalyticsService {
    if (!this.analyticsService) {
      const baseURL = process.env.ANALYTICS_SERVICE_URL || 'http://localhost:8002';
      this.analyticsService = new HTTPAnalyticsService(baseURL);
    }
    return this.analyticsService;
  }

  createAdminPortalService(): AdminPortalService {
    if (!this.adminPortalService) {
      const baseURL = process.env.ADMIN_PORTAL_SERVICE_URL || 'http://localhost:8095';
      this.adminPortalService = new HTTPAdminPortalService(baseURL);
    }
    return this.adminPortalService;
  }

  // Method to set auth token for all services
  setAuthToken(token: string): void {
    if (this.learnerService && 'setAuthToken' in this.learnerService) {
      (this.learnerService as HTTPLearnerService).setAuthToken(token);
    }
    if (this.iepService && 'setAuthToken' in this.iepService) {
      (this.iepService as HTTPIepService).setAuthToken(token);
    }
    if (this.analyticsService && 'setAuthToken' in this.analyticsService) {
      (this.analyticsService as HTTPAnalyticsService).setAuthToken(token);
    }
    if (this.adminPortalService && 'setAuthToken' in this.adminPortalService) {
      (this.adminPortalService as HTTPAdminPortalService).setAuthToken(token);
    }
  }
}
