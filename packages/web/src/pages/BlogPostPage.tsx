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
