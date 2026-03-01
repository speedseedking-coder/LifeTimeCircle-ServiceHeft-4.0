/* DEV-SCAFFOLD: Developer/debug-only page.\n   This page is intended for local development and diagnostics.\n   Keep as dev-only or follow project policy before promoting to production. */

import ApiBox from "../components/debug/ApiBox";

export default function DebugPublicSitePage(): JSX.Element {
  return <ApiBox path="/public/site" title="API: /public/site" />;
}
