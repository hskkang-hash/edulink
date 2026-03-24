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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (isApiPath(url.pathname)) {
      const targetUrl = `${env.BACKEND_ORIGIN}${url.pathname}${url.search}`;
      const headers = new Headers(request.headers);
      headers.set("x-forwarded-host", url.host);
      headers.set("x-forwarded-proto", url.protocol.replace(":", ""));

      // localtunnel returns an interstitial HTML page unless this header is present.
      if ((env.BACKEND_ORIGIN || "").includes(".loca.lt")) {
        headers.set("bypass-tunnel-reminder", "true");
      }

      const proxiedRequest = new Request(targetUrl, {
        method: request.method,
        headers,
        body: request.body,
        redirect: "follow",
      });

      try {
        const backendResponse = await fetch(proxiedRequest);
        const contentType = (backendResponse.headers.get("content-type") || "").toLowerCase();

        if (backendResponse.ok) {
          return backendResponse;
        }

        if (backendResponse.status >= 500 || contentType.includes("text/html")) {
          const text = await backendResponse.text();
          const tunnelUnavailable = /tunnel unavailable|localtunnel|loca\.lt|service unavailable/i.test(text);

          if (tunnelUnavailable || contentType.includes("text/html")) {
            return jsonError(
              backendResponse.status || 503,
              `Backend is temporarily unavailable (${backendResponse.status || 503}). Please retry in a moment.`,
              env.BACKEND_ORIGIN,
            );
          }
        }

        return backendResponse;
      } catch (error) {
        return jsonError(503, "Backend is temporarily unavailable (503). Please retry in a moment.", env.BACKEND_ORIGIN);
      }
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
