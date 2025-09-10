import { test, expect } from '@playwright/test';

test.describe('Device Policy Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/device-policies');
  });

  test('should display device policy page', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Device Policies' })
    ).toBeVisible();
    await expect(
      page.getByText(
        'Create and manage device policies for different use cases'
      )
    ).toBeVisible();
  });

  test('should show create policy button', async ({ page }) => {
    const createButton = page.getByRole('button', { name: 'Create Policy' });
    await expect(createButton).toBeVisible();
    await expect(createButton).toBeEnabled();
  });

  test('should open policy creation form when create button is clicked', async ({
    page,
  }) => {
    await page.getByRole('button', { name: 'Create Policy' }).click();

    // Wait for modal overlay to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    await expect(
      page.getByRole('heading', { name: 'Create New Policy' })
    ).toBeVisible();
    await expect(page.getByText('Policy Name')).toBeVisible();
    await expect(page.getByText('Description')).toBeVisible();
    await expect(page.getByText('Policy Type')).toBeVisible();
    await expect(page.getByText('Configuration (JSON)')).toBeVisible();

    // Check for form inputs
    await expect(page.locator('input[name="name"]')).toBeVisible();
    await expect(page.locator('input[name="description"]')).toBeVisible();
    await expect(page.locator('select[name="policy_type"]')).toBeVisible();
    await expect(page.locator('textarea[name="config"]')).toBeVisible();
  });

  test('should populate default config when policy type is selected', async ({
    page,
  }) => {
    await page.getByRole('button', { name: 'Create Policy' }).click();

    // Wait for modal to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    // Select kiosk policy type
    await page.locator('select[name="policy_type"]').selectOption('kiosk');

    // Check that textarea gets populated with default config
    const configTextarea = page.locator('textarea[name="config"]');
    const configValue = await configTextarea.inputValue();

    expect(configValue).toContain('allowed_apps');
    expect(configValue).toContain('exit_code');
    expect(configValue).toContain('lockdown_level');
  });

  test('should display policy type stats', async ({ page }) => {
    // Wait for page to load
    await expect(
      page.getByRole('heading', { name: 'Device Policies' })
    ).toBeVisible();

    // Check for stats cards specifically, not the filter options
    await expect(
      page.locator('.grid').getByText('Kiosk Policies')
    ).toBeVisible();
    await expect(
      page.locator('.grid').getByText('Network Policies')
    ).toBeVisible();
    await expect(page.locator('.grid').getByText('DNS Policies')).toBeVisible();
    await expect(page.locator('.grid').getByText('Study Window')).toBeVisible();
  });

  test('should have policy search and filter functionality', async ({
    page,
  }) => {
    await expect(page.getByPlaceholder('Search policies...')).toBeVisible();
    await expect(
      page.locator('select').filter({ hasText: 'All Types' })
    ).toBeVisible();
  });

  test('should display refresh button', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: 'Refresh' });
    await expect(refreshButton).toBeVisible();
    await expect(refreshButton).toBeEnabled();
  });
});

test.describe('Device Policy CTA Guards', () => {
  test('all interactive elements have proper handlers', async ({ page }) => {
    await page.goto('/device-policies');

    // Check main action buttons
    const createButton = page
      .getByRole('button', { name: 'Create Policy' })
      .first();
    await expect(createButton).toBeEnabled();

    const refreshButton = page.getByRole('button', { name: 'Refresh' });
    await expect(refreshButton).toBeEnabled();

    // Test policy creation form CTAs
    await createButton.click();

    // Wait for modal to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    const cancelButton = page.getByRole('button', { name: 'Cancel' });
    await expect(cancelButton).toBeEnabled();

    const submitButton = page
      .getByRole('button', { name: 'Create Policy' })
      .last();
    await expect(submitButton).toBeEnabled();

    // Test cancel functionality
    await cancelButton.click();
    await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
  });

  test('form validation works correctly', async ({ page }) => {
    await page.goto('/device-policies');
    await page.getByRole('button', { name: 'Create Policy' }).click();

    // Wait for modal to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    // Fill in required fields
    await page.locator('input[name="name"]').fill('Test Policy');
    await page.locator('input[name="description"]').fill('Test Description');
    await page.locator('select[name="policy_type"]').selectOption('kiosk');

    // Configuration should be auto-populated and valid
    const submitButton = page
      .getByRole('button', { name: 'Create Policy' })
      .last();
    await expect(submitButton).toBeEnabled();
  });
});
