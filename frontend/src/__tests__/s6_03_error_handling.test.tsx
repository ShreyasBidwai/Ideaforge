import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';

// TEST 1: ErrorDisplay renders with message
it('should render error with title and message', async () => {
  const { default: ErrorDisplay } = await import('../components/ui/ErrorDisplay');
  render(<MemoryRouter><ErrorDisplay title="Oops" message="Something went wrong" /></MemoryRouter>);
  expect(screen.getByText('Oops')).toBeDefined();
  expect(screen.getByText('Something went wrong')).toBeDefined();
});

// TEST 2: ErrorDisplay retry button calls onRetry
it('should call onRetry when retry clicked', async () => {
  const onRetry = vi.fn();
  const { default: ErrorDisplay } = await import('../components/ui/ErrorDisplay');
  render(<MemoryRouter><ErrorDisplay title="Error" message="Failed" onRetry={onRetry} /></MemoryRouter>);
  fireEvent.click(screen.getByText(/retry|try again/i));
  expect(onRetry).toHaveBeenCalled();
});

// TEST 3: LoadingSpinner renders with message
it('should render spinner with message', async () => {
  const { default: LoadingSpinner } = await import('../components/ui/LoadingSpinner');
  render(<LoadingSpinner message="Loading data..." />);
  expect(screen.getByText('Loading data...')).toBeDefined();
});

// TEST 4: EmptyState renders with action
it('should render empty state with action button', async () => {
  const onAction = vi.fn();
  const { default: EmptyState } = await import('../components/ui/EmptyState');
  render(<EmptyState title="Nothing here" message="Get started" actionLabel="Create" onAction={onAction} />);
  expect(screen.getByText('Nothing here')).toBeDefined();
  fireEvent.click(screen.getByText('Create'));
  expect(onAction).toHaveBeenCalled();
});

// TEST 5: EmptyState renders without action
it('should render empty state without button when no action', async () => {
  const { default: EmptyState } = await import('../components/ui/EmptyState');
  render(<EmptyState title="Empty" message="Nothing to show" />);
  expect(screen.getByText('Empty')).toBeDefined();
  expect(screen.queryByRole('button')).toBeNull();
});

// TEST 6: ErrorBoundary catches errors
it('should catch rendering errors', async () => {
  const { default: ErrorBoundary } = await import('../components/ui/ErrorBoundary');
  const ThrowError = () => { throw new Error('Test error'); };
  // Suppress console.error for this test
  const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
  render(<ErrorBoundary><ThrowError /></ErrorBoundary>);
  expect(screen.getByText(/something went wrong/i)).toBeDefined();
  spy.mockRestore();
});
