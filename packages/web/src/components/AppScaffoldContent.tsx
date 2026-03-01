import { type AppGateState, type Role } from "../lib/appGate";
import { type Route } from "../lib/appRouting";
import AuthPage from "../pages/AuthPage";
import BlogListPage from "../pages/BlogListPage";
import BlogPostPage from "../pages/BlogPostPage";
import ConsentPage from "../pages/ConsentPage";
import DebugPublicSitePage from "../pages/DebugPublicSitePage";
import DocumentsPage from "../pages/DocumentsPage";
import NewsListPage from "../pages/NewsListPage";
import NewsPostPage from "../pages/NewsPostPage";
import OnboardingWizardPage from "../pages/OnboardingWizardPage";
import { PublicQrPage } from "../pages/PublicQrPage";
import TrustFolderDetailPage from "../pages/TrustFolderDetailPage";
import TrustFoldersPage from "../pages/TrustFoldersPage";
import VehicleDetailPage from "../pages/VehicleDetailPage";
import VehiclesPage from "../pages/VehiclesPage";
import AdminPage from "../pages/AdminPage";

export default function AppScaffoldContent(props: {
  route: Route;
  actorRole: Role | null;
  gateState: AppGateState;
}): JSX.Element | null {
  switch (props.route.kind) {
    case "debugPublicSite":
      return <DebugPublicSitePage />;
    case "blogList":
      return <BlogListPage />;
    case "newsList":
      return <NewsListPage />;
    case "blogPost":
      return <BlogPostPage slug={props.route.slug} />;
    case "newsPost":
      return <NewsPostPage slug={props.route.slug} />;
    case "publicQr":
      return (
        <div style={{ marginTop: 12 }}>
          <PublicQrPage vehicleId={decodeURIComponent(props.route.vehicleId)} />
        </div>
      );
    case "auth":
      return <AuthPage />;
    case "consent":
      return props.gateState !== "forbidden" ? <ConsentPage /> : null;
    case "vehicles":
      return props.gateState === "ready" ? <VehiclesPage /> : null;
    case "vehicleDetail":
      return props.gateState === "ready" ? <VehicleDetailPage vehicleId={decodeURIComponent(props.route.vehicleId)} /> : null;
    case "documents":
      return props.gateState === "ready" ? <DocumentsPage /> : null;
    case "onboarding":
      return props.gateState === "ready" ? <OnboardingWizardPage /> : null;
    case "admin":
      return props.gateState === "ready" && props.actorRole && (props.actorRole === "admin" || props.actorRole === "superadmin") ? (
        <AdminPage actorRole={props.actorRole} />
      ) : null;
    case "trustFolders":
      return props.gateState === "ready" ? <TrustFoldersPage /> : null;
    case "trustFolderDetail":
      return props.gateState === "ready" ? <TrustFolderDetailPage folderId={decodeURIComponent(props.route.folderId)} /> : null;
    default:
      return null;
  }
}
