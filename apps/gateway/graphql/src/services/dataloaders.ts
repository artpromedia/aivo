// Using a simple DataLoader-like implementation since we don't have the package yet
export class DataLoader<K, V> {
  private batchLoadFn: (keys: readonly K[]) => Promise<readonly (V | Error)[]>;
  private cache: Map<string, Promise<V>> = new Map();
  private batch: K[] = [];
  private batchPromise: Promise<void> | null = null;

  constructor(batchLoadFn: (keys: readonly K[]) => Promise<readonly (V | Error)[]>) {
    this.batchLoadFn = batchLoadFn;
  }

  async load(key: K): Promise<V> {
    const cacheKey = String(key);

    // Return cached result if available
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!;
    }

    // Create promise for this key
    const promise = new Promise<V>((resolve, reject) => {
      this.batch.push(key);

      // Schedule batch execution
      if (!this.batchPromise) {
        this.batchPromise = Promise.resolve().then(() => this.processBatch());
      }

      this.batchPromise.then(() => {
        const result = this.cache.get(cacheKey);
        if (result) {
          result.then(resolve).catch(reject);
        } else {
          reject(new Error(`No result for key: ${String(key)}`));
        }
      });
    });

    this.cache.set(cacheKey, promise);
    return promise;
  }

  async loadMany(keys: readonly K[]): Promise<(V | Error)[]> {
    return Promise.all(keys.map(key => this.load(key).catch(error => error)));
  }

  clear(key: K): this {
    this.cache.delete(String(key));
    return this;
  }

  clearAll(): this {
    this.cache.clear();
    return this;
  }

  private async processBatch(): Promise<void> {
    const batch = this.batch.slice();
    this.batch = [];
    this.batchPromise = null;

    if (batch.length === 0) return;

    try {
      const results = await this.batchLoadFn(batch);

      batch.forEach((key, index) => {
        const result = results[index];
        const cacheKey = String(key);

        if (result instanceof Error) {
          this.cache.set(cacheKey, Promise.reject(result));
        } else {
          this.cache.set(cacheKey, Promise.resolve(result));
        }
      });
    } catch (error) {
      // If batch function fails, reject all keys
      batch.forEach(key => {
        const cacheKey = String(key);
        this.cache.set(cacheKey, Promise.reject(error));
      });
    }
  }
}

import {
  Learner,
  IepDoc,
  Guardian,
  LearnerAnalytics,
  LearnerService,
  IepService,
  AnalyticsService,
  CacheService,
} from '@/types';

// DataLoader factory functions
function createLearnerLoader(
  learnerService: LearnerService,
  cache: CacheService
): DataLoader<string, Learner> {
  return new DataLoader<string, Learner>(async ids => {
    const results = await Promise.allSettled(
      ids.map(async id => {
        const cached = await cache.get<string>(`learner:${id}`);
        if (cached) {
          return JSON.parse(cached) as Learner;
        }

        const response = await learnerService.getLearner(id);
        if (response.data) {
          await cache.set(`learner:${id}`, JSON.stringify(response.data), 300); // 5 min TTL
          return response.data;
        }
        throw new Error(`Learner not found: ${id}`);
      })
    );

    return results.map(result =>
      result.status === 'fulfilled' ? result.value : new Error(`Failed to load learner`)
    );
  });
}

function createGuardianLoader(
  learnerService: LearnerService,
  cache: CacheService
): DataLoader<string, Guardian[]> {
  return new DataLoader<string, Guardian[]>(async learnerIds => {
    const results = await Promise.allSettled(
      learnerIds.map(async learnerId => {
        const cached = await cache.get<string>(`guardians:${learnerId}`);
        if (cached) {
          return JSON.parse(cached) as Guardian[];
        }

        // Get learner first to access guardians
        const response = await learnerService.getLearner(learnerId);
        if (response.data && response.data.guardians) {
          await cache.set(`guardians:${learnerId}`, JSON.stringify(response.data.guardians), 600); // 10 min TTL
          return response.data.guardians;
        }
        return [];
      })
    );

    return results.map(result => (result.status === 'fulfilled' ? result.value : []));
  });
}

