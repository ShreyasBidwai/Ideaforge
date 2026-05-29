import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';

// TEST 6: discovery form shows optional guidance textarea
it('renders guidance textarea', async () => {
  const { default: Discovery } = await import('../pages/Discovery');
  render(<MemoryRouter><Discovery /></MemoryRouter>);
  expect(screen.getByText(/anything specific/i)).toBeDefined();
});
