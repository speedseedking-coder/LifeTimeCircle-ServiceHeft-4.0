import { bgStyle, getBgForRoute, type Route } from "../lib/appRouting";
import ContactPage from "../pages/ContactPage";
import CookiesPage from "../pages/CookiesPage";
import DatenschutzPage from "../pages/DatenschutzPage";
import EntryPage from "../pages/EntryPage";
import FaqPage from "../pages/FaqPage";
import ImpressumPage from "../pages/ImpressumPage";
import JobsPage from "../pages/JobsPage";
import LandingPage from "../pages/LandingPage";

export default function PublicRouteRenderer(props: { route: Extract<Route, { kind: "home" | "entry" | "faq" | "cookies" | "jobs" | "contact" | "impressum" | "datenschutz" }> }): JSX.Element | null {
  if (props.route.kind === "home") {
    return <LandingPage />;
  }

  const appStyle = bgStyle(getBgForRoute(props.route));

  switch (props.route.kind) {
    case "entry":
      return <EntryPage appStyle={appStyle} />;
    case "faq":
      return <FaqPage appStyle={appStyle} />;
    case "cookies":
      return <CookiesPage appStyle={appStyle} />;
    case "jobs":
      return <JobsPage appStyle={appStyle} />;
    case "contact":
      return <ContactPage appStyle={appStyle} />;
    case "impressum":
      return <ImpressumPage appStyle={appStyle} />;
    case "datenschutz":
      return <DatenschutzPage appStyle={appStyle} />;
    default:
      return null;
  }
}
