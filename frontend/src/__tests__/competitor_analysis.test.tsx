import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import React from 'react';
import { CompetitorAnalysis } from '../components/solutions/CompetitorAnalysis';

// Mock the Zustand store
const mockUseCompetitorStore = vi.fn();
vi.mock('../stores/competitorStore', () => ({
  useCompetitorStore: () => mockUseCompetitorStore(),
}));

describe('CompetitorAnalysis Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // TEST 1: Fetching analysis
  it('should fetch competitor analysis when loaded', async () => {
    const mockFetch = vi.fn();
    mockUseCompetitorStore.mockReturnValue({
      analyses: {},
      fetchAnalysis: mockFetch,
      runAnalysis: vi.fn(),
      refreshAnalysis: vi.fn(),
    });

    render(<CompetitorAnalysis solutionId="sol-123" />);

    // Check that fetch was called on mount
    expect(mockFetch).toHaveBeenCalledWith('sol-123');
  });

  // TEST 2: Displaying competitor details
  it('should render detailed competitor information', async () => {
    mockUseCompetitorStore.mockReturnValue({
      analyses: {
        'sol-123': {
          id: 'analysis-123',
          solution_id: 'sol-123',
          status: 'completed',
          market_summary: 'Innovative market',
          differentiation: 'Highly unique',
          competitors: [
            {
              name: 'Competitor A',
              description: 'A competitor doing X',
              pricing: '$49/mo',
              funding: '$1M Seed',
              strengths: ['Fast UI', 'Cheap'],
              weaknesses: ['Poor support'],
              url: 'https://competitor-a.com',
            }
          ],
          sources: [{ title: 'Source 1', url: 'https://source-1.com' }],
          error: null,
        }
      },
      fetchAnalysis: vi.fn(),
      runAnalysis: vi.fn(),
      refreshAnalysis: vi.fn(),
    });

    render(<CompetitorAnalysis solutionId="sol-123" />);

    expect(screen.getByText('Innovative market')).toBeDefined();
    expect(screen.getByText('Highly unique')).toBeDefined();
    expect(screen.getByText('Competitor A')).toBeDefined();
    expect(screen.getByText('A competitor doing X')).toBeDefined();
    expect(screen.getByText('$49/mo')).toBeDefined();
    expect(screen.getByText('$1M Seed')).toBeDefined();
    expect(screen.getByText('Fast UI')).toBeDefined();
    expect(screen.getByText('Poor support')).toBeDefined();
    expect(screen.getByText('Source 1')).toBeDefined();
  });

  // TEST 3: Background polling status changes (from researching to completed)
  it('should poll for analysis status changes when researching', async () => {
    vi.useFakeTimers();
    const mockFetch = vi.fn();
    mockUseCompetitorStore.mockReturnValue({
      analyses: {
        'sol-123': {
          id: 'analysis-123',
          solution_id: 'sol-123',
          status: 'researching',
          market_summary: null,
          differentiation: null,
          competitors: null,
          sources: null,
          error: null,
        }
      },
      fetchAnalysis: mockFetch,
      runAnalysis: vi.fn(),
      refreshAnalysis: vi.fn(),
    });

    render(<CompetitorAnalysis solutionId="sol-123" />);

    // Initially, it renders the researching spinner
    expect(screen.getByTestId('researching-spinner')).toBeDefined();

    // Advance time by 3 seconds
    act(() => {
      vi.advanceTimersByTime(3000);
    });

    // Check that fetchAnalysis was called again (polling)
    expect(mockFetch).toHaveBeenCalledTimes(2); // 1st on mount, 2nd on interval
  });

  // TEST 4: Graceful handling of missing API key (failed state with error)
  it('should gracefully handle failed status and display error message', async () => {
    mockUseCompetitorStore.mockReturnValue({
      analyses: {
        'sol-123': {
          id: 'analysis-123',
          solution_id: 'sol-123',
          status: 'failed',
          market_summary: null,
          differentiation: null,
          competitors: null,
          sources: null,
          error: 'Search not configured',
        }
      },
      fetchAnalysis: vi.fn(),
      runAnalysis: vi.fn(),
      refreshAnalysis: vi.fn(),
    });

    render(<CompetitorAnalysis solutionId="sol-123" />);

    expect(screen.getByText('Research Failed')).toBeDefined();
    expect(screen.getByText('Search not configured')).toBeDefined();
  });
});
