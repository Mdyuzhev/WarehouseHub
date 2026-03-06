# TASK: UI Cleanup — Remove demo accounts, replace emoji with SVG icons

## Goal

1. Remove the demo accounts block from the login page entirely
2. Replace all emoji icons across the frontend with inline SVG icons

The result should look professional — no emoji anywhere in the UI.

---

## Done When

- Login page has no demo accounts section (no buttons, no `fillDemo` method, no `🔑` title)
- No emoji characters remain in any `.vue` file in `frontend/src/`
- All icons are inline SVG with consistent size and `currentColor` stroke/fill
- App still works — login, navigation, facility selector all functional

---

## Step 1 — Remove demo accounts from LoginPage.vue

In `frontend/src/components/LoginPage.vue`:

**Delete** the entire `demo-accounts` block from template:
```html
<!-- Delete from here -->
<div class="demo-accounts">
  ...
</div>
<!-- to here -->
```

**Delete** the `fillDemo` method from `methods: {}`.

**Delete** the `.demo-accounts`, `.demo-title`, `.demo-list`, `.demo-btn`, `.role` CSS classes.

The login page should only have: logo, title, username input, password input, error message, login button, footer.

---

## Step 2 — Create a shared SVG icon component

Create `frontend/src/components/AppIcon.vue`:

```vue
<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    :stroke="filled ? 'none' : 'currentColor'"
    :fill="filled ? 'currentColor' : 'none'"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="app-icon"
    aria-hidden="true"
  >
    <component :is="'path'" v-for="(d, i) in paths" :key="i" :d="d" />
  </svg>
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 20 },
  filled: { type: Boolean, default: false }
})
</script>
```

Actually, inline SVG per-usage is simpler and more reliable than a dynamic component.
**Use inline SVG directly in each file instead.** No separate component needed.

---

## Step 3 — SVG icon library

Use these SVG paths (all from Heroicons outline style, 24×24 viewBox):

```
user (👤):
  <path d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"/>

lock (🔒):
  <path d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z"/>

eye (👁️):
  <path d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z"/>
  <path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>

eye-off (🙈):
  <path d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88"/>

warning / alert (⚠️):
  <path d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"/>

factory / DC (🏭):
  <path d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z"/>

box / WH (📦):
  <path d="m20.25 7.5-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z"/>

store / PP (🏪):
  <path d="M13.5 21v-7.5a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 .75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349M3.75 21V9.349m0 0a3.001 3.001 0 0 0 3.75-.615A2.993 2.993 0 0 0 9.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 0 0 2.25 1.016 2.993 2.993 0 0 0 2.25-1.016 3.001 3.001 0 0 0 3.75.614m-16.5 0a3.004 3.004 0 0 1-.621-4.72l1.189-1.19A1.5 1.5 0 0 1 5.378 3h13.243a1.5 1.5 0 0 1 1.06.44l1.19 1.189a3 3 0 0 1-.621 4.72M6.75 18h3.75a.75.75 0 0 0 .75-.75V13.5a.75.75 0 0 0-.75-.75H6.75a.75.75 0 0 0-.75.75v3.75c0 .414.336.75.75.75Z"/>

inbox / receipt-in (📥):
  <path d="M9 3.75H6.912a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H15M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859M12 3v8.25m0 0-3-3m3 3 3-3"/>

arrow-up-tray / shipment-out (📤):
  <path d="M9 3.75H6.912a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H15M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859M12 3v8.25m0 0 3-3m-3 3-3-3"/>

plus / add (➕):
  <path d="M12 4.5v15m7.5-7.5h-15"/>

clipboard-list / inventory (📋):
  <path d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z"/>

shopping-cart / issue (🛒):
  <path d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z"/>

pencil / edit (✏️):
  <path d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125"/>

trash / delete (🗑️):
  <path d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"/>

map-pin / location (📍):
  <path d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>
  <path d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z"/>

chevron-down / dropdown arrow (▼):
  <path d="m19.5 8.25-7.5 7.5-7.5-7.5"/>
```

---

## Step 4 — Replace emoji in each file

### LoginPage.vue

| Emoji | Replace with |
|-------|-------------|
| `🏭` in `.logo` | SVG factory icon, size 64px |
| `👤` in username label | SVG user icon, size 16px |
| `🔒` in password label | SVG lock icon, size 16px |
| `👁️` / `🙈` toggle button | SVG eye / eye-off icon, size 20px |
| `⚠️` in error message | SVG warning icon, size 16px |

### FacilitySelector.vue

| Emoji | Replace with |
|-------|-------------|
| `🏭` DC | SVG factory icon, size 18px |
| `📦` WH | SVG box icon, size 18px |
| `🏪` PP | SVG store icon, size 18px |
| `📍` fallback | SVG map-pin icon, size 18px |
| `▼` dropdown arrow | SVG chevron-down icon, size 14px |

### DCDashboard.vue, WHDashboard.vue, PPDashboard.vue

| Emoji | Replace with |
|-------|-------------|
| `📥` | SVG inbox icon, size 32px |
| `📤` | SVG arrow-up-tray icon, size 32px |
| `📦` | SVG box icon, size 32px |
| `📋` | SVG clipboard-list icon, size 32px |
| `🛒` | SVG shopping-cart icon, size 32px |
| `➕` | SVG plus icon, size 32px |

### HomePage.vue

| Emoji | Replace with |
|-------|-------------|
| `✏️` edit button | SVG pencil icon, size 16px |
| `🗑️` delete button | SVG trash icon, size 16px |

---

## Step 5 — SVG styling rules

All inline SVGs must follow this pattern:

```html
<!-- In labels/small contexts (16px): -->
<svg width="16" height="16" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.5"
     stroke-linecap="round" stroke-linejoin="round"
     style="flex-shrink: 0; vertical-align: middle;">
  <path d="..."/>
</svg>

<!-- In nav cards (32px): -->
<svg width="32" height="32" viewBox="0 0 24 24" fill="none"
     stroke="currentColor" stroke-width="1.5"
     stroke-linecap="round" stroke-linejoin="round">
  <path d="..."/>
</svg>
```

Key rules:
- Always `fill="none"` + `stroke="currentColor"` — icons inherit text color
- Always `stroke-width="1.5"` — consistent weight
- `flex-shrink: 0` on small icons so they don't compress in flex containers
- No hardcoded colors — SVGs adapt to dark/light context automatically

---

## Constraints

- Do NOT change any functionality — only visual changes
- Do NOT change `data-testid` attributes — UI tests depend on them
- Do NOT use any icon library (no heroicons package, no fontawesome) — inline SVG only
- Do NOT change the login form layout or styles — only remove demo-accounts block and swap emoji
- After changes, run `npm run lint` in `frontend/` to verify no syntax errors

---

## Verification

1. Open login page — no demo accounts visible, logo is SVG factory icon
2. Open facility selector — dropdown shows SVG icons for DC/WH/PP
3. Open any dashboard — nav cards show SVG icons
4. Open products page — edit/delete buttons show SVG icons
5. Check browser console — no errors about missing components or broken templates
