import { test, expect } from '@playwright/test';

test.describe('S2C-17: Enterprise Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to admin dashboard
    await page.goto('/');

    // Wait for navigation to load
    await page.waitForSelector('[data-testid="sidebar-nav"]', {
      timeout: 5000,
    });
  });

  test('should display enterprise navigation sections in sidebar', async ({
    page,
  }) => {
    // Check that enterprise navigation items are visible
    const expectedNavItems = [
      'Settings',
      'Identity & Access',
      'RBAC & Permissions',
      'Integrations Hub',
      'Secrets & Keys Vault',
      'Audit Logs',
      'Data Governance',
      'Incident Center',
      'API Usage & Limits',
      'Fleet Health',
      'Announcements',
      'Notifications',
      'Feature Flags',
      'Experiments',
      'Reports & Analytics',
    ];

    for (const navItem of expectedNavItems) {
      await expect(page.getByRole('link', { name: navItem })).toBeVisible();
    }
  });

  test('should navigate to Identity & Access Management page', async ({
    page,
  }) => {
    // Click on Identity & Access navigation item
    await page.getByRole('link', { name: 'Identity & Access' }).click();

    // Verify navigation to correct page
    await expect(page).toHaveURL('/identity');

    // Verify page content loads
    await expect(
      page.getByRole('heading', { name: 'Identity & Access Management' })
    ).toBeVisible();

    // Check that API call buttons are present
    await expect(
      page.getByRole('button', { name: 'Create User' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Manage Roles' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Security Settings' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Audit Logs' })
    ).toBeVisible();
  });

  test('should navigate to RBAC & Permissions page', async ({ page }) => {
    // Click on RBAC & Permissions navigation item
    await page.getByRole('link', { name: 'RBAC & Permissions' }).click();

    // Verify navigation to correct page
    await expect(page).toHaveURL('/rbac');

    // Verify page content loads
    await expect(
      page.getByRole('heading', { name: 'RBAC & Permissions' })
    ).toBeVisible();

    // Check that API call buttons are present
    await expect(
      page.getByRole('button', { name: 'Create Role' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Assign Permissions' })
    ).toBeVisible();
  });

  test('should navigate to Secrets & Keys Vault page', async ({ page }) => {
    // Click on Secrets & Keys Vault navigation item
    await page.getByRole('link', { name: 'Secrets & Keys Vault' }).click();

    // Verify navigation to correct page
    await expect(page).toHaveURL('/secrets');

    // Verify page content loads
    await expect(
      page.getByRole('heading', { name: 'Secrets & Keys Vault' })
    ).toBeVisible();

    // Check that API call buttons are present
    await expect(
      page.getByRole('button', { name: 'Add Secret' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Rotate Keys' })
    ).toBeVisible();
  });

  test('should navigate to API Usage & Limits page', async ({ page }) => {
    // Click on API Usage & Limits navigation item
    await page.getByRole('link', { name: 'API Usage & Limits' }).click();

    // Verify navigation to correct page
    await expect(page).toHaveURL('/operations/api-usage');

    // Verify page content loads
    await expect(
      page.getByRole('heading', { name: 'API Usage & Rate Limits' })
    ).toBeVisible();

    // Check that API call buttons are present
    await expect(
      page.getByRole('button', { name: 'View Metrics' })
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Configure Limits' })
    ).toBeVisible();
  });

  test('should trigger API call alerts when buttons are clicked', async ({
    page,
  }) => {
    // Navigate to Identity page
    await page.getByRole('link', { name: 'Identity & Access' }).click();
    await page.waitForURL('/identity');

    // Set up dialog listener
    page.on('dialog', async dialog => {
      expect(dialog.type()).toBe('alert');
      expect(dialog.message()).toContain('API call needed');
      await dialog.accept();
    });

    // Test Create User button triggers API call placeholder
    await page.getByRole('button', { name: 'Create User' }).click();

    // Test Manage Roles button triggers API call placeholder
    await page.getByRole('button', { name: 'Manage Roles' }).click();

    // Test Security Settings button triggers API call placeholder
    await page.getByRole('button', { name: 'Security Settings' }).click();

    // Test Audit Logs button triggers API call placeholder
    await page.getByRole('button', { name: 'Audit Logs' }).click();
  });

  test('should maintain enterprise navigation organization', async ({
    page,
  }) => {
    // Verify navigation sections are properly organized
    const sidebar = page.locator('[data-testid="sidebar-nav"]');

    // Check that enterprise sections appear in correct order
    const navLinks = await sidebar.locator('a').allTextContents();

    // Verify key enterprise sections appear after core sections
    const enterpriseStartIndex = navLinks.findIndex(link =>
      link.includes('Settings')
    );
    const identityIndex = navLinks.findIndex(link =>
      link.includes('Identity & Access')
    );
    const rbacIndex = navLinks.findIndex(link =>
      link.includes('RBAC & Permissions')
    );
    const secretsIndex = navLinks.findIndex(link =>
      link.includes('Secrets & Keys Vault')
    );

    expect(enterpriseStartIndex).toBeGreaterThan(0);
    expect(identityIndex).toBeGreaterThan(enterpriseStartIndex);
    expect(rbacIndex).toBeGreaterThan(identityIndex);
    expect(secretsIndex).toBeGreaterThan(rbacIndex);
  });
});
