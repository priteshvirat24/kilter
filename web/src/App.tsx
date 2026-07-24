/**
 * App.tsx — Router and query provider setup.
 * No layout shell — each route is full-bleed.
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { DriftFeed } from './routes/DriftFeed'
import { ServerDetail } from './routes/ServerDetail'
import { EvidenceView } from './routes/EvidenceView'
import { RemediationView } from './routes/RemediationView'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 25000,         // 25s — just under the 30s poll interval
      gcTime: 5 * 60 * 1000,   // 5 min cache
      retry: 1,
    },
  },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="app-root">
          <Routes>
            <Route path="/" element={<DriftFeed />} />
            <Route path="/servers/:id" element={<ServerDetail />} />
            <Route path="/drift/:id" element={<EvidenceView />} />
            <Route path="/drift/:id/fix" element={<RemediationView />} />
          </Routes>
        </div>
        <div className="mobile-notice">
          Kilter is a desktop-first tool. Please open on a larger screen.
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
