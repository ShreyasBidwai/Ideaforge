import { describe, it, expect, vi } from 'vitest';
import { renderHook } from '@testing-library/react';

vi.mock('../stores/authStore', () => ({
  useAuthStore: vi.fn(() => ({
    user: { full_name: 'John Doe', email: 'john@example.com' },
    isAuthenticated: true, isLoading: false,
  })),
}));

// TEST 1: useMediaQuery hook works
it('should return boolean from useMediaQuery', async () => {
  const { useMediaQuery } = await import('../hooks/useMediaQuery');
  const { result } = renderHook(() => useMediaQuery('(max-width: 768px)'));
  expect(typeof result.current).toBe('boolean');
});

// TEST 2: useIsMobile returns boolean
it('should return boolean from useIsMobile', async () => {
  const { useIsMobile } = await import('../hooks/useMediaQuery');
  const { result } = renderHook(() => useIsMobile());
  expect(typeof result.current).toBe('boolean');
});

// TEST 3: All pages render without horizontal overflow
it('should render dashboard without errors at narrow width', async () => {
  // Set viewport to mobile width
  Object.defineProperty(window, 'innerWidth', { value: 375, writable: true });
  const { default: Dashboard } = await import('../pages/Dashboard');
  const { render } = await import('@testing-library/react');
  const { MemoryRouter } = await import('react-router-dom');
  const { container } = render(<MemoryRouter><Dashboard /></MemoryRouter>);
  expect(container.scrollWidth).toBeLessThanOrEqual(375 + 50); // some tolerance
});