function createIepLoader(iepService: IepService, cache: CacheService): DataLoader<string, IepDoc> {
  return new DataLoader<string, IepDoc>(async ids => {
    const results = await Promise.allSettled(
      ids.map(async id => {
        const cached = await cache.get<string>(`iep:${id}`);
        if (cached) {
          return JSON.parse(cached) as IepDoc;
        }

        const response = await iepService.getIep(id);
        if (response.data) {
          await cache.set(`iep:${id}`, JSON.stringify(response.data), 300); // 5 min TTL
          return response.data;
        }
        throw new Error(`IEP not found: ${id}`);
      })
    );

    return results.map(result =>
      result.status === 'fulfilled' ? result.value : new Error(`Failed to load IEP`)
    );
  });
}

function createAnalyticsLoader(
  analyticsService: AnalyticsService,
  cache: CacheService
): DataLoader<string, LearnerAnalytics> {
  return new DataLoader<string, LearnerAnalytics>(async learnerIds => {
    const results = await Promise.allSettled(
      learnerIds.map(async learnerId => {
        const cached = await cache.get<string>(`learner_analytics:${learnerId}`);
        if (cached) {
          return JSON.parse(cached) as LearnerAnalytics;
        }

        const response = await analyticsService.getLearnerAnalytics(learnerId);
        if (response.data) {
          await cache.set(`learner_analytics:${learnerId}`, JSON.stringify(response.data), 900); // 15 min TTL
          return response.data;
        }
        throw new Error(`Analytics not found: ${learnerId}`);
      })
    );

    return results.map(result =>
      result.status === 'fulfilled' ? result.value : new Error(`Failed to load analytics`)
    );
  });
}

function createStudentIepsLoader(
  iepService: IepService,
  cache: CacheService
): DataLoader<string, IepDoc[]> {
  return new DataLoader<string, IepDoc[]>(async studentIds => {
    const results = await Promise.allSettled(
      studentIds.map(async studentId => {
        const cached = await cache.get<string>(`student_ieps:${studentId}`);
        if (cached) {
          return JSON.parse(cached) as IepDoc[];
        }

        // Get IEPs for this student using getIeps with studentId filter
        const response = await iepService.getIeps({ studentId });
        if (response.data) {
          await cache.set(`student_ieps:${studentId}`, JSON.stringify(response.data), 600); // 10 min TTL
          return response.data;
        }
        return [];
      })
    );

    return results.map(result => (result.status === 'fulfilled' ? result.value : []));
  });
}

export const createDataLoaders = (
  learnerService: LearnerService,
  iepService: IepService,
  analyticsService: AnalyticsService,
  cache: CacheService
): any => {
  return {
    learnerLoader: createLearnerLoader(learnerService, cache),
    guardianLoader: createGuardianLoader(learnerService, cache),
    iepLoader: createIepLoader(iepService, cache),
    analyticsLoader: createAnalyticsLoader(analyticsService, cache),
    studentIepsLoader: createStudentIepsLoader(iepService, cache),
  };
};

// Cache clearing utility functions
export const clearCacheForLearner = async (
  cache: CacheService,
  learnerId: string
): Promise<void> => {
  await Promise.all([
    cache.del(`learner:${learnerId}`),
    cache.del(`guardians:${learnerId}`),
    cache.del(`learner_analytics:${learnerId}`),
    cache.del(`student_ieps:${learnerId}`),
  ]);
};

export const clearCacheForIep = async (
  cache: CacheService,
  iepId: string,
  learnerId?: string
): Promise<void> => {
  const keysToDelete = [`iep:${iepId}`];
  if (learnerId) {
    keysToDelete.push(`student_ieps:${learnerId}`);
  }
  await Promise.all(keysToDelete.map(key => cache.del(key)));
};

// Cache invalidation helpers
export function createCacheInvalidators(cache: CacheService) {
  return {
    invalidateLearner: async (learnerId: string) => {
      await Promise.all([
        cache.del(`learner:${learnerId}`),
        cache.del(`guardians:${learnerId}`),
        cache.del(`analytics:${learnerId}`),
        cache.del(`student-ieps:${learnerId}`),
      ]);
    },

    invalidateIep: async (iepId: string, studentId?: string) => {
      await cache.del(`iep:${iepId}`);
      if (studentId) {
        await cache.del(`student-ieps:${studentId}`);
      }
    },

    invalidateGuardians: async (learnerId: string) => {
      await cache.del(`guardians:${learnerId}`);
    },

    invalidateAnalytics: async (learnerId: string) => {
      await cache.del(`analytics:${learnerId}`);
    },

    invalidateTenantData: async (_tenantId: string) => {
      // This would require a more sophisticated cache invalidation strategy
      // For now, we'll implement a simple pattern-based invalidation
      await cache.flush(); // Nuclear option - in production, use pattern matching
    },
  };
}
