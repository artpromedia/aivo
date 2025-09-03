# S1-15 Admin Web App

A React 18 + TypeScript admin dashboard for the Educational Platform.

## Features

- Interactive dashboard with 8 functional cards
- User management with role assignment
- API integration via Kong Gateway
- Real-time data visualization with Recharts
- E2E testing with Playwright
- CTA guard validation (no static buttons/links)
- Responsive design with soft lavender gradients

## Tech Stack

- React 18 + TypeScript
- Vite 7 (build system)
- Tailwind CSS + shadcn/ui
- React Router 7 (navigation)
- TanStack Query (state management)
- Recharts (data visualization)
- Playwright (E2E testing)

## Development

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Run tests
pnpm test

# Run E2E tests
pnpm e2e

# Validate CTAs
pnpm cta-guard

# Build for production
pnpm build
```

## Dashboard Cards

All cards call real API endpoints or open modals:

1. **Usage Summary** - API metrics from Kong Gateway
2. **Subscription** - Opens billing management modal
3. **User Management** - Navigates to users page
4. **License Management** - Opens license modal
5. **Revenue Analytics** - API data visualization
6. **Team Management** - Opens team modal
7. **Namespace Management** - Opens namespace modal
8. **Support & Help** - Opens support modal

## Architecture

- `src/pages/` - Dashboard and user management pages
- `src/components/` - Reusable UI components
- `src/services/` - API service layer
- `src/hooks/` - React Query hooks
- `e2e/` - Playwright test suites
- `scripts/` - CTA validation scripts
