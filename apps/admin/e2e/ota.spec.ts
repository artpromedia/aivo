import { test, expect } from '@playwright/test';

test.describe('OTA Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/ota');
  });

  test('should display OTA management page', async ({ page }) => {
    await expect(
      page.getByRole('heading', { name: 'Over-the-Air Updates' })
    ).toBeVisible();
    await expect(
      page.getByText('Manage firmware updates and deployment rollouts')
    ).toBeVisible();
  });

  test('should show create update button', async ({ page }) => {
    const createButton = page.getByRole('button', { name: 'Create Update' });
    await expect(createButton).toBeVisible();
    await expect(createButton).toBeEnabled();
  });

  test('should open firmware update creation form', async ({ page }) => {
    await page.getByRole('button', { name: 'Create Update' }).click();

    // Wait for modal overlay to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    await expect(
      page.getByRole('heading', { name: 'Create Firmware Update' })
    ).toBeVisible();
    await expect(page.getByText('Version')).toBeVisible();
    await expect(page.getByText('Description')).toBeVisible();
    await expect(page.getByText('Release Notes')).toBeVisible();
    await expect(page.getByText('File URL')).toBeVisible();
    await expect(page.getByText('Checksum')).toBeVisible();

    // Check for form inputs
    await expect(page.locator('input[name="version"]')).toBeVisible();
    await expect(page.locator('input[name="description"]')).toBeVisible();
    await expect(page.locator('textarea[name="release_notes"]')).toBeVisible();
    await expect(page.locator('input[name="file_url"]')).toBeVisible();
  });

  test('should validate firmware update form', async ({ page }) => {
    await page.getByRole('button', { name: 'Create Update' }).click();

    // Wait for modal to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    // Fill required fields
    await page.locator('input[name="version"]').fill('2.1.0');
    await page.locator('input[name="file_size"]').fill('1048576');
    await page
      .locator('input[name="description"]')
      .fill('Test firmware update');
    await page
      .locator('textarea[name="release_notes"]')
      .fill('Bug fixes and improvements');
    await page
      .locator('input[name="file_url"]')
      .fill('https://cdn.example.com/firmware.bin');
    await page.locator('input[name="checksum"]').fill('sha256:abc123def456');
    await page
      .locator('input[name="target_device_types"]')
      .fill('tablet, chromebook');

    const submitButton = page
      .getByRole('button', { name: 'Create Update' })
      .last();
    await expect(submitButton).toBeEnabled();
  });

  test('should display OTA stats cards', async ({ page }) => {
    await expect(page.getByText('Active Updates')).toBeVisible();
    await expect(page.getByText('Successful')).toBeVisible();
    await expect(page.getByText('Failed')).toBeVisible();
    await expect(page.getByText('In Progress')).toBeVisible();
  });

  test('should display deployment ring percentages', async ({ page }) => {
    await page.getByRole('button', { name: 'Create Update' }).click();

    // Wait for modal to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    await expect(page.getByText('Canary %')).toBeVisible();
    await expect(page.getByText('Early %')).toBeVisible();
    await expect(page.getByText('Broad %')).toBeVisible();
    await expect(page.getByText('Production %')).toBeVisible();

    // Check for the actual input fields and their default values
    await expect(page.locator('input[name="canary_percentage"]')).toBeVisible();
    await expect(page.locator('input[name="early_percentage"]')).toBeVisible();
    await expect(page.locator('input[name="broad_percentage"]')).toBeVisible();
    await expect(
      page.locator('input[name="production_percentage"]')
    ).toBeVisible();

    // Check default values
    await expect(page.locator('input[name="canary_percentage"]')).toHaveValue(
      '5'
    );
    await expect(page.locator('input[name="early_percentage"]')).toHaveValue(
      '25'
    );
    await expect(page.locator('input[name="broad_percentage"]')).toHaveValue(
      '75'
    );
    await expect(
      page.locator('input[name="production_percentage"]')
    ).toHaveValue('100');
  });

  test('should have refresh functionality', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: 'Refresh' });
    await expect(refreshButton).toBeVisible();
    await expect(refreshButton).toBeEnabled();
  });
});

test.describe('OTA CTA Guards', () => {
  test('all buttons have proper functionality', async ({ page }) => {
    await page.goto('/ota');

    // Test main action buttons
    const createButton = page
      .getByRole('button', { name: 'Create Update' })
      .first();
    await expect(createButton).toBeEnabled();

    const refreshButton = page.getByRole('button', { name: 'Refresh' });
    await expect(refreshButton).toBeEnabled();

    // Test form CTAs
    await createButton.click();

    // Wait for modal to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    const cancelButton = page.getByRole('button', { name: 'Cancel' });
    await expect(cancelButton).toBeEnabled();

    const submitButton = page
      .getByRole('button', { name: 'Create Update' })
      .last();
    await expect(submitButton).toBeEnabled();

    // Test cancel functionality
    await cancelButton.click();
    await expect(page.locator('.fixed.inset-0')).not.toBeVisible();
  });

  test('form submission requires all fields', async ({ page }) => {
    await page.goto('/ota');
    await page.getByRole('button', { name: 'Create Update' }).click();

    // Wait for modal to appear
    await expect(page.locator('.fixed.inset-0')).toBeVisible();

    // Check that form fields are required
    await expect(page.locator('input[name="version"]')).toHaveAttribute(
      'required'
    );
    await expect(page.locator('input[name="description"]')).toHaveAttribute(
      'required'
    );
    await expect(
      page.locator('textarea[name="release_notes"]')
    ).toHaveAttribute('required');
  });
});
