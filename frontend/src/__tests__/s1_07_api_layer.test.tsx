import { describe, it, expect } from 'vitest';

describe("API Client Layer Tests", () => {
  // TEST 1: API client has correct base URL
  it('should configure base URL from env', async () => {
    const { default: apiClient } = await import('../services/api');
    expect(apiClient.defaults.baseURL).toBeDefined();
    expect(typeof apiClient.defaults.baseURL).toBe('string');
  });

  // TEST 2: Auth service exports all functions
  it('should export login, register, refreshToken, getCurrentUser', async () => {
    const authService = await import('../services/authService');
    expect(typeof authService.login).toBe('function');
    expect(typeof authService.register).toBe('function');
    expect(typeof authService.refreshToken).toBe('function');
    expect(typeof authService.getCurrentUser).toBe('function');
  });

  // TEST 3: Session service exports all functions
  it('should export session service functions', async () => {
    const sessionService = await import('../services/sessionService');
    expect(typeof sessionService.createSession).toBe('function');
    expect(typeof sessionService.getSession).toBe('function');
    expect(typeof sessionService.getUserSessions).toBe('function');
    expect(typeof sessionService.discoverPainPoints).toBe('function');
  });

  // TEST 4: Problem service exports all functions
  it('should export problem service functions', async () => {
    const problemService = await import('../services/problemService');
    expect(typeof problemService.generateProblems).toBe('function');
    expect(typeof problemService.getProblems).toBe('function');
    expect(typeof problemService.getProblem).toBe('function');
    expect(typeof problemService.updateProblem).toBe('function');
  });

  // TEST 5: Solution service exports all functions
  it('should export solution service functions', async () => {
    const solutionService = await import('../services/solutionService');
    expect(typeof solutionService.generateSolutions).toBe('function');
    expect(typeof solutionService.getSolutions).toBe('function');
    expect(typeof solutionService.getSolution).toBe('function');
    expect(typeof solutionService.approveSolution).toBe('function');
  });

  // TEST 6: Evaluation service exports all functions
  it('should export evaluation service functions', async () => {
    const evalService = await import('../services/evaluationService');
    expect(typeof evalService.runEvaluation).toBe('function');
    expect(typeof evalService.getEvaluation).toBe('function');
    expect(typeof evalService.updateRubric).toBe('function');
  });

  // TEST 7: Toast store works
  it('should add and remove toasts', async () => {
    const { useToastStore } = await import('../stores/toastStore');
    const { addToast, removeToast } = useToastStore.getState();
    addToast('success', 'Test message');
    let state = useToastStore.getState();
    expect(state.toasts.length).toBe(1);
    expect(state.toasts[0].message).toBe('Test message');
    expect(state.toasts[0].type).toBe('success');
    removeToast(state.toasts[0].id);
    state = useToastStore.getState();
    expect(state.toasts.length).toBe(0);
  });

  // TEST 8: All types are importable
  it('should export all TypeScript types', async () => {
    const types = await import('../types/api');
    expect(types).toBeDefined();
  });

  // TEST 9: Toast component renders
  it('should render toast notification', async () => {
    const { render, screen } = await import('@testing-library/react');
    const { default: Toast } = await import('../components/ui/Toast');
    render(<Toast type="success" message="It worked!" onClose={() => {}} />);
    expect(screen.getByText('It worked!')).toBeDefined();
  });

  // TEST 10: API client has request interceptor
  it('should have request interceptors configured', async () => {
    const { default: apiClient } = await import('../services/api');
    expect(apiClient.interceptors.request.handlers!.length).toBeGreaterThan(0);
  });

  // TEST 11: API client has response interceptor
  it('should have response interceptors configured', async () => {
    const { default: apiClient } = await import('../services/api');
    expect(apiClient.interceptors.response.handlers!.length).toBeGreaterThan(0);
  });
});
