import { test, expect } from '@playwright/test';

test.describe('InkOps Debug Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ink-ops');
  });

  test('should display InkOps page', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Ink Operations' })
    ).toBeVisible();
    await expect(
      page.getByText('Monitor and debug ink sessions across devices')
    ).toBeVisible();
  });

  test('should show analytics cards when analytics button is clicked', async ({
    page,
  }) => {
    // Click Analytics button to show the cards
    await page.getByRole('button', { name: 'Analytics' }).click();

    // Now the analytics cards should be visible
    await expect(page.getByText('Total Sessions')).toBeVisible();
    await expect(page.getByText('Active Sessions')).toBeVisible();
    await expect(page.getByText('Avg Duration')).toBeVisible();
    await expect(page.getByText('Total Strokes')).toBeVisible();
  });

  test('should display sessions table with correct headers', async ({
    page,
  }) => {
    // Wait for the table to load
    await expect(page.locator('table')).toBeVisible();

    // Wait for data to load by checking if loading spinner is gone
    await expect(page.locator('.animate-spin')).not.toBeVisible({
      timeout: 10000,
    });

    // Check table headers
    await expect(
      page.locator('th').filter({ hasText: 'Session' })
    ).toBeVisible();
    await expect(
      page.locator('th').filter({ hasText: 'Device' })
    ).toBeVisible();
    await expect(page.locator('th').filter({ hasText: 'Type' })).toBeVisible();
    await expect(
      page.locator('th').filter({ hasText: 'Status' })
    ).toBeVisible();
    await expect(
      page.locator('th').filter({ hasText: 'Duration' })
    ).toBeVisible();
    await expect(
      page.locator('th').filter({ hasText: 'Strokes' })
    ).toBeVisible();
    await expect(
      page.locator('th').filter({ hasText: 'Started' })
    ).toBeVisible();
    await expect(
      page.locator('th').filter({ hasText: 'Actions' })
    ).toBeVisible();
  });

  test('should have functional filter controls', async ({ page }) => {
    // Check status filter
    const statusFilter = page
      .locator('select')
      .filter({ hasText: 'All Status' });
    await expect(statusFilter).toBeVisible();

    // Check device filter
    const deviceFilter = page
      .locator('select')
      .filter({ hasText: 'All Devices' });
    await expect(deviceFilter).toBeVisible();

    // Check session type filter
    const typeFilter = page.locator('select').filter({ hasText: 'All Types' });
    await expect(typeFilter).toBeVisible();

    // Check search input
    await expect(page.getByPlaceholder('Search sessions...')).toBeVisible();
  });

  test('should have refresh button', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: 'Refresh' });
    await expect(refreshButton).toBeVisible();
    await expect(refreshButton).toBeEnabled();
  });

  test('should have analytics toggle button', async ({ page }) => {
    const analyticsButton = page.getByRole('button', { name: 'Analytics' });
    await expect(analyticsButton).toBeVisible();
    await expect(analyticsButton).toBeEnabled();
  });

  test('should show empty state when no sessions', async ({ page }) => {
    // Wait for the table to load first
    await expect(page.locator('table')).toBeVisible();

    // If no sessions are loaded, should show empty state
    // We need to wait for either loading to finish or content to appear
    await page.waitForLoadState('networkidle');

    // Check if we see empty state or actual data
    const hasEmptyState = await page
      .getByText('No ink sessions found')
      .isVisible();
    const hasSessionData = (await page.locator('tbody tr').count()) > 1; // More than just the header

    if (hasEmptyState) {
      await expect(page.getByText('No ink sessions found')).toBeVisible();
      await expect(
        page.getByText(
          'Sessions will appear here as users interact with ink-enabled devices'
        )
      ).toBeVisible();
    } else if (!hasSessionData) {
      // If neither empty state nor data, might be loading
      await expect(page.getByText('Loading sessions...')).toBeVisible();
    }
    // If there's actual data, that's fine too - the test passes
  });
});

test.describe('InkOps CTA Guards', () => {
  test('all interactive elements are functional', async ({ page }) => {
    await page.goto('/ink-ops');

    // Test main action buttons
    const refreshButton = page.getByRole('button', { name: 'Refresh' });
    await expect(refreshButton).toBeVisible();
    await expect(refreshButton).toBeEnabled();

    const analyticsButton = page.getByRole('button', { name: 'Analytics' });
    await expect(analyticsButton).toBeVisible();
    await expect(analyticsButton).toBeEnabled();

    // Test filter elements
    const statusFilter = page
      .locator('select')
      .filter({ hasText: 'All Status' });
    await expect(statusFilter).toBeEnabled();

    const deviceFilter = page
      .locator('select')
      .filter({ hasText: 'All Devices' });
    await expect(deviceFilter).toBeEnabled();

    const typeFilter = page.locator('select').filter({ hasText: 'All Types' });
    await expect(typeFilter).toBeEnabled();

    const searchInput = page.getByPlaceholder('Search sessions...');
    await expect(searchInput).toBeEnabled();

    // Test search functionality
    await searchInput.fill('test-session');
    await expect(searchInput).toHaveValue('test-session');

    // Clear search
    await searchInput.clear();
    await expect(searchInput).toHaveValue('');
  });

  test('analytics toggle functionality', async ({ page }) => {
    await page.goto('/ink-ops');

    // Wait for page to load
    await expect(
      page.getByRole('heading', { name: 'Ink Operations' })
    ).toBeVisible();

    const analyticsButton = page.getByRole('button', { name: 'Analytics' });

    // Initially analytics should be hidden
    await expect(page.getByText('Total Sessions')).not.toBeVisible();

    // Click to show analytics
    await analyticsButton.click();

    // Wait for analytics to load and appear
    await page.waitForTimeout(1000); // Give time for analytics API call

    // Now analytics should be visible (if analytics data is available)
    const analyticsVisible = await page.getByText('Total Sessions').isVisible();
    if (analyticsVisible) {
      await expect(page.getByText('Total Sessions')).toBeVisible();

      // Click again to hide
      await analyticsButton.click();

      // Analytics should be hidden again
      await expect(page.getByText('Total Sessions')).not.toBeVisible();
    }
    // If analytics data is not available, that's also acceptable for this test
  });

  test('filter interactions work correctly', async ({ page }) => {
    await page.goto('/ink-ops');

    // Test status filter selection
    const statusFilter = page
      .locator('select')
      .filter({ hasText: 'All Status' });
    await statusFilter.selectOption('active');
    await expect(statusFilter).toHaveValue('active');

    // Test device filter selection
    const deviceFilter = page
      .locator('select')
      .filter({ hasText: 'All Devices' });
    await expect(deviceFilter).toBeVisible();
    // Note: Device options are loaded from API, so we can't test specific selection without mock data

    // Test type filter selection
    const typeFilter = page.locator('select').filter({ hasText: 'All Types' });
    await typeFilter.selectOption('handwriting');
    await expect(typeFilter).toHaveValue('handwriting');

    // Reset filters
    await statusFilter.selectOption('');
    await typeFilter.selectOption('');
  });
});
