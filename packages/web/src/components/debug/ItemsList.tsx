import { useEffect, useState } from "react";
import { apiGet, asString, isRecord, prettyBody } from "../../api";
import DebugCard from "./DebugCard";

type Item = {
  slug: string;
  title: string;
};

export default function ItemsList(props: { title: string; path: string; kind: "blog" | "news" }): JSX.Element {
  const [state, setState] = useState<{
    loading: boolean;
    error?: string;
    status?: number;
    items?: Item[];
    raw?: string;
  }>({ loading: true });

  useEffect(() => {
    let alive = true;
    setState({ loading: true });

    apiGet(props.path).then((response) => {
      if (!alive) return;

      if (!response.ok) {
        setState({
          loading: false,
          status: response.status,
          error: `${response.error}${response.body ? `: ${String(response.body)}` : ""}`,
        });
        return;
      }

      const body = response.body;

      if (Array.isArray(body)) {
        const mapped = body
          .map((item) => {
            if (!isRecord(item)) return null;
            const slug = asString(item.slug) ?? asString(item.id) ?? null;
            const title = asString(item.title) ?? asString(item.name) ?? slug;
            if (!slug || !title) return null;
            return { slug, title };
          })
          .filter(Boolean) as Item[];

        if (mapped.length > 0) {
          setState({ loading: false, status: response.status, items: mapped });
          return;
        }
      }

      setState({ loading: false, status: response.status, raw: prettyBody(body) });
    });

    return () => {
      alive = false;
    };
  }, [props.path]);

  return (
    <DebugCard title={props.title}>
      <div className="ltc-meta">
        GET <code>{`/api${props.path.startsWith("/") ? props.path : `/${props.path}`}`}</code>
        {typeof state.status === "number" ? ` -> ${state.status}` : ""}
      </div>

      {state.loading ? (
        <div className="ltc-muted">Lädt…</div>
      ) : state.error ? (
        <pre className="ltc-pre">{state.error}</pre>
      ) : state.items ? (
        <ul className="ltc-list">
          {state.items.map((item) => (
            <li key={item.slug}>
              <a className="ltc-link" href={`#/${props.kind}/${encodeURIComponent(item.slug)}`}>
                {item.title}
              </a>{" "}
              <span className="ltc-muted">({item.slug})</span>
            </li>
          ))}
        </ul>
      ) : (
        <pre className="ltc-pre">{state.raw ?? ""}</pre>
      )}
    </DebugCard>
  );
}
