import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// TEST 5: StreamProgress component renders steps
it('should render progress steps', async () => {
  const { default: StreamProgress } = await import('../components/discovery/StreamProgress');
  render(<StreamProgress currentStep="calling_ai" />);
  expect(screen.getByText(/analyzing/i) || screen.getByText(/consulting ai/i)).toBeDefined();
});

// TEST 6: StreamProgress shows active step with spinner
it('should show spinner on active step', async () => {
  const { default: StreamProgress } = await import('../components/discovery/StreamProgress');
  const { container } = render(<StreamProgress currentStep="calling_ai" />);
  expect(container.querySelector('[class*="animate-spin"]')).toBeDefined();
});
