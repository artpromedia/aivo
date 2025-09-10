import DataLoader from 'dataloader';

import { JWTAuthService } from '@/middleware/auth';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  tenantId?: string;
  scopes: string[];
}

export enum UserRole {
  STUDENT = 'STUDENT',
  TEACHER = 'TEACHER',
  STAFF = 'STAFF',
  DISTRICT_ADMIN = 'DISTRICT_ADMIN',
  SYSTEM_ADMIN = 'SYSTEM_ADMIN',
}

export interface JWTPayload {
  sub: string;
  email: string;
  role: UserRole;
  tenantId?: string;
  scopes: string[];
  iat: number;
  exp: number;
  iss: string;
  aud: string;
}

export interface GraphQLContext {
  user?: User;
  token?: string;
  dataSources: {
    learnerService: LearnerService;
    iepService: IepService;
    analyticsService: AnalyticsService;
    adminPortalService: AdminPortalService;
  };
  cache: CacheService;
  loaders: DataLoaders;
  authService: JWTAuthService;
  cacheInvalidators: CacheInvalidators;
}

export interface DataLoaders {
  learnerLoader: DataLoader<string, Learner>;
  iepLoader: DataLoader<string, IepDoc>;
  guardianLoader: DataLoader<string, Guardian[]>;
  analyticsLoader: DataLoader<string, LearnerAnalytics>;
  studentIepsLoader: DataLoader<string, IepDoc[]>;
}

export interface CacheInvalidators {
  invalidateLearner: (learnerId: string) => Promise<void>;
  invalidateIep: (iepId: string, studentId?: string) => Promise<void>;
  invalidateGuardians: (learnerId: string) => Promise<void>;
  invalidateAnalytics: (learnerId: string) => Promise<void>;
  invalidateTenantData: (tenantId: string) => Promise<void>;
}

export interface CacheService {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttl?: number): Promise<void>;
  del(key: string): Promise<void>;
  flush(): Promise<void>;
}

export interface ServiceResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface LearnerService {
  getLearner(id: string): Promise<ServiceResponse<Learner>>;
  getLearners(params: GetLearnersParams): Promise<ServiceResponse<Learner[]>>;
  createLearner(input: LearnerInput): Promise<ServiceResponse<Learner>>;
  updateLearner(id: string, input: LearnerInput): Promise<ServiceResponse<Learner>>;
  addGuardian(learnerId: string, guardian: GuardianInput): Promise<ServiceResponse<Guardian>>;
}

export interface IepService {
  getIep(id: string): Promise<ServiceResponse<IepDoc>>;
  getIeps(params: GetIepsParams): Promise<ServiceResponse<IepDoc[]>>;
  createIep(input: IepDocInput): Promise<ServiceResponse<IepDoc>>;
  saveDraft(iepId: string, operations: CrdtOperationInput[]): Promise<ServiceResponse<IepDoc>>;
  submitForApproval(iepId: string): Promise<ServiceResponse<IepDoc>>;
  addGoal(iepId: string, goal: GoalInput): Promise<ServiceResponse<Goal>>;
  addAccommodation(iepId: string, accommodation: AccommodationInput): Promise<ServiceResponse<Accommodation>>;
}

export interface AnalyticsService {
  getLearnerAnalytics(learnerId: string): Promise<ServiceResponse<LearnerAnalytics>>;
  getDashboardMetrics(tenantId?: string): Promise<ServiceResponse<DashboardMetrics>>;
  getAcademicTrends(tenantId?: string, timeframe?: string): Promise<ServiceResponse<SubjectGrade[]>>;
  getGoalProgressSummary(tenantId?: string, timeframe?: string): Promise<ServiceResponse<GoalProgress[]>>;
}

export interface AdminPortalService {
  getDashboardData(tenantId?: string): Promise<ServiceResponse<DashboardMetrics>>;
}

// Core Types
export interface Learner {
  id: string;
  tenantId: string;
  firstName: string;
  lastName: string;
  email?: string;
  dateOfBirth?: string;
  grade?: string;
  enrollmentStatus: EnrollmentStatus;
  guardians: Guardian[];
  ieps: IepDoc[];
  analytics?: LearnerAnalytics;
  createdAt: string;
  updatedAt: string;
}

export interface Guardian {
  id: string;
  learnerId: string;
  firstName: string;
  lastName: string;
  email?: string;
  phone?: string;
  relationship: GuardianRelationship;
  isPrimary: boolean;
  createdAt: string;
}

