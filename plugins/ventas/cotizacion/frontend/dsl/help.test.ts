import { describe, it, expect } from "vitest";
import { isHelpCommand } from "./help";

describe("isHelpCommand", () => {
  it("detects cotizar --help", () => {
    expect(isHelpCommand("cotizar --help")).toBe(true);
  });

  it("detects preview cotizar --help", () => {
    expect(isHelpCommand("preview cotizar --help")).toBe(true);
  });

  it("is case-insensitive", () => {
    expect(isHelpCommand("COTIZAR --HELP")).toBe(true);
  });

  it("does not flag normal commands", () => {
    expect(isHelpCommand("cotizar cliente Bohdan 400 Bombona1")).toBe(false);
  });
});
