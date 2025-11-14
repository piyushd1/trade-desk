# Frontend Refactoring Plan

## Overview
This document outlines the refactoring strategy for the TradeDesk frontend application.

## Current State Analysis

### Directory Structure
```
frontend/
├── app/                    # Next.js 14 App Router pages
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # Main app pages
│   ├── layout.tsx         # Root layout
│   ├── page.tsx          # Login page
│   └── providers.tsx     # App-wide providers
├── components/
│   └── ui/               # shadcn/ui components
├── lib/
│   ├── api.ts           # API client
│   ├── hooks/           # Custom hooks
│   └── utils.ts         # Utilities
└── public/              # Static assets
```

### Issues Identified
1. No custom components - everything uses ui/ directly
2. API calls mixed in components (page.tsx uses axios directly)
3. No consistent error handling
4. No loading states management
5. No type definitions for API responses in components
6. No component documentation
7. No tests
8. No consistent styling approach

## Refactoring Goals

### 1. Component Architecture
- Create feature-based component structure
- Separate presentational and container components
- Add proper TypeScript types
- Add JSDoc documentation

### 2. State Management
- Centralize authentication state
- Add proper error boundaries
- Implement consistent loading states
- Add optimistic updates where appropriate

### 3. Code Quality
- Add ESLint rules for consistency
- Add Prettier configuration
- Implement proper error handling
- Add loading skeletons
- Remove unused UI components

### 4. Performance
- Implement code splitting
- Add proper memoization
- Optimize bundle size
- Add proper caching strategies

### 5. Developer Experience
- Add component documentation
- Create component library/storybook
- Add development utilities
- Improve TypeScript usage

## Implementation Steps

### Phase 1: Structure & Standards
1. Create component structure
2. Add linting and formatting
3. Create shared types
4. Add error boundaries

### Phase 2: Component Refactoring
1. Extract reusable components
2. Create feature components
3. Add loading states
4. Implement error handling

### Phase 3: State & Data
1. Centralize auth logic
2. Create data hooks
3. Add caching strategies
4. Implement optimistic updates

### Phase 4: Polish & Documentation
1. Add component docs
2. Create usage examples
3. Add performance monitoring
4. Clean up unused code

## Component Structure (Proposed)

```
components/
├── features/           # Feature-specific components
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── AuthGuard.tsx
│   ├── dashboard/
│   │   ├── MetricsCard.tsx
│   │   ├── TradingStatus.tsx
│   │   └── RiskLimits.tsx
│   ├── risk/
│   │   ├── KillSwitch.tsx
│   │   ├── RiskConfig.tsx
│   │   └── BreachList.tsx
│   └── audit/
│       ├── AuditTable.tsx
│       └── EventDetails.tsx
├── layouts/           # Layout components
│   ├── DashboardLayout.tsx
│   └── AuthLayout.tsx
├── shared/           # Shared components
│   ├── ErrorBoundary.tsx
│   ├── LoadingSpinner.tsx
│   └── DataTable.tsx
└── ui/              # Keep shadcn/ui components
```

## Next Steps
1. Start with Phase 1 implementation
2. Create ESLint and Prettier configs
3. Extract first set of components
4. Add proper TypeScript types
