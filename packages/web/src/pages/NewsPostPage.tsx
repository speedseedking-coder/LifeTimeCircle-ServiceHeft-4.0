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
