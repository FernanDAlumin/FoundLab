import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the FoundLab dashboard shell", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "FoundLab" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Dashboard sections" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Assets", level: 2 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Backtest Runs", level: 2 })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Reports", level: 2 })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Open reports" })).not.toBeInTheDocument();
  });
});
