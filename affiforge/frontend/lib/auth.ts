const ACCESS_TOKEN_KEY = "access_token";

function setAccessTokenCookie(token: string): void {
  document.cookie = `${ACCESS_TOKEN_KEY}=${encodeURIComponent(token)}; Path=/; SameSite=Lax`;
}

function clearAccessTokenCookie(): void {
  document.cookie = `${ACCESS_TOKEN_KEY}=; Path=/; Max-Age=0; SameSite=Lax`;
}

function getAccessTokenFromCookie(): string | null {
  const prefix = `${ACCESS_TOKEN_KEY}=`;
  const parts = document.cookie.split(";");
  for (const rawPart of parts) {
    const part = rawPart.trim();
    if (part.startsWith(prefix)) {
      const value = part.slice(prefix.length);
      return value ? decodeURIComponent(value) : null;
    }
  }
  return null;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const fromStorage = window.localStorage.getItem(ACCESS_TOKEN_KEY);
  if (fromStorage) {
    return fromStorage;
  }
  return getAccessTokenFromCookie();
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  setAccessTokenCookie(token);
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  clearAccessTokenCookie();
}

export function isAuthenticated(): boolean {
  return Boolean(getAccessToken());
}
