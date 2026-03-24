# AdSense Go-Live Runbook

Last Updated: 2026-03-24

## 1. Configure Production Values

Use one command with your real values:

```bash
npm run configure:public -- --siteUrl https://your-domain.com --adsPublisherId pub-1234567890123456
```

Optional:
- `--adsRelation DIRECT`
- `--adsCertificationId f08c47fec0942fa0`

## 2. Build and Validate

```bash
npm run build:release
```

Expected:
- `frontend/robots.txt` points to your real sitemap URL
- `frontend/sitemap.xml` uses real domain and includes content pages
- `frontend/ads.txt` contains real publisher ID
- strict validation passes

## 3. Deploy

```bash
npm run cf:deploy
```

## 4. Search Console Submission

1. Open Google Search Console and add your property.
2. Verify domain ownership.
3. Submit `https://your-domain.com/sitemap.xml`.
4. Request indexing for:
- `/`
- `/content-hub.html`
- policy pages (`/privacy.html`, `/terms.html`, `/contact.html`, `/adsense-disclosure.html`)

## 5. AdSense Pre-Submission Checklist

- Privacy, Terms, Contact, Ads disclosure pages are public.
- At least 20 indexable content pages are live.
- No placeholder values remain in robots/sitemap/ads.
- Navigation to policy and content hub is visible on homepage.
- No policy-violating content and no click-inducing ad placement.

## 6. Submit AdSense Review

Apply with your production domain and monitor policy center for feedback.
