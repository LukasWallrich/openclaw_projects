const { test, expect } = require('@playwright/test');
const { pathToFileURL } = require('url');
const path = require('path');

const prototypeUrl = process.env.CROSSROADS_URL || pathToFileURL(path.resolve(__dirname, '..', 'index.html')).href;

test.beforeEach(async ({ page }) => {
  await page.goto(prototypeUrl);
});

test('adapts room supply to attendance', async ({ page }) => {
  await expect(page).toHaveTitle(/Crossroads/);
  await expect(page.locator('.room')).toHaveCount(9);
  await expect(page.locator('.room.closed')).toHaveCount(2);

  await page.getByRole('button', { name: '18 people' }).click();
  await expect(page.locator('.room.closed')).toHaveCount(5);
  await expect(page.getByText('15 in conversations · 3 in the lobby · 4 rooms open')).toBeVisible();

  await page.getByRole('button', { name: '72 people' }).click();
  await expect(page.locator('.room.closed')).toHaveCount(0);
});

test('supports selecting, walking, and Meet handoff', async ({ page }) => {
  await page.locator('.room[data-id="eval"]').click();
  await expect(page.getByRole('heading', { name: 'Evaluation headaches' })).toBeVisible();
  await page.getByRole('button', { name: 'Walk to this room' }).click();
  await expect(page.getByRole('button', { name: 'Open Google Meet ↗' })).toBeEnabled();
  await expect(page.getByText('You are at Evaluation headaches')).toBeVisible();

  await page.getByRole('button', { name: 'Open Google Meet ↗' }).click();
  await expect(page.getByRole('heading', { name: 'Meet opens next' })).toBeVisible();
});

test('offers interest-aware automatic routing', async ({ page }) => {
  await page.getByRole('button', { name: 'Take me somewhere' }).click();
  await expect(page.getByRole('button', { name: 'Open Google Meet ↗' })).toBeEnabled();
  await expect(page.locator('#yourStatus')).not.toHaveText(/lobby/);
});

test('keyboard navigation and mobile layout remain usable', async ({ page }) => {
  await page.locator('#map').focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('heading', { name: 'Human-centred automation' })).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('button', { name: 'Open Google Meet ↗' })).toBeEnabled();

  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('heading', { name: /Find the conversation/ })).toBeVisible();
  await expect(page.locator('.workspace')).toBeVisible();
  await expect(page.locator('body')).toHaveJSProperty('scrollWidth', 390);
});
