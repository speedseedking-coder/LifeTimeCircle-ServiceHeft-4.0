import { FormEvent, useEffect, useMemo, useState } from "react";
import InlineErrorBanner from "../components/InlineErrorBanner";
import {
  buildConsentAcceptances,
  fetchRequiredConsents,
  normalizeRequiredConsents,
  logoutSession,
  readAuthChallenge,
  readVerifiedSession,
  requestAuthChallenge,
  verifyAuthChallenge,
  type RequiredConsent,
} from "../authConsentApi";
import { extractApiError } from "../api";
import { authHeaders, clearAuthToken, getAuthToken, setAuthToken } from "../lib.auth";

function safeNextHash(raw: string | null): string {
  if (!raw || !raw.startsWith("#/") || raw.startsWith("#//")) return "#/vehicles";
  return raw;
}

function nextHashFromLocation(): string {
  const raw = window.location.hash || "#/auth";
  const query = raw.split("?")[1] ?? "";
  const params = new URLSearchParams(query);
  return safeNextHash(params.get("next"));
}

function toAuthErrorMessage(status: number, body: unknown): string {
  const code = (extractApiError(body) ?? "").toUpperCase();

  if (status === 429 && code === "RATE_LIMIT") return "Zu viele Anfragen. Bitte kurz warten und erneut versuchen.";
  if (status === 429 && code === "LOCKED") return "Zu viele falsche Codes. Bitte neuen Code anfordern.";
  if (status === 400 && code === "EXPIRED") return "Der Code ist abgelaufen. Bitte neuen Code anfordern.";
  if (status === 400 && code === "INVALID") return "Code oder Challenge sind ungültig.";
  if (status === 403 && code === "CONSENT_REQUIRED") {
    return "Die angeforderten Consent-Versionen passen nicht zum aktuellen Server-Stand. Seite neu laden und erneut versuchen.";
  }
  if (status === 0) return "Netzwerkfehler. Bitte Verbindung und Backend prüfen.";
  return "Authentifizierung fehlgeschlagen.";
}

