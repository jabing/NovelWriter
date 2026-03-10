import { test as base } from '@playwright/test';

export const test = base.extend({
  // Custom fixtures can be added here
  // For example: login state, test data, etc.
});

export { expect } from '@playwright/test';
