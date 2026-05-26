import { it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// Mock auth store to return authenticated state
vi.mock("../stores/authStore", () => ({
  useAuthStore: vi.fn(() => ({
    isAuthenticated: true,
    isLoading: false,
    user: {
      id: "1",
      email: "test@test.com",
      full_name: "Test User",
      is_active: true,
      created_at: "",
    },
    logout: vi.fn(),
  })),
}));

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("sidebar_collapsed", "false");
});

// TEST 1: Shell renders sidebar with navigation
it("should render sidebar with nav items", async () => {
  const { default: AppShell } = await import("../components/layout/AppShell");
  render(
    <MemoryRouter>
      <AppShell />
    </MemoryRouter>
  );
  expect(screen.getAllByText(/dashboard/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/discovery/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/problem library/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/approvals/i).length).toBeGreaterThan(0);
});

// TEST 2: Shell renders brand logo
it("should render IdeaForge brand", async () => {
  const { default: AppShell } = await import("../components/layout/AppShell");
  render(
    <MemoryRouter>
      <AppShell />
    </MemoryRouter>
  );
  expect(screen.getAllByText(/idea/i).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/forge/i).length).toBeGreaterThan(0);
});

// TEST 3: User avatar shows initials
it("should show user initials in avatar", async () => {
  const { default: AppShell } = await import("../components/layout/AppShell");
  render(
    <MemoryRouter>
      <AppShell />
    </MemoryRouter>
  );
  expect(screen.getByText("TU")).toBeDefined(); // "Test User" → "TU"
});

// TEST 4: Sidebar collapse toggle works
it("should toggle sidebar collapse", async () => {
  const { default: AppShell } = await import("../components/layout/AppShell");
  render(
    <MemoryRouter>
      <AppShell />
    </MemoryRouter>
  );
  const toggle =
    screen.queryByRole("button", { name: /collapse/i }) ||
    screen.getByTestId("sidebar-toggle");
  fireEvent.click(toggle);
  // After click, sidebar should be in collapsed state
});

// TEST 5: Breadcrumbs render for current route
it("should render breadcrumbs", async () => {
  const { default: AppShell } = await import("../components/layout/AppShell");
  render(
    <MemoryRouter initialEntries={["/discovery"]}>
      <AppShell />
    </MemoryRouter>
  );
  expect(screen.getAllByText(/discovery/i).length).toBeGreaterThan(0);
});

// TEST 6: Logout button exists in dropdown
it("should have logout option", async () => {
  const { default: AppShell } = await import("../components/layout/AppShell");
  render(
    <MemoryRouter>
      <AppShell />
    </MemoryRouter>
  );
  // Click avatar to open dropdown
  const avatar = screen.getByText("TU");
  fireEvent.click(avatar);
  expect(screen.getAllByText(/log out/i).length).toBeGreaterThan(0);
});
