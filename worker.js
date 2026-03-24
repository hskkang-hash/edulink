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

      const proxiedRequest = new Request(targetUrl, {
        method: request.method,
        headers,
        body: request.body,
        redirect: "follow",
      });

      return fetch(proxiedRequest);
    }

    return env.ASSETS.fetch(request);
  },
};