export default function AuthPage(): JSX.Element {
  const [requiredConsents, setRequiredConsents] = useState<RequiredConsent[]>([]);
  const [consentLoadError, setConsentLoadError] = useState("");
  const [consentLoading, setConsentLoading] = useState(true);

  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [challengeId, setChallengeId] = useState("");
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [requestMessage, setRequestMessage] = useState("");
  const [busy, setBusy] = useState<"request" | "verify" | "logout" | null>(null);
  const [error, setError] = useState("");
  const [tokenPresent, setTokenPresent] = useState(() => getAuthToken() !== null);

  const [termsChecked, setTermsChecked] = useState(false);
  const [privacyChecked, setPrivacyChecked] = useState(false);

  const nextHash = useMemo(() => nextHashFromLocation(), []);
  const consentSummary = useMemo(
    () => requiredConsents.map((item) => `${item.doc_type}:${item.doc_version}`).join(", "),
    [requiredConsents],
  );

  useEffect(() => {
    let alive = true;

    const run = async () => {
      setConsentLoading(true);
      setConsentLoadError("");
      const res = await fetchRequiredConsents();
      if (!alive) return;

      setConsentLoading(false);
      if (!res.ok) {
        setConsentLoadError("Consent-Versionen konnten nicht geladen werden.");
        return;
      }

      const required = normalizeRequiredConsents(res.body);
      if (required.length === 0) {
        setConsentLoadError("Consent-Versionen fehlen oder haben ein unerwartetes Format.");
        return;
      }

      setRequiredConsents(required);
    };

    void run();
    return () => {
      alive = false;
    };
  }, []);

  const allChecksPresent = termsChecked && privacyChecked;
  const canVerify = challengeId.trim().length > 0 && otp.trim().length > 0 && allChecksPresent && !consentLoading && !consentLoadError;

  async function onRequestChallenge(e: FormEvent) {
    e.preventDefault();
    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      setError("Bitte eine E-Mail-Adresse eingeben.");
      return;
    }

    setBusy("request");
    setError("");
    setRequestMessage("");
    setDevOtp(null);
    setChallengeId("");
    setOtp("");

    const res = await requestAuthChallenge(normalizedEmail);
    setBusy(null);

    if (!res.ok) {
      setError(toAuthErrorMessage(res.status, res.body));
      return;
    }

    const parsed = readAuthChallenge(res.body);
    if (!parsed.challengeId) {
      setError("Challenge-ID fehlt in der Antwort.");
      return;
    }

    setChallengeId(parsed.challengeId);
    setRequestMessage(parsed.message || "Code angefordert. Bitte OTP eingeben.");
    setDevOtp(parsed.devOtp);
  }

  async function onVerify(e: FormEvent) {
    e.preventDefault();

    if (!canVerify) {
      setError("Bitte Consent bestätigen und Challenge + OTP vollständig ausfüllen.");
      return;
    }

    setBusy("verify");
    setError("");

    const res = await verifyAuthChallenge({
      email: email.trim(),
      challengeId: challengeId.trim(),
      otp: otp.trim(),
      consents: buildConsentAcceptances(requiredConsents),
    });
    setBusy(null);

    if (!res.ok) {
      setError(toAuthErrorMessage(res.status, res.body));
      return;
    }

    const verified = readVerifiedSession(res.body);
    if (!verified.accessToken) {
      setError("Access-Token fehlt in der Verify-Antwort.");
      return;
    }

    setAuthToken(verified.accessToken);
    setTokenPresent(true);
    const next = encodeURIComponent(nextHash);
    window.location.hash = `#/consent?next=${next}`;
  }

  async function onLogout() {
    const token = getAuthToken();
    setBusy("logout");
    setError("");
    if (token) {
      await logoutSession(authHeaders(token));
    }
    clearAuthToken();
    setTokenPresent(false);
    setBusy(null);
    window.location.hash = "#/auth";
  }

  return (
    <main style={{ padding: 12 }}>
      <h1>Auth</h1>
      <p>OTP-Login über die echten Endpunkte `/auth/request` und `/auth/verify`. Danach geht der Flow in den Consent-Schritt.</p>

      <section className="ltc-card" style={{ marginTop: 16 }}>
        <h2>Aktueller Einstieg</h2>
        <p className="ltc-muted">
          Ziel nach erfolgreichem Login: <code>{nextHash}</code>
        </p>
        {tokenPresent ? (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
            <a href={`#/consent?next=${encodeURIComponent(nextHash)}`}>Weiter zu Consent</a>
            <button type="button" disabled={busy === "logout"} onClick={() => void onLogout()}>
              {busy === "logout" ? "Meldet ab..." : "Abmelden"}
            </button>
          </div>
        ) : null}
      </section>

      <section className="ltc-card" style={{ marginTop: 16 }}>
        <h2>Schritt 1: Code anfordern</h2>
        <form onSubmit={(e) => void onRequestChallenge(e)}>
          <label>
            E-Mail
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              autoComplete="email"
              placeholder="name@example.com"
              style={{ display: "block", marginTop: 8, padding: 10, width: "100%", maxWidth: 420 }}
            />
          </label>

          <button type="submit" disabled={busy === "request"} style={{ marginTop: 12 }}>
            {busy === "request" ? "Fordert an..." : "Code anfordern"}
          </button>
        </form>

        {requestMessage ? <p className="ltc-muted" style={{ marginTop: 10 }}>{requestMessage}</p> : null}
        {challengeId ? (
          <p className="ltc-muted" style={{ marginTop: 10 }}>
            Challenge: <code data-testid="auth-challenge-id">{challengeId}</code>
          </p>
        ) : null}
        {devOtp ? (
          <p className="ltc-muted" style={{ marginTop: 10 }}>
            Dev-OTP: <code data-testid="auth-dev-otp">{devOtp}</code>
          </p>
        ) : null}
      </section>

      <section className="ltc-card" style={{ marginTop: 16 }}>
        <h2>Schritt 2: Verify</h2>

        {consentLoading ? <p className="ltc-muted">Lade Consent-Versionen...</p> : null}
        {consentLoadError ? <InlineErrorBanner message={consentLoadError} /> : null}

        {!consentLoading && !consentLoadError ? (
          <>
            <p className="ltc-muted">
              Für den Login-Vertrag werden die aktuellen Consent-Versionen mitgegeben: <code>{consentSummary}</code>
            </p>

            <form onSubmit={(e) => void onVerify(e)}>
              <label>
                OTP
                <input
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  autoComplete="one-time-code"
                  placeholder="Einmalcode"
                  style={{ display: "block", marginTop: 8, padding: 10, width: "100%", maxWidth: 240 }}
                />
              </label>

              <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
                <label>
                  <input type="checkbox" checked={termsChecked} onChange={(e) => setTermsChecked(e.target.checked)} /> Ich bestätige die
                  aktuelle Terms-Version.
                </label>
                <label>
                  <input type="checkbox" checked={privacyChecked} onChange={(e) => setPrivacyChecked(e.target.checked)} /> Ich bestätige die
                  aktuelle Privacy-Version.
                </label>
              </div>

              <button type="submit" disabled={busy === "verify" || !canVerify} style={{ marginTop: 12 }}>
                {busy === "verify" ? "Verifiziert..." : "Login verifizieren"}
              </button>
            </form>
          </>
        ) : null}
      </section>

      {error ? <InlineErrorBanner message={error} /> : null}

      <section style={{ marginTop: 16 }}>
        <h2>Navigation (Hash)</h2>
        <ul>
          <li>
            <a href={`#/consent?next=${encodeURIComponent(nextHash)}`}>Weiter zu Consent</a>
          </li>
          <li>
            <a href={nextHash}>Zum Zielbereich</a>
          </li>
        </ul>
      </section>
    </main>
  );
}
