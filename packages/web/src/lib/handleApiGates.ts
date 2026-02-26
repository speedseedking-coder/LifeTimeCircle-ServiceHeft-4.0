import { isConsentRequired } from "../lib.auth";
import { normalizeApiError, ApiResult } from "../api";
import { handleUnauthorized } from "./handleUnauthorized";

type SetViewState = (next: any) => void;
type SetError = (msg: string) => void;

export function handleApiNotOk(
  res: Pick<ApiResult, "ok" | "status" | "body">,
  opts: { setViewState: SetViewState; setError: SetError; fallbackError: string },
): void {
  const apiErr = normalizeApiError(res);

  if (apiErr.status === 401) {
    handleUnauthorized();
    return;
  }

  if (apiErr.status === 403 && (apiErr.consent_required || isConsentRequired(res.body))) {
    if (!window.location.hash.startsWith("#/consent")) window.location.hash = "#/consent";
    return;
  }

  if (apiErr.status === 403 && apiErr.addon_required) {
    opts.setViewState("addon");
    return;
  }

  if (apiErr.status === 403) {
    opts.setViewState("forbidden");
    return;
  }

  opts.setViewState("error");
  opts.setError(opts.fallbackError);
}