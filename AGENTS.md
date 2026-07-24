# AGENTS.md

This file contains essential guidance for developers working in this repository. It answers: "Would an agent likely miss this without help?"

## Setup & Development

- Run `npm install` to install all dependencies.
- Use `npm run dev` to start the development server.
- The project uses TypeScript; compiled artifacts are in `.next/` (Next.js) or `dist/`.

## Architecture

- Entry point is `src/main.ts` (for CLI tools) or `pages/index.tsx` (for web apps).
- The app is organized into:
  - `src/components/`: Reusable React components
  - `src/lib/`: Core logic and utilities
  - `src/pages/`: Page routes (Next.js)
- All code is linted with ESLint; type checked with TypeScript.

## Commands

- Run tests with `npm test`.
- Lint with `npm run lint`.
- Format code with `npm run format`.
- Type-check with `npm run typecheck`.
- Build the project with `npm run build`.
- Run a specific test file (e.g., `src/components/Button.test.tsx`) using `npm test src/components/Button.test.tsx`.

## Testing

- Unit and integration tests reside in `__tests__/` or alongside source files as `.test.tsx`.
- Snapshot testing is used where relevant.
- Tests requiring network services must be mocked appropriately.
- The CI workflow runs lint, typecheck, test, and build in strict order.

## Special Notes

- Generated code (e.g., `.generated.ts`) must not be modified directly; they are overwritten on regeneration.
- Migrations are placed in `migrations/` and must be run manually via `npm run migrate`.
- Environment variables are loaded using dotenv; see `.env.example` for reference.
