import { useEffect, useState } from "react";
import { apiGet, prettyBody } from "../../api";
import DebugCard from "./DebugCard";

export default function ApiBox(props: { path: string; title: string }): JSX.Element {
  const [state, setState] = useState<{ loading: boolean; text: string; status?: number }>({ loading: true, text: "" });

  useEffect(() => {
    let alive = true;
    setState({ loading: true, text: "" });

    apiGet(props.path).then((response) => {
      if (!alive) return;

      if (!response.ok) {
        setState({
          loading: false,
          text: `${response.error}\n${typeof response.body === "string" ? response.body : ""}`.trim(),
          status: response.status,
        });
        return;
      }

      setState({ loading: false, text: prettyBody(response.body), status: response.status });
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

      {state.loading ? <div className="ltc-muted">Lädt…</div> : <pre className="ltc-pre">{state.text}</pre>}
    </DebugCard>
  );
}
