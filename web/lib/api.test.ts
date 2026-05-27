import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch, clearToken, getToken, saveToken } from "@/lib/api";

afterEach(() => {
  clearToken();
  vi.restoreAllMocks();
});

describe("token storage", () => {
  it("saves and clears the token", () => {
    saveToken("abc");
    expect(getToken()).toBe("abc");
    clearToken();
    expect(getToken()).toBeNull();
  });
});

describe("apiFetch", () => {
  it("attaches the bearer token when present", async () => {
    saveToken("tok123");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ ok: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/auth/me");

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer tok123");
  });

  it("throws on a non-ok response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401, text: async () => "nope" }),
    );
    await expect(apiFetch("/auth/me")).rejects.toThrow("401");
  });
});
