/* DEV-SCAFFOLD: Developer/debug-only page.\n   Blog list is currently a technical scaffold. Marked dev-only until editorial migration. */

import ItemsList from "../components/debug/ItemsList";

export default function BlogListPage(): JSX.Element {
  return <ItemsList title="Blog (Public)" path="/blog" kind="blog" />;
}