export interface IepDoc {
  id: string;
  studentId: string;
  student?: Learner;
  tenantId: string;
  documentVersion: string;
  status: IepStatus;
  effectiveDate: string;
  expirationDate: string;
  studentInfo: StudentInfo;
  goals: Goal[];
  accommodations: Accommodation[];
  modifications: Modification[];
  services: Service[];
  approvalRecords: ApprovalRecord[];
  currentApprovalStep: number;
  vectorClock: Record<string, any>;
  operations: CrdtOperation[];
  createdBy: string;
  lastModifiedBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface LearnerAnalytics {
  learnerId: string;
  academicProgress: AcademicProgress;
  goalProgress: GoalProgress[];
  attendanceMetrics: AttendanceMetrics;
  behavioralData: BehavioralData;
  assessmentScores: AssessmentScore[];
  interventionTracking: InterventionTracking[];
  lastUpdated: string;
}

export interface DashboardMetrics {
  totalLearners: number;
  activeIeps: number;
  pendingApprovals: number;
  upcomingDeadlines: number;
  recentActivity: ActivityItem[];
  performanceOverview: PerformanceOverview;
}

// Enums
export enum EnrollmentStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  GRADUATED = 'GRADUATED',
  TRANSFERRED = 'TRANSFERRED',
}

export enum GuardianRelationship {
  PARENT = 'PARENT',
  GUARDIAN = 'GUARDIAN',
  FOSTER_PARENT = 'FOSTER_PARENT',
  GRANDPARENT = 'GRANDPARENT',
  OTHER = 'OTHER',
}

export enum IepStatus {
  DRAFT = 'DRAFT',
  SUBMITTED_FOR_APPROVAL = 'SUBMITTED_FOR_APPROVAL',
  PARTIALLY_APPROVED = 'PARTIALLY_APPROVED',
  APPROVED = 'APPROVED',
  ACTIVE = 'ACTIVE',
  EXPIRED = 'EXPIRED',
  ARCHIVED = 'ARCHIVED',
}

// Input Types
export interface LearnerInput {
  firstName: string;
  lastName: string;
  email?: string;
  dateOfBirth?: string;
  grade?: string;
  enrollmentStatus: EnrollmentStatus;
}

export interface GuardianInput {
  firstName: string;
  lastName: string;
  email?: string;
  phone?: string;
  relationship: GuardianRelationship;
  isPrimary: boolean;
}

export interface IepDocInput {
  studentId: string;
  effectiveDate: string;
  expirationDate: string;
  studentInfo: StudentInfoInput;
}

export interface StudentInfoInput {
  fullName: string;
  dateOfBirth: string;
  grade: string;
  disability: string;
  placementSetting: string;
  assessmentAccommodations: string[];
}

export interface GoalInput {
  domain: GoalDomain;
  description: string;
  measurableAnnualGoal: string;
  benchmarks: BenchmarkInput[];
}

export interface BenchmarkInput {
  description: string;
  targetDate: string;
}

export interface AccommodationInput {
  category: AccommodationCategory;
  description: string;
  setting: AccommodationSetting;
  frequency: string;
}

export interface CrdtOperationInput {
  operationType: CrdtOperationType;
  fieldPath: string;
  value: any;
  vectorClock: Record<string, any>;
}

// Query Parameters
export interface GetLearnersParams {
  tenantId?: string;
  enrollmentStatus?: EnrollmentStatus;
  grade?: string;
  limit?: number;
  offset?: number;
}

export interface GetIepsParams {
  studentId?: string;
  tenantId?: string;
  status?: IepStatus;
  limit?: number;
  offset?: number;
}

// Additional types for completeness
export interface StudentInfo {
  fullName: string;
  dateOfBirth: string;
  grade: string;
  disability: string;
  placementSetting: string;
  assessmentAccommodations: string[];
}

export interface Goal {
  id: string;
  domain: GoalDomain;
  description: string;
  measurableAnnualGoal: string;
  benchmarks: Benchmark[];
  progressReports: ProgressReport[];
  createdAt: string;
}

export interface Accommodation {
  id: string;
  category: AccommodationCategory;
  description: string;
  setting: AccommodationSetting;
  frequency: string;
}

export interface Modification {
  id: string;
  subject: string;
  description: string;
  justification: string;
}

export interface Service {
  id: string;
  serviceType: ServiceType;
  frequency: string;
  duration: string;
  location: string;
  provider: string;
  startDate: string;
  endDate?: string;
}

export interface ApprovalRecord {
  id: string;
  approvalStep: number;
  approverRole: string;
  approverUserId: string;
  status: ApprovalStatus;
  comments?: string;
  approvedAt?: string;
  createdAt: string;
}

