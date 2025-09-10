import Redis from 'ioredis';

import { CacheService } from '@/types';

export class RedisCacheService implements CacheService {
  private redis: Redis;
  private defaultTTL: number;

  constructor(redisUrl: string, defaultTTL = 300) {
    this.redis = new Redis(redisUrl, {
      enableReadyCheck: false,
      maxRetriesPerRequest: 3,
    });
    this.defaultTTL = defaultTTL;
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await this.redis.get(key);
      if (!value) return null;
      return JSON.parse(value) as T;
    } catch (error) {
      console.error(`Cache get error for key ${key}:`, error);
      return null;
    }
  }

  async set<T>(key: string, value: T, ttl?: number): Promise<void> {
    try {
      const serialized = JSON.stringify(value);
      const expiration = ttl || this.defaultTTL;
      await this.redis.setex(key, expiration, serialized);
    } catch (error) {
      console.error(`Cache set error for key ${key}:`, error);
    }
  }

  async del(key: string): Promise<void> {
    try {
      await this.redis.del(key);
    } catch (error) {
      console.error(`Cache delete error for key ${key}:`, error);
    }
  }

  async flush(): Promise<void> {
    try {
      await this.redis.flushdb();
    } catch (error) {
      console.error('Cache flush error:', error);
    }
  }

  async mget<T>(keys: string[]): Promise<(T | null)[]> {
    try {
      const values = await this.redis.mget(...keys);
      return values.map((value: any) => {
        if (!value) return null;
        try {
          return JSON.parse(value) as T;
        } catch {
          return null;
        }
      });
    } catch (error) {
      console.error(`Cache mget error for keys ${keys.join(', ')}:`, error);
      return keys.map(() => null);
    }
  }

  async mset<T>(keyValuePairs: Array<{ key: string; value: T; ttl?: number }>): Promise<void> {
    try {
      const pipeline = this.redis.pipeline();
      for (const { key, value, ttl } of keyValuePairs) {
        const serialized = JSON.stringify(value);
        const expiration = ttl || this.defaultTTL;
        pipeline.setex(key, expiration, serialized);
      }
      await pipeline.exec();
    } catch (error) {
      console.error('Cache mset error:', error);
    }
  }

  // Persisted queries cache
  async getPersistedQuery(queryHash: string): Promise<string | null> {
    return this.get<string>(`pq:${queryHash}`);
  }

  async setPersistedQuery(queryHash: string, query: string, ttl = 86400): Promise<void> {
    await this.set(`pq:${queryHash}`, query, ttl);
  }

  // Query result cache with complexity-based TTL
  async getCachedQueryResult<T>(
    queryHash: string,
    variables: Record<string, any>,
    userId?: string
  ): Promise<T | null> {
    const cacheKey = this.buildQueryCacheKey(queryHash, variables, userId);
    return this.get<T>(cacheKey);
  }

  async setCachedQueryResult<T>(
    queryHash: string,
    variables: Record<string, any>,
    result: T,
    ttl?: number,
    userId?: string
  ): Promise<void> {
    const cacheKey = this.buildQueryCacheKey(queryHash, variables, userId);
    await this.set(cacheKey, result, ttl);
  }

  private buildQueryCacheKey(
    queryHash: string,
    variables: Record<string, any>,
    userId?: string
  ): string {
    const variablesHash = this.hashObject(variables);
    const userPart = userId ? `:user:${userId}` : '';
    return `qr:${queryHash}:${variablesHash}${userPart}`;
  }

  private hashObject(obj: Record<string, any>): string {
    // Simple hash function for cache key generation
    const str = JSON.stringify(obj, Object.keys(obj).sort());
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }

  // Health check
  async ping(): Promise<boolean> {
    try {
      const result = await this.redis.ping();
      return result === 'PONG';
    } catch {
      return false;
    }
  }

  // Cleanup
  async disconnect(): Promise<void> {
    await this.redis.quit();
  }
}
