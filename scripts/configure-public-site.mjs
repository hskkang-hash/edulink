import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(process.cwd());
const configPath = resolve(root, "public-site.config.json");

const defaults = {
  siteUrl: "https://example.com",
  adsPublisherId: "pub-REPLACE_WITH_PUBLISHER_ID",
  adsRelation: "DIRECT",
  adsCertificationId: "f08c47fec0942fa0",
};

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      out[key] = "true";
      continue;
    }
    out[key] = next;
    i += 1;
  }
  return out;
}

function normalizeSiteUrl(raw) {
  const text = String(raw || "").trim();
  if (!text) return "";
  const withProtocol = /^https?:\/\//i.test(text) ? text : `https://${text}`;
  return withProtocol.replace(/\/+$/, "");
}

const args = parseArgs(process.argv.slice(2));
const existing = existsSync(configPath)
  ? JSON.parse(readFileSync(configPath, "utf8"))
  : defaults;

const siteUrl = normalizeSiteUrl(args.siteUrl || process.env.SITE_URL || existing.siteUrl || defaults.siteUrl);
const adsPublisherId = String(args.adsPublisherId || process.env.ADS_PUBLISHER_ID || existing.adsPublisherId || defaults.adsPublisherId).trim();
const adsRelation = String(args.adsRelation || process.env.ADS_RELATION || existing.adsRelation || defaults.adsRelation).trim() || "DIRECT";
const adsCertificationId = String(
  args.adsCertificationId || process.env.ADS_CERTIFICATION_ID || existing.adsCertificationId || defaults.adsCertificationId
).trim() || defaults.adsCertificationId;

const nextConfig = {
  siteUrl,
  adsPublisherId,
  adsRelation,
  adsCertificationId,
};

writeFileSync(configPath, `${JSON.stringify(nextConfig, null, 2)}\n`, "utf8");

console.log("Updated public-site.config.json");
console.log(`- siteUrl: ${siteUrl}`);
console.log(`- adsPublisherId: ${adsPublisherId}`);
console.log(`- adsRelation: ${adsRelation}`);
console.log(`- adsCertificationId: ${adsCertificationId}`);
