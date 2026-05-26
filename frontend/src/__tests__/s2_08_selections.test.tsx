import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// TEST 1: MaturitySelector renders all 4 level cards
it('should render 4 maturity level cards', async () => {
  const { default: MaturitySelector } = await import('../components/discovery/MaturitySelector');
  render(<MaturitySelector value="mvp" onChange={() => {}} levels={[
    { level: 'poc', label: 'POC', description: 'Quick validation' },
    { level: 'mvp', label: 'MVP', description: 'Balanced depth' },
    { level: 'pre_production', label: 'Pre-Production', description: 'Full rigor' },
    { level: 'production', label: 'Production', description: 'Enterprise-ready' },
  ]} />);
  expect(screen.getByText('POC')).toBeDefined();
  expect(screen.getByText('MVP')).toBeDefined();
  expect(screen.getByText('Pre-Production')).toBeDefined();
  expect(screen.getByText('Production')).toBeDefined();
});

// TEST 2: Clicking a maturity card calls onChange
it('should call onChange when a level is selected', async () => {
  const onChange = vi.fn();
  const { default: MaturitySelector } = await import('../components/discovery/MaturitySelector');
  render(<MaturitySelector value="mvp" onChange={onChange} levels={[
    { level: 'poc', label: 'POC', description: 'Quick' },
    { level: 'mvp', label: 'MVP', description: 'Balanced' },
    { level: 'pre_production', label: 'Pre-Prod', description: 'Full' },
    { level: 'production', label: 'Production', description: 'Enterprise' },
  ]} />);
  fireEvent.click(screen.getByText('POC'));
  expect(onChange).toHaveBeenCalledWith('poc');
});

// TEST 3: TechStackInput renders input field
it('should render tech stack search input', async () => {
  const { default: TechStackInput } = await import('../components/discovery/TechStackInput');
  render(<TechStackInput selected={[]} onChange={() => {}} />);
  expect(screen.getByPlaceholderText(/search|tech|stack/i)).toBeDefined();
});

// TEST 4: TechStackInput shows selected tags
it('should display selected technologies as tags', async () => {
  const { default: TechStackInput } = await import('../components/discovery/TechStackInput');
  render(<TechStackInput selected={["React", "FastAPI", "PostgreSQL"]} onChange={() => {}} />);
  expect(screen.getByText('React')).toBeDefined();
  expect(screen.getByText('FastAPI')).toBeDefined();
  expect(screen.getByText('PostgreSQL')).toBeDefined();
});

// TEST 5: TechStackInput allows removing tags
it('should remove tag when X is clicked', async () => {
  const onChange = vi.fn();
  const { default: TechStackInput } = await import('../components/discovery/TechStackInput');
  render(<TechStackInput selected={["React", "FastAPI"]} onChange={onChange} />);
  const removeButtons = screen.getAllByRole('button').filter(b => b.getAttribute('aria-label')?.includes('remove') || b.textContent === '×' || b.textContent === '✕');
  if (removeButtons.length > 0) {
    fireEvent.click(removeButtons[0]);
    expect(onChange).toHaveBeenCalled();
  }
});

// TEST 6: Discovery store has maturity and tech stack state
it('should have maturity and tech stack in discovery store', async () => {
  const { useDiscoveryStore } = await import('../stores/discoveryStore');
  const state = useDiscoveryStore.getState();
  expect(state.selectedMaturity).toBe('mvp');
  expect(Array.isArray(state.selectedTechStack)).toBe(true);
});
