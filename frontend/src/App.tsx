import { Suspense, lazy } from "react";
import { Link, Route, Routes } from "react-router-dom";

import ProtectedRoute from "@/components/ProtectedRoute";
import { Spinner } from "@/components/ui/feedback";
import AppLayout from "@/layouts/AppLayout";

const LandingPage = lazy(() => import("@/pages/LandingPage"));
const LoginPage = lazy(() => import("@/pages/LoginPage"));
const SignupPage = lazy(() => import("@/pages/SignupPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const RepositoriesPage = lazy(() => import("@/pages/RepositoriesPage"));
const RepositoryDetailPage = lazy(() => import("@/pages/RepositoryDetailPage"));
const ScanHistoryPage = lazy(() => import("@/pages/ScanHistoryPage"));
const ScanResultsPage = lazy(() => import("@/pages/ScanResultsPage"));
const FindingsPage = lazy(() => import("@/pages/FindingsPage"));
const FindingDetailPage = lazy(() => import("@/pages/FindingDetailPage"));
const FixSuggestionsPage = lazy(() => import("@/pages/FixSuggestionsPage"));
const PatchReviewPage = lazy(() => import("@/pages/PatchReviewPage"));
const AnalyticsPage = lazy(() => import("@/pages/AnalyticsPage"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));
const ProfilePage = lazy(() => import("@/pages/ProfilePage"));

function RouteFallback() {
  return (
    <div className="flex h-64 items-center justify-center text-muted">
      <Spinner className="h-5 w-5" />
    </div>
  );
}

function NotFound() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-3 text-center">
      <p className="text-3xl font-semibold">404</p>
      <p className="text-[13px] text-muted">This page does not exist.</p>
      <Link to="/dashboard" className="text-[13px] text-accent hover:underline">
        Back to dashboard
      </Link>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/repositories" element={<RepositoriesPage />} />
            <Route path="/repositories/:id" element={<RepositoryDetailPage />} />
            <Route path="/scans" element={<ScanHistoryPage />} />
            <Route path="/scans/:id" element={<ScanResultsPage />} />
            <Route path="/findings" element={<FindingsPage />} />
            <Route path="/findings/:id" element={<FindingDetailPage />} />
            <Route path="/findings/:id/fixes" element={<FixSuggestionsPage />} />
            <Route path="/fixes/:id" element={<PatchReviewPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
