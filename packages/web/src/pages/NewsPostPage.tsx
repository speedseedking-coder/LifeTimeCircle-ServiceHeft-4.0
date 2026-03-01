/* DEV-SCAFFOLD: Developer/debug-only page.\n   News post view is a technical scaffold; convert to editorial flow before promoting. */

import PostView from "../components/debug/PostView";

export default function NewsPostPage(props: { slug: string }): JSX.Element {
  return (
    <PostView
      title={`News Post: ${props.slug}`}
      path={`/news/${encodeURIComponent(props.slug)}`}
      backHref="#/news"
      backLabel="zur News-Liste"
    />
  );
}
