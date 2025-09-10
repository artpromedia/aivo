import { test, expect } from '@playwright/test';

test.describe('Device Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/devices');
  });

  test('should display device management page', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Device Management' })
    ).toBeVisible();
    await expect(
      page.getByText('Manage device enrollment, monitoring, and policies')
    ).toBeVisible();
  });

  test('should show enroll device button', async ({ page }) => {
    const enrollButton = page.getByRole('button', { name: 'Enroll Device' });
    await expect(enrollButton).toBeVisible();
    await expect(enrollButton).toBeEnabled();
  });

  test('should open enrollment form when enroll button is clicked', async ({
    page,
  }) => {
    await page.getByRole('button', { name: 'Enroll Device' }).first().click();

    // Wait for modal overlay to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    await expect(
      page.getByRole('heading', { name: 'Enroll New Device' })
    ).toBeVisible();
    await expect(page.getByText('Serial Number')).toBeVisible();
    await expect(page.getByText('Device Type')).toBeVisible();

    // Check for form inputs
    await expect(page.getByPlaceholder('Enter serial number')).toBeVisible();
    await expect(page.locator('select[name="device_type"]')).toBeVisible();
    await expect(page.getByPlaceholder('e.g. Classroom 101')).toBeVisible();

    // Test form submission functionality
    await page.getByPlaceholder('Enter serial number').fill('TEST-DEVICE-001');
    await page.locator('select[name="device_type"]').selectOption('tablet');
    await page.getByPlaceholder('e.g. Classroom 101').fill('Test Lab');

    const submitButton = page
      .getByRole('button', { name: 'Enroll Device' })
      .last();
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeEnabled();
  });

  test('should display device filters', async ({ page }) => {
    await expect(page.getByPlaceholder('Search devices...')).toBeVisible();
    await expect(
      page.locator('select').filter({ hasText: 'All Status' })
    ).toBeVisible();
    await expect(
      page.locator('select').filter({ hasText: 'All Types' })
    ).toBeVisible();
  });

  test('should have refresh functionality', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: 'Refresh' });
    await expect(refreshButton).toBeVisible();
    await expect(refreshButton).toBeEnabled();
  });

  test('should display device stats cards', async ({ page }) => {
    // Wait for page to load
    await expect(
      page.getByRole('heading', { name: 'Device Management' })
    ).toBeVisible();

    // Check for stats cards specifically, not the filter options
    await expect(page.locator('.grid').getByText('Online')).toBeVisible();
    await expect(page.locator('.grid').getByText('Offline')).toBeVisible();
    await expect(page.locator('.grid').getByText('Pending')).toBeVisible();
    await expect(page.locator('.grid').getByText('Total')).toBeVisible();
  });
});

test.describe('Device Management CTA Guards', () => {
  test('all buttons have proper handlers', async ({ page }) => {
    await page.goto('/devices');

    // Check that all buttons have onclick handlers or href attributes
    const buttons = await page.locator('button').all();

    for (const button of buttons) {
      const buttonText = await button.textContent();
      if (buttonText && buttonText.trim()) {
        // Verify button is not disabled (unless it's supposed to be)
        const isDisabled = await button.isDisabled();
        const hasOnClick = await button.evaluate(
          el => el.onclick !== null || el.getAttribute('data-testid') !== null
        );

        // All enabled buttons should have some form of interaction
        if (!isDisabled) {
          expect(
            hasOnClick || (await button.getAttribute('type')) === 'submit'
          ).toBeTruthy();
        }
      }
    }
  });
});
