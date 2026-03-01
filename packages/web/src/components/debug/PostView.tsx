/* DEV-SCAFFOLD: Debug post view — developer-only helper for blog/news posts. */

import ApiBox from "./ApiBox";

export default function PostView(props: { title: string; path: string; backHref: string; backLabel: string }): JSX.Element {
  return (
    <>
      <div style={{ marginBottom: 12 }}>
        <a className="ltc-link" href={props.backHref}>
          ← {props.backLabel}
        </a>
      </div>
      <ApiBox path={props.path} title={props.title} />
    </>
  );
}
