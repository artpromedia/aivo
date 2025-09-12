import { describe, it, expect } from 'vitest';

import { SubscriptionsAPI } from '@/api/subscriptions';

describe('SubscriptionsAPI', () => {
  it('fetches subscriptions successfully', async () => {
    const result = await SubscriptionsAPI.getSubscriptions();

    expect(result).toBeDefined();
    expect(result.subscriptions).toBeInstanceOf(Array);
    expect(result.subscriptions.length).toBeGreaterThan(0);

    // Check the structure of a subscription
    const subscription = result.subscriptions[0];
    expect(subscription).toHaveProperty('id');
    expect(subscription).toHaveProperty('plan_name');
    expect(subscription).toHaveProperty('status');
    expect(subscription).toHaveProperty('tenant_id');
  });

  it('fetches subscription plans successfully', async () => {
    const result = await SubscriptionsAPI.getAvailablePlans();

    expect(result).toBeDefined();
    expect(result.plans).toBeInstanceOf(Array);
    expect(result.plans.length).toBeGreaterThan(0);

    // Check the structure of a plan
    const plan = result.plans[0];
    expect(plan).toHaveProperty('id');
    expect(plan).toHaveProperty('name');
    expect(plan).toHaveProperty('amount');
    expect(plan).toHaveProperty('features');
  });

  it('creates a new subscription', async () => {
    const subscriptionData = {
      tenant_id: 'test_tenant',
      plan_id: 'plan_basic',
      quantity: 5,
      metadata: { test: 'true' },
    };

    const result = await SubscriptionsAPI.createSubscription(subscriptionData);

    expect(result).toBeDefined();
    expect(result.tenant_id).toBe(subscriptionData.tenant_id);
    expect(result.plan_id).toBe(subscriptionData.plan_id);
    expect(result.quantity).toBe(subscriptionData.quantity);
    expect(result.status).toBe('active');
  });
});
