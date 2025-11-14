# TradeDesk Frontend

SEBI-compliant algorithmic trading platform frontend built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- 🔐 JWT-based authentication with refresh tokens
- 📊 Real-time trading dashboard
- 🛡️ Risk management interface
- 📝 Audit log viewer
- 🎨 Modern UI with shadcn/ui components
- 📱 Fully responsive design
- ⚡ Optimized performance with React Query
- 🔄 Auto-refreshing data
- 🎯 Type-safe API client

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: React Query (TanStack Query)
- **HTTP Client**: Axios
- **Notifications**: Sonner
- **Forms**: React Hook Form
- **Charts**: Recharts

## Project Structure

```
frontend/
├── app/                      # Next.js app router pages
│   ├── (auth)/              # Authentication pages
│   ├── dashboard/           # Protected dashboard pages
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Home/Login page
├── components/              # React components
│   ├── features/           # Feature-specific components
│   │   ├── auth/          # Authentication components
│   │   ├── dashboard/     # Dashboard components
│   │   ├── risk/          # Risk management components
│   │   └── audit/         # Audit log components
│   ├── layouts/           # Layout components
│   ├── shared/            # Shared/common components
│   └── ui/                # shadcn/ui components
├── lib/                    # Utilities and hooks
│   ├── api.ts             # API client
│   ├── hooks/             # Custom React hooks
│   ├── types/             # TypeScript types
│   └── utils.ts           # Utility functions
└── public/                # Static assets
```

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your values
```

### Development

```bash
# Run development server
npm run dev

# The app will be available at http://localhost:3000
```

### Building for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint errors
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting
- `npm run type-check` - Run TypeScript type checking

## Component Library

### Authentication
- `LoginForm` - Username/password login form
- `AuthGuard` - Route protection wrapper

### Dashboard
- `MetricsCard` - KPI display card
- `TradingStatusCard` - Trading enabled/disabled status
- `PnLCard` - Profit & Loss display

### Shared
- `ErrorBoundary` - Error handling wrapper
- `LoadingSpinner` - Loading state indicator
- `DataTable` - Generic data table component

### Layouts
- `DashboardLayout` - Main app layout with sidebar

## State Management

The app uses React Query for server state management:

- Automatic caching and background refetching
- Optimistic updates
- Request deduplication
- Stale-while-revalidate pattern

## Authentication Flow

1. User enters credentials on login page
2. JWT tokens stored in localStorage
3. Access token included in API requests
4. Refresh token used to renew access token
5. Auto-logout on token expiration

## API Integration

All API calls go through the centralized client in `lib/api.ts`:

```typescript
import { api, riskApi, auditApi } from '@/lib/api';

// Example usage
const { data } = await riskApi.getConfig();
```

## Styling

- Tailwind CSS for utility-first styling
- shadcn/ui for pre-built components
- CSS modules for component-specific styles
- Dark mode support via next-themes

## Performance Optimizations

- Code splitting with dynamic imports
- Image optimization with next/image
- Font optimization with next/font
- API request caching
- Memoization of expensive computations

## Testing

```bash
# Run unit tests (coming soon)
npm test

# Run e2e tests (coming soon)
npm run test:e2e
```

## Deployment

The frontend can be deployed to any Node.js hosting platform:

- Vercel (recommended)
- Netlify
- AWS Amplify
- Self-hosted with PM2

## Environment Variables

```env
# API URL (optional, defaults to /api/v1)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run linting and formatting
4. Create a pull request

## License

Proprietary - All rights reserved
