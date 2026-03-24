import { existsSync, readFileSync, readdirSync } from "node:fs";
import { resolve } from "node:path";

const strict = process.argv.includes("--strict");
const root = resolve(process.cwd());
const configPath = resolve(root, "public-site.config.json");
const frontendDir = resolve(root, "frontend");
const contentDir = resolve(frontendDir, "content");

const errors = [];
const warnings = [];

function fail(message) {
  errors.push(message);
}

function warn(message) {
  warnings.push(message);
}

function readUtf8(filePath) {
  return readFileSync(filePath, "utf8");
}

if (!existsSync(configPath)) {
  fail("public-site.config.json is missing.");
}

const config = existsSync(configPath)
  ? JSON.parse(readUtf8(configPath))
  : {
      siteUrl: "",
      adsPublisherId: "",
    };

const siteUrl = String(config.siteUrl || "").trim().replace(/\/+$/, "");
const publisherId = String(config.adsPublisherId || "").trim();
const isPlaceholderDomain = siteUrl.includes("example.com") || !/^https?:\/\//i.test(siteUrl);
const isPlaceholderPublisher = publisherId.includes("REPLACE") || !publisherId.startsWith("pub-");

if (isPlaceholderDomain) {
  const msg = "siteUrl is placeholder or invalid in public-site.config.json.";
  strict ? fail(msg) : warn(msg);
}
if (isPlaceholderPublisher) {
  const msg = "adsPublisherId is placeholder or invalid in public-site.config.json.";
  strict ? fail(msg) : warn(msg);
}

const robotsPath = resolve(frontendDir, "robots.txt");
const sitemapPath = resolve(frontendDir, "sitemap.xml");
const adsPath = resolve(frontendDir, "ads.txt");
const hubPath = resolve(frontendDir, "content-hub.html");

for (const p of [robotsPath, sitemapPath, adsPath, hubPath]) {
  if (!existsSync(p)) {
    fail(`Missing required file: ${p}`);
  }
}

if (existsSync(robotsPath) && siteUrl) {
  const robots = readUtf8(robotsPath);
  const expected = `${siteUrl}/sitemap.xml`;
  if (!robots.includes(expected)) {
    fail(`robots.txt does not include expected sitemap URL: ${expected}`);
  }
}

if (existsSync(sitemapPath) && siteUrl) {
  const sitemap = readUtf8(sitemapPath);
  if (!sitemap.includes(`${siteUrl}/`)) {
    fail("sitemap.xml does not include configured base siteUrl.");
  }
}

if (existsSync(adsPath) && publisherId) {
  const ads = readUtf8(adsPath);
  if (!ads.includes(publisherId)) {
    fail("ads.txt does not include configured adsPublisherId.");
  }
}

const contentFiles = existsSync(contentDir)
  ? readdirSync(contentDir).filter((n) => n.toLowerCase().endsWith(".html"))
  : [];

if (contentFiles.length < 20) {
  fail(`Expected at least 20 content pages. Found ${contentFiles.length}.`);
}

if (existsSync(sitemapPath)) {
  const sitemap = readUtf8(sitemapPath);
  const missingContent = contentFiles.filter((name) => !sitemap.includes(`/content/${name}`));
  if (missingContent.length > 0) {
    fail(`sitemap.xml is missing ${missingContent.length} content URLs.`);
  }
}

console.log("Public site validation summary");
console.log(`- strict mode: ${strict}`);
console.log(`- siteUrl: ${siteUrl || "(empty)"}`);
console.log(`- adsPublisherId: ${publisherId || "(empty)"}`);
console.log(`- content pages: ${contentFiles.length}`);

if (warnings.length > 0) {
  console.log("Warnings:");
  for (const w of warnings) {
    console.log(`- ${w}`);
  }
}

if (errors.length > 0) {
  console.error("Errors:");
  for (const e of errors) {
    console.error(`- ${e}`);
  }
  process.exit(1);
}

console.log("Validation passed.");
