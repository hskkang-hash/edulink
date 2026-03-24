import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { join, resolve } from "node:path";

const root = resolve(process.cwd());
const distDir = resolve(root, "dist");
const frontendDir = resolve(root, "frontend");
const assetsDir = resolve(root, "assets");
const contentDir = resolve(frontendDir, "content");
const publicSiteConfigPath = resolve(root, "public-site.config.json");

if (!existsSync(frontendDir)) {
  throw new Error("Missing frontend directory. Expected ./frontend");
}

function normalizeSiteUrl(siteUrl) {
  const raw = String(siteUrl || "").trim();
  if (!raw) return "https://example.com";
  const withProtocol = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  return withProtocol.replace(/\/+$/, "");
}

function loadPublicSiteConfig() {
  const defaults = {
    siteUrl: "https://example.com",
    adsPublisherId: "pub-REPLACE_WITH_PUBLISHER_ID",
    adsRelation: "DIRECT",
    adsCertificationId: "f08c47fec0942fa0",
  };

  if (!existsSync(publicSiteConfigPath)) {
    return defaults;
  }

  try {
    const parsed = JSON.parse(readFileSync(publicSiteConfigPath, "utf8"));
    return {
      ...defaults,
      ...parsed,
    };
  } catch (error) {
    throw new Error(`Invalid public-site.config.json: ${error.message}`);
  }
}

function syncPublicSiteFiles() {
  const config = loadPublicSiteConfig();
  const baseUrl = normalizeSiteUrl(config.siteUrl);

  const robotsTxt = [
    "User-agent: *",
    "Allow: /",
    "",
    `Sitemap: ${baseUrl}/sitemap.xml`,
    "",
  ].join("\n");

  const contentPaths = existsSync(contentDir)
    ? readdirSync(contentDir)
        .filter((name) => name.toLowerCase().endsWith(".html"))
        .map((name) => `/content/${name}`)
    : [];

  const paths = [
    "/",
    "/content-hub.html",
    "/about.html",
    "/privacy.html",
    "/terms.html",
    "/contact.html",
    "/adsense-disclosure.html",
    ...contentPaths,
  ];
  const sitemapBody = paths.map((path) => `  <url><loc>${baseUrl}${path}</loc></url>`).join("\n");
  const sitemapXml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    sitemapBody,
    "</urlset>",
    "",
  ].join("\n");

  const adsTxt = [
    `google.com, ${config.adsPublisherId}, ${config.adsRelation}, ${config.adsCertificationId}`,
    "",
  ].join("\n");

  writeFileSync(resolve(frontendDir, "robots.txt"), robotsTxt, "utf8");
  writeFileSync(resolve(frontendDir, "sitemap.xml"), sitemapXml, "utf8");
  writeFileSync(resolve(frontendDir, "ads.txt"), adsTxt, "utf8");

  return {
    baseUrl,
    adsPublisherId: config.adsPublisherId,
  };
}

function copyDirectoryRecursive(sourceDir, targetDir) {
  mkdirSync(targetDir, { recursive: true });

  for (const name of readdirSync(sourceDir)) {
    const sourcePath = join(sourceDir, name);
    const targetPath = join(targetDir, name);
    const stats = statSync(sourcePath);

    if (stats.isDirectory()) {
      copyDirectoryRecursive(sourcePath, targetPath);
      continue;
    }

    copyFileSync(sourcePath, targetPath);
  }
}

rmSync(distDir, { recursive: true, force: true });
mkdirSync(distDir, { recursive: true });

const syncSummary = syncPublicSiteFiles();

copyDirectoryRecursive(frontendDir, distDir);

if (existsSync(assetsDir)) {
  copyDirectoryRecursive(assetsDir, resolve(distDir, "assets"));
}

console.log("Static bundle ready in ./dist");
console.log(`Public site URL: ${syncSummary.baseUrl}`);
console.log(`AdSense publisher: ${syncSummary.adsPublisherId}`);
