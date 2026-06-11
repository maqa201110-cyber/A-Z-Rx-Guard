# AZRxGUARD Bot

A Telegram bot providing group management, utility tools (IP lookup, weather, currency exchange, font conversion, AI features via Gemini), and more. Includes a Flask keep-alive web server and a TypeScript monorepo for the API and UI sandbox.

## Run & Operate

- **Bot**: `.pythonlibs/bin/python3 bot.py` — runs the Telegram bot (requires `TELEGRAM_BOT_TOKEN` secret)
- **Web (keep-alive)**: `.pythonlibs/bin/gunicorn --bind 0.0.0.0:5000 main:app` — Flask web server on port 5000
- **API Server**: `pnpm --filter @workspace/api-server run dev` — Express API (port 8080)
- **Mockup Sandbox**: `pnpm --filter @workspace/mockup-sandbox run dev` — Vite/React component preview
- **DB schema push**: `pnpm --filter @workspace/db run push`
- **API codegen**: `pnpm --filter @workspace/api-spec run codegen`

## Required Secrets

- `TELEGRAM_BOT_TOKEN` — from @BotFather on Telegram (required)
- `BOT_OWNER_ID` — your Telegram user ID for owner-level commands (optional, defaults to 0)

## Stack

- **Bot**: Python 3.11, python-telegram-bot v22, google-genai (Gemini AI), requests, flask, psycopg2
- **Monorepo**: pnpm workspaces, Node.js 20, TypeScript 5.9
- **API**: Express 5, Drizzle ORM, PostgreSQL, Zod validation
- **UI sandbox**: Vite + React 19 + Tailwind CSS

## Where things live

- `bot.py` — all Telegram bot logic (~9000 lines)
- `main.py` — minimal Flask keep-alive server
- `artifacts/api-server/` — Express API server
- `artifacts/mockup-sandbox/` — React component preview environment
- `lib/db/` — Drizzle ORM schema and config
- `lib/api-spec/` — OpenAPI spec (source of truth for API types)
- `lib/api-zod/` — Zod schemas generated from the API spec

## Architecture decisions

- Bot uses polling mode (not webhooks) — simpler for Replit hosted environment
- Flask keep-alive on port 5000 serves as the webview so Replit shows a preview
- Python packages installed in `.pythonlibs/` virtualenv — workflows use `.pythonlibs/bin/` prefix

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- Always use `.pythonlibs/bin/python3` and `.pythonlibs/bin/gunicorn` in workflow commands (not system `python3`)
- Run `pnpm install` from the workspace root before starting Node.js workflows after a fresh clone
