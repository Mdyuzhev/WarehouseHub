# TASK: Fix hardcoded addresses — remove K3s ports, add homelab support

## Context

Frontend determines API URL at runtime via a script in `index.html`.
This script contains hardcoded K3s ports (31080, 31081, 30080, 30081) that no longer exist.
New homelab layout: frontend on `:80`, API on `:8080`, same host `192.168.1.74`.

## Files to change

Only two files need changes:

1. `frontend/index.html` — runtime API URL detection script
2. `frontend/src/utils/apiConfig.js` — analytics URL detection (minor cleanup)

Everything else (`auth.js`, `useDocument.js`, `vite.config.js`) is fine — they read from
`window.__API_URL__` or use `VITE_API_URL` env var. No changes needed there.

---

## Done When

- Opening `http://192.168.1.74` (port 80) → frontend uses `http://192.168.1.74:8080/api`
- Opening `http://wh-lab.ru` → frontend uses `https://api.wh-lab.ru/api`
- Opening `http://localhost:3000` (local dev) → frontend uses `/api` (proxied by Vite)
- No ports 30080, 30081, 31080, 31081 remain anywhere in the codebase

---

## Step 1 — Replace script in frontend/index.html

Replace the entire `<script>` block in `<head>` with this:

```html
<script>
  (function() {
    var host = window.location.hostname;
    var apiUrl;
    var analyticsUrl;

    if (host === 'wh-lab.ru' || host === 'www.wh-lab.ru') {
      // Yandex Cloud production
      apiUrl = 'https://api.wh-lab.ru/api';
      analyticsUrl = 'https://api.wh-lab.ru/analytics';
    } else if (host === '192.168.1.74') {
      // Homelab — API on port 8080, frontend on port 80
      apiUrl = 'http://192.168.1.74:8080/api';
      analyticsUrl = 'http://192.168.1.74:8090';
    } else {
      // Local dev (localhost) or any other host — use relative path
      // Vite proxy handles /api → localhost:8080
      apiUrl = '/api';
      analyticsUrl = 'http://' + host + ':8090';
    }

    window.__API_URL__ = apiUrl;
    window.__ANALYTICS_URL__ = analyticsUrl;
  })();
</script>
```

Removed cases: `warehouse.local` (K3s cluster DNS), port-based branching (31081→31080, 30081→30080).

---

## Step 2 — Update frontend/src/utils/apiConfig.js

Replace `getAnalyticsUrl` if it exists, or add it. The file should read
`window.__ANALYTICS_URL__` the same way it reads `window.__API_URL__`.

Add this export to `apiConfig.js`:

```js
/**
 * Analytics service URL
 * @returns {string}
 */
export function getAnalyticsUrl() {
  if (import.meta.env.VITE_ANALYTICS_URL) {
    return import.meta.env.VITE_ANALYTICS_URL
  }
  // eslint-disable-next-line no-eval
  return eval('window.__ANALYTICS_URL__') || 'http://localhost:8090'
}
```

---

## Step 3 — Search and verify no other hardcoded K3s ports remain

Run a search across the entire frontend/src for any remaining references to old ports:

- `31080`, `31081`, `30080`, `30081`
- `warehouse.local`
- `cluster.local`

If found in any `.vue`, `.js`, or `.ts` file — replace with the correct runtime-resolved URL
using `getApiUrl()` from `utils/apiConfig.js`.

Do NOT search in `node_modules/`, `dist/`, or test snapshots.

---

## Step 4 — Verify vite.config.js proxy

`vite.config.js` already has the correct local dev proxy:

```js
proxy: {
  '/api': {
    target: 'http://localhost:8080',
    changeOrigin: true
  }
}
```

No changes needed. Just confirm it's there.

---

## Constraints

- Do NOT touch `auth.js` — it reads `window.__API_URL__` correctly
- Do NOT touch `useDocument.js` — it uses `getApiUrl()` correctly
- Do NOT add `VITE_API_URL` to any committed file — it's for local overrides only
- Do NOT hardcode any IP or port in `.vue` or `.js` files — all URLs must go through `getApiUrl()`

---

## Verification

After changes, open browser dev tools on `http://192.168.1.74` and check:

```js
window.__API_URL__      // → "http://192.168.1.74:8080/api"
window.__ANALYTICS_URL__ // → "http://192.168.1.74:8090"
```
