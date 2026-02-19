import { handleUnauthorized } from "./handleUnauthorized";

export async function httpFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const res = await fetch(input, init);

  if (res.status === 401) {
    handleUnauthorized();
  }

  return res;
}
