import { isConsentRequired } from "../lib.auth";
import { handleUnauthorized } from "./handleUnauthorized";

type SetViewState = (next: any) => void;
type SetError = (msg: string) => void;

function extractCode(body: unknown): string | null {
  if (typeof body === "string") {
    try {
      const parsed = JSON.parse(body) as any;
      const d = parsed?.detail;
      if (typeof d === "string") return d;
      if (typeof d?.code === "string") return d.code;
    } catch {
      return body;
    }
    return body;
  }
  const anyBody = body as any;
  const d = anyBody?.detail;
  if (typeof d === "string") return d;
  if (typeof d?.code === "string") return d.code;
  return null;
}

export function handleApiNotOk(
  res: { status: number; body?: unknown },
  opts: { setViewState: SetViewState; setError: SetError; fallbackError: string },
): void {
  if (res.status === 401) {
    handleUnauthorized();
    return;
  }

  const code = (extractCode(res.body) ?? "").toLowerCase();
  const consent = res.status === 403 && (code === "consent_required" || isConsentRequired(res.body));
  if (consent) {
    if (!window.location.hash.startsWith("#/consent")) window.location.hash = "#/consent";
    return;
  }

  const addon =
    res.status === 403 &&
    (code.includes("addon") || code.includes("paywall") || code.includes("entitlement"));
  if (addon) {
    opts.setViewState("addon");
    return;
  }

  if (res.status === 403) {
    opts.setViewState("forbidden");
    return;
  }

  opts.setViewState("error");
  opts.setError(opts.fallbackError);
}