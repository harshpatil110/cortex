# Cortex Browser Extension (scaffold)

This workspace is a placeholder for the Chrome Extension (MV3).

`manifest.json` currently references entry files (`index.html`, `src/background.js`)
that do not exist yet, so the `dev` / `build` / `lint` scripts are intentionally
absent — with no entry files, `vite` / `eslint` would fail and break every
monorepo-wide command (`pnpm dev`, `pnpm build`, `pnpm lint` run through Turborepo).

When the extension is implemented, add back:
- `src/` entry files and a `vite.config.js`
- `"dev": "vite"`, `"build": "vite build"`, and a `lint` script

Only a `test` script exists for now so `turbo run test` has a task to execute.
