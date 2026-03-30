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
      const backendOrigins = buildBackendOrigins(env);
      if (!backendOrigins.length) {
        return jsonError(503, "Backend is not configured. Please set BACKEND_ORIGIN.", "");
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
