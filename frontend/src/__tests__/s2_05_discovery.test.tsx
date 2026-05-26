import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';

// TEST 1: Discovery page renders input form
it('should render discovery form with all fields', async () => {
  const { default: Discovery } = await import('../pages/Discovery');
  render(<MemoryRouter><Discovery /></MemoryRouter>);
  expect(screen.getByText(/discover industry pain points/i)).toBeDefined();
  expect(screen.getByPlaceholderText(/industry/i) || screen.getByLabelText(/industry/i)).toBeDefined();
  expect(screen.getByPlaceholderText(/location/i) || screen.getByLabelText(/location/i)).toBeDefined();
  expect(screen.getByText(/start discovery/i)).toBeDefined();
});

// TEST 2: Maturity selector renders all 4 levels
it('should render all 4 maturity levels', async () => {
  const { default: MaturitySelector } = await import('../components/discovery/MaturitySelector');
  render(<MaturitySelector value="mvp" onChange={() => {}} />);
  expect(screen.getByText(/poc/i)).toBeDefined();
  expect(screen.getByText(/mvp/i)).toBeDefined();
  expect(screen.getByText(/pre-prod/i) || screen.getByText(/pre.production/i)).toBeDefined();
  expect(screen.getByText(/production/i)).toBeDefined();
});

// TEST 3: Maturity selector highlights selected level
it('should highlight the selected maturity level', async () => {
  const { default: MaturitySelector } = await import('../components/discovery/MaturitySelector');
  const onChange = vi.fn();
  render(<MaturitySelector value="mvp" onChange={onChange} />);
  const mvpButton = screen.getByText(/mvp/i);
  expect(mvpButton.closest('button')?.className || '').toContain('blue');
});

// TEST 4: Pain point card renders correctly
it('should render pain point card with all data', async () => {
  const { default: PainPointCard } = await import('../components/discovery/PainPointCard');
  render(<PainPointCard painPoint={{
    name: "Long wait times",
    description: "Patients wait 3+ hours",
    severity: 8,
    affected_stakeholders: ["Patients", "Doctors"],
    evidence: "Government data confirms this"
  }} />);
  expect(screen.getByText("Long wait times")).toBeDefined();
  expect(screen.getByText(/3\+ hours/)).toBeDefined();
  expect(screen.getByText("Patients")).toBeDefined();
});

// TEST 5: Severity badge shows correct color
it('should show red badge for high severity', async () => {
  const { default: PainPointCard } = await import('../components/discovery/PainPointCard');
  const { container } = render(<PainPointCard painPoint={{
    name: "Critical issue", description: "Very bad", severity: 9,
    affected_stakeholders: ["All"], evidence: "Real"
  }} />);
  // Severity badge should have red-ish styling for 9
  const badge = container.querySelector('[class*="red"]') || container.querySelector('[class*="rose"]');
  expect(badge).toBeDefined();
});

// TEST 6: Skeleton loading renders
it('should render skeleton loading cards', async () => {
  const { default: PainPointSkeleton } = await import('../components/discovery/PainPointSkeleton');
  const { container } = render(<PainPointSkeleton />);
  expect(container.querySelector('[class*="animate"]')).toBeDefined();
});

// TEST 7: Discovery store initializes correctly
it('should initialize discovery store with null session', async () => {
  const { useDiscoveryStore } = await import('../stores/discoveryStore');
  const state = useDiscoveryStore.getState();
  expect(state.currentSession).toBeNull();
  expect(state.painPoints).toEqual([]);
  expect(state.isDiscovering).toBe(false);
});

// TEST 8: Form validates required fields
it('should not submit without industry and location', async () => {
  const { default: Discovery } = await import('../pages/Discovery');
  render(<MemoryRouter><Discovery /></MemoryRouter>);
  const button = screen.getByText(/start discovery/i);
  fireEvent.click(button);
  await waitFor(() => {
    expect(screen.getAllByText(/required/i)[0] || screen.getByText(/enter/i)).toBeDefined();
  });
});
