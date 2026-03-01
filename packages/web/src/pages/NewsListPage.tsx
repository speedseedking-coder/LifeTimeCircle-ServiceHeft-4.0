/* DEV-SCAFFOLD: Developer/debug-only page.\n   News list is currently a technical scaffold. Marked dev-only until editorial migration. */

import ItemsList from "../components/debug/ItemsList";

export default function NewsListPage(): JSX.Element {
  return <ItemsList title="News (Public)" path="/news" kind="news" />;
}