export interface CrdtOperation {
  id: string;
  operationType: CrdtOperationType;
  fieldPath: string;
  value: any;
  vectorClock: Record<string, any>;
  authorId: string;
  timestamp: string;
}

export interface AcademicProgress {
  currentGPA?: number;
  gradeLevel: string;
  subjectGrades: SubjectGrade[];
  progressTrend: ProgressTrend;
  comparedToGrade: ComparisonMetric;
}

export interface SubjectGrade {
  subject: string;
  currentGrade: string;
  percentage?: number;
  trend: ProgressTrend;
}

export interface GoalProgress {
  goalId: string;
  goal: Goal;
  completionPercentage: number;
  onTrack: boolean;
  projectedCompletion?: string;
  recentBenchmarks: Benchmark[];
}

export interface AttendanceMetrics {
  attendanceRate: number;
  absences: number;
  tardies: number;
  attendanceTrend: ProgressTrend;
  lastThirtyDays: number;
}

export interface BehavioralData {
  incidentCount: number;
  positiveReinforcements: number;
  interventionsActive: number;
  behavioralGoalsOnTrack: number;
  trend: ProgressTrend;
}

export interface AssessmentScore {
  assessmentId: string;
  assessmentName: string;
  subject: string;
  score: number;
  percentile?: number;
  dateAdministered: string;
  accommodationsUsed: string[];
}

export interface InterventionTracking {
  interventionId: string;
  interventionType: string;
  startDate: string;
  endDate?: string;
  effectiveness?: number;
  status: InterventionStatus;
}

export interface ActivityItem {
  id: string;
  type: ActivityType;
  description: string;
  timestamp: string;
  userId: string;
  metadata?: Record<string, any>;
}

export interface PerformanceOverview {
  totalStudentsServed: number;
  iepComplianceRate: number;
  averageGoalProgress: number;
  servicesDelivered: number;
  upcomingMeetings: number;
}

export interface Benchmark {
  id: string;
  description: string;
  targetDate: string;
  achieved: boolean;
}

export interface ProgressReport {
  id: string;
  reportingPeriod: string;
  progressTowardGoal: string;
  reportDate: string;
  reportedBy: string;
}

export interface ComparisonMetric {
  percentile?: number;
  standardDeviations?: number;
  comparison: string;
}

// Additional Enums
export enum GoalDomain {
  ACADEMIC = 'ACADEMIC',
  FUNCTIONAL = 'FUNCTIONAL',
  BEHAVIORAL = 'BEHAVIORAL',
  COMMUNICATION = 'COMMUNICATION',
  SOCIAL = 'SOCIAL',
}

export enum AccommodationCategory {
  PRESENTATION = 'PRESENTATION',
  RESPONSE = 'RESPONSE',
  TIMING = 'TIMING',
  SETTING = 'SETTING',
  ASSISTIVE_TECHNOLOGY = 'ASSISTIVE_TECHNOLOGY',
}

export enum AccommodationSetting {
  CLASSROOM = 'CLASSROOM',
  ASSESSMENT = 'ASSESSMENT',
  BOTH = 'BOTH',
}

export enum ServiceType {
  SPECIAL_EDUCATION = 'SPECIAL_EDUCATION',
  SPEECH_THERAPY = 'SPEECH_THERAPY',
  OCCUPATIONAL_THERAPY = 'OCCUPATIONAL_THERAPY',
  PHYSICAL_THERAPY = 'PHYSICAL_THERAPY',
  COUNSELING = 'COUNSELING',
  BEHAVIORAL_SUPPORT = 'BEHAVIORAL_SUPPORT',
}

export enum ApprovalStatus {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  REQUIRES_REVISION = 'REQUIRES_REVISION',
}

export enum CrdtOperationType {
  INSERT = 'INSERT',
  UPDATE = 'UPDATE',
  DELETE = 'DELETE',
  MERGE = 'MERGE',
}

export enum ProgressTrend {
  IMPROVING = 'IMPROVING',
  STABLE = 'STABLE',
  DECLINING = 'DECLINING',
}

export enum InterventionStatus {
  ACTIVE = 'ACTIVE',
  COMPLETED = 'COMPLETED',
  DISCONTINUED = 'DISCONTINUED',
  ON_HOLD = 'ON_HOLD',
}

export enum ActivityType {
  IEP_CREATED = 'IEP_CREATED',
  IEP_APPROVED = 'IEP_APPROVED',
  GOAL_UPDATED = 'GOAL_UPDATED',
  ASSESSMENT_COMPLETED = 'ASSESSMENT_COMPLETED',
  MEETING_SCHEDULED = 'MEETING_SCHEDULED',
}
