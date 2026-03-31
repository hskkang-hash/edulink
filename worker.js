import { Container, getContainer } from "@cloudflare/containers";

// ---------------------------------------------------------------------------
// EduLinkBackend – Cloudflare Container that runs the Flask API server.
// Each named instance keeps its own SQLite database inside the container
// filesystem. In production consider attaching a persistent volume or
// migrating to Cloudflare D1 for true durability across restarts.
// ---------------------------------------------------------------------------
export class EduLinkBackend extends Container {
  defaultPort = 5000;
  sleepAfter = "30m";

  constructor(state, env) {
    super(state, env);
    // Env vars injected into the container at startup.
    // Set secrets with: npx wrangler secret put SECRET_KEY
    this.envVars = {
      PORT: "5000",
      DEBUG: "false",
      SECRET_KEY: env.SECRET_KEY || "dev-secret-replace-via-wrangler-secret",
      DATABASE_URL: "sqlite:////app/data/edulink.db",
      ALLOWED_CORS_ORIGINS: "https://edulinks.pro,https://www.edulinks.pro",
      EMAIL_ADAPTER_TYPE: String(env.EMAIL_ADAPTER_TYPE || "mock"),
    };
  }

  onStart() {
    console.log("[EduLinkBackend] container started");
  }

  onStop() {
    console.log("[EduLinkBackend] container stopped");
  }

  onError(error) {
    console.error("[EduLinkBackend] container error:", error);
  }
}

// Flask + SQLite need a stable, single container instance (singleton).
// getContainer() defaults to the 'cf-singleton-container' ID from the package.

const API_PREFIXES = [
  "/auth",
  "/api",
  "/sessions",
  "/postings",
  "/dashboard",
  "/district",
  "/instructor",
  "/applications",
  "/reviews",
  "/contracts",
  "/escrow",
  "/admin",
  "/sos",
  "/health",
];

function isApiPath(pathname) {
  return API_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

function buildBackendOrigins(env) {
  const primary = String(env.BACKEND_ORIGIN || "").trim();
  const fallbackRaw = String(env.BACKEND_ORIGIN_FALLBACKS || "");
  const candidates = [
    primary,
    ...fallbackRaw
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
  ].filter(Boolean);

  return [...new Set(candidates)];
}

async function fetchWithTimeout(request, timeoutMs) {
  const timeout = Number.isFinite(Number(timeoutMs)) ? Math.max(1000, Number(timeoutMs)) : 12000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(request, { signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (isApiPath(url.pathname)) {
      // -----------------------------------------------------------------------
      // Primary path: Cloudflare Container binding (set in wrangler.toml).
      // Falls back to BACKEND_ORIGIN env var for local dev or legacy tunnels.
      // -----------------------------------------------------------------------
      if (env.EDULINK_BACKEND) {
        try {
          const container = getContainer(env.EDULINK_BACKEND);
          return await container.fetch(request);
        } catch (containerErr) {
          console.error("[worker] container fetch failed:", containerErr);
          return jsonError(503, "Container backend unavailable. Please retry in a moment.", "edulink-backend");
        }
      }

      // -----------------------------------------------------------------------
      // Fallback path: external origin (BACKEND_ORIGIN / BACKEND_ORIGIN_FALLBACKS).
      // Used when the container binding is absent (local dev without Docker).
      // -----------------------------------------------------------------------
      const backendOrigins = buildBackendOrigins(env);
      if (!backendOrigins.length) {
        return jsonError(503, "Backend is not configured. Set BACKEND_ORIGIN or deploy with CF Containers.", "");
      }

      let lastUnavailableStatus = 503;

      for (const backendOrigin of backendOrigins) {
        const targetUrl = `${backendOrigin}${url.pathname}${url.search}`;
        const headers = new Headers(request.headers);
        headers.set("x-forwarded-host", url.host);
        headers.set("x-forwarded-proto", url.protocol.replace(":", ""));

        // localtunnel returns an interstitial HTML page unless this header is present.
        if (backendOrigin.includes(".loca.lt")) {
          headers.set("bypass-tunnel-reminder", "true");
        }

        const proxiedRequest = new Request(targetUrl, {
          method: request.method,
          headers,
          body: request.body,
          redirect: "follow",
        });

        try {
          const backendResponse = await fetchWithTimeout(proxiedRequest, env.BACKEND_TIMEOUT_MS || 12000);
          const contentType = (backendResponse.headers.get("content-type") || "").toLowerCase();

          if (backendResponse.ok) {
            return backendResponse;
          }

          if (backendResponse.status >= 500 || contentType.includes("text/html")) {
            const text = await backendResponse.text();
            const tunnelUnavailable = /tunnel unavailable|localtunnel|loca\.lt|service unavailable/i.test(text);
            lastUnavailableStatus = backendResponse.status || 503;

            // Retry next origin for tunnel/html/5xx failures.
            if (tunnelUnavailable || contentType.includes("text/html") || backendResponse.status >= 500) {
              continue;
            }
          }

          return backendResponse;
        } catch (error) {
          // Try next backend origin.
          continue;
        }
      }

      return jsonError(
        lastUnavailableStatus,
        `Backend is temporarily unavailable (${lastUnavailableStatus}). Please retry in a moment.`,
        backendOrigins[0],
      );
    }

    const assetResponse = await env.ASSETS.fetch(request);

    // Prevent stale HTML shell caching so clients always receive the latest frontend logic.
    if (url.pathname === "/" || url.pathname.endsWith(".html")) {
      const headers = new Headers(assetResponse.headers);
      headers.set("cache-control", "no-store, no-cache, must-revalidate, max-age=0");
      headers.set("pragma", "no-cache");
      headers.set("expires", "0");
      return new Response(assetResponse.body, {
        status: assetResponse.status,
        statusText: assetResponse.statusText,
        headers,
      });
    }

    return assetResponse;
  },
};

function jsonError(status, message, backendOrigin) {
  return new Response(
    JSON.stringify({
      error: message,
      errorCode: "BACKEND_UNAVAILABLE",
      status,
      backendOrigin,
    }),
    {
      status,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
      },
    },
  );
}
