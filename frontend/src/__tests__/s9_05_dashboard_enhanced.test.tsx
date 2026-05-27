import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// TEST 1: Failure panel renders error details
it('should show failure details', async () => {
  const { default: FailurePanel } = await import('../components/build/FailurePanel');
  render(<FailurePanel
    taskName="S3-04 Edit Modal"
    errorOutput="AssertionError: expected 200 but got 401"
    onRetry={() => {}}
    onEditPrompt={() => {}}
    onCancel={() => {}}
  />);
  expect(screen.getByText(/s3-04/i) || screen.getByText(/edit modal/i)).toBeDefined();
  expect(screen.getByText(/assertionerror/i)).toBeDefined();
  expect(screen.getByText(/Retry Failed Task/i)).toBeDefined();
});

// TEST 2: Queue position renders
it('should show queue position', async () => {
  const { default: QueuePosition } = await import('../components/build/QueuePosition');
  render(<QueuePosition position={3} estimatedWait="~2 hours" onCancel={() => {}} />);
  expect(screen.getByText('3') || screen.getByText(/#3/)).toBeDefined();
  expect(screen.getByText(/2 hours/i)).toBeDefined();
});

// TEST 3: Rate limit countdown renders
it('should show countdown to resume', async () => {
  const { default: RateLimitCountdown } = await import('../components/build/RateLimitCountdown');
  render(<RateLimitCountdown resumeAt="2026-05-27T19:00:00Z" />);
  expect(screen.getByText(/paused/i)).toBeDefined();
});

// TEST 4: Rate limit reassures progress is saved
it('should show progress saved message', async () => {
  const { default: RateLimitCountdown } = await import('../components/build/RateLimitCountdown');
  render(<RateLimitCountdown resumeAt="2026-05-27T19:00:00Z" />);
  expect(screen.getByText(/saved|safe|close/i)).toBeDefined();
});

// TEST 5: Failure panel has retry and edit buttons
it('should have retry and edit prompt buttons', async () => {
  const onRetry = vi.fn();
  const onEdit = vi.fn();
  const { default: FailurePanel } = await import('../components/build/FailurePanel');
  render(<FailurePanel taskName="Task" errorOutput="Error" onRetry={onRetry} onEditPrompt={onEdit} onCancel={() => {}} />);
  expect(screen.getByText(/Retry Failed Task/i)).toBeDefined();
  expect(screen.getByText(/Edit/i)).toBeDefined();
});
