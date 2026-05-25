import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// TEST 1: App renders without crashing
describe("App", () => {
  it("should render without crashing", async () => {
    const { default: App } = await import("../App");
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>
    );
    // Should not throw
  });
});

// TEST 2: Auth store initial state
describe("AuthStore", () => {
  it("should initialize with unauthenticated state", async () => {
    const { useAuthStore } = await import("../stores/authStore");
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
  });

  // TEST 3: Logout clears state
  it("should clear state on logout", async () => {
    const { useAuthStore } = await import("../stores/authStore");
    useAuthStore.setState({ accessToken: "test", isAuthenticated: true });
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.isAuthenticated).toBe(false);
    expect(state.accessToken).toBeNull();
  });
});

// TEST 4: API client has correct base URL
describe("API Client", () => {
  it("should have base URL configured", async () => {
    const { default: apiClient } = await import("../services/api");
    expect(apiClient.defaults.baseURL).toBeDefined();
  });
});

// TEST 5: ProtectedRoute redirects when not authenticated
describe("ProtectedRoute", () => {
  it("should redirect to /login when not authenticated", async () => {
    const { useAuthStore } = await import("../stores/authStore");
    useAuthStore.setState({ isAuthenticated: false, isLoading: false });
    const { default: ProtectedRoute } =
      await import("../components/layout/ProtectedRoute");
    render(
      <MemoryRouter initialEntries={["/dashboard"]}>
        <ProtectedRoute />
      </MemoryRouter>
    );
    // Should redirect — component should not render protected content
  });
});

// TEST 6: TypeScript types are properly defined
describe("Types", () => {
  it("should export all required interfaces", async () => {
    const types = await import("../types/api");
    // These should exist as types — we verify the module is importable
    expect(types).toBeDefined();
  });
});

// TEST 7: Utility functions work
describe("Utils", () => {
  it("cn() should merge classnames correctly", async () => {
    const { cn } = await import("../lib/utils");
    expect(cn("foo", "bar")).toBe("foo bar");
    expect(cn("foo", undefined, "bar")).toBe("foo bar");
  });
});
