/* DEV-SCAFFOLD: Developer/debug-only page.\n   Blog post view is a technical scaffold; convert to editorial flow before promoting. */

import PostView from "../components/debug/PostView";

export default function BlogPostPage(props: { slug: string }): JSX.Element {
  return (
    <PostView
      title={`Blog Post: ${props.slug}`}
      path={`/blog/${encodeURIComponent(props.slug)}`}
      backHref="#/blog"
      backLabel="zur Blog-Liste"
    />
  );
}
