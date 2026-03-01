import { useState } from "react";

type CookiePrefs = {
  necessary: true;
  analytics: boolean;
  marketing: boolean;
  savedAtIso: string;
};

const COOKIE_KEY = "ltc_cookie_prefs_v1";

function loadCookiePrefs(): CookiePrefs | null {
  try {
    const raw = localStorage.getItem(COOKIE_KEY);
    if (!raw) return null;
    const prefs = JSON.parse(raw) as Partial<CookiePrefs>;
    if (prefs.necessary !== true) return null;
    if (typeof prefs.analytics !== "boolean") return null;
    if (typeof prefs.marketing !== "boolean") return null;
    if (typeof prefs.savedAtIso !== "string") return null;
    return prefs as CookiePrefs;
  } catch {
    return null;
  }
}

function saveCookiePrefs(next: Omit<CookiePrefs, "savedAtIso">) {
  const prefs: CookiePrefs = { ...next, savedAtIso: new Date().toISOString() };
  localStorage.setItem(COOKIE_KEY, JSON.stringify(prefs));
  return prefs;
}

export default function CookieSettingsCard(props: { onSaved?: () => void }): JSX.Element {
  const [prefs, setPrefs] = useState<CookiePrefs>(() => {
    return (
      loadCookiePrefs() ?? {
        necessary: true,
        analytics: false,
        marketing: false,
        savedAtIso: new Date(0).toISOString(),
      }
    );
  });

  return (
    <div className="ltc-card">
      <div className="ltc-card__title">Cookie-Einstellungen</div>
      <div className="ltc-muted">Notwendig ist immer aktiv. Analytics ist optional. Marketing/Tracking ist deaktiviert.</div>

      <div className="ltc-divider" />

      <div className="ltc-row">
        <div id="cookies-necessary-copy">
          <div className="ltc-strong">Notwendig</div>
          <div className="ltc-muted">Sitzung, Sicherheit, grundlegende Funktionen</div>
        </div>
        <input type="checkbox" checked disabled className="ltc-check" aria-describedby="cookies-necessary-copy" />
      </div>

      <div className="ltc-divider" />

      <div className="ltc-row">
        <div id="cookies-analytics-copy">
          <div className="ltc-strong">Analytics (optional)</div>
          <div className="ltc-muted">anonymisierte Nutzungsstatistik zur Verbesserung</div>
        </div>
        <input
          id="cookies-analytics-toggle"
          type="checkbox"
          checked={prefs.analytics}
          onChange={(event) => setPrefs((current) => ({ ...current, analytics: event.target.checked }))}
          className="ltc-check"
          aria-describedby="cookies-analytics-copy"
        />
      </div>

      <div className="ltc-divider" />

      <div className="ltc-row">
        <div id="cookies-marketing-copy">
          <div className="ltc-strong">Marketing/Tracking</div>
          <div className="ltc-muted">derzeit nicht verwendet</div>
        </div>
        <input type="checkbox" checked={prefs.marketing} disabled className="ltc-check" aria-describedby="cookies-marketing-copy" />
      </div>

      <div className="ltc-actions">
        <button
          type="button"
          className="ltc-btn ltc-btn--primary"
          onClick={() => {
            saveCookiePrefs({ necessary: true, analytics: prefs.analytics, marketing: false });
            props.onSaved?.();
          }}
        >
          Speichern
        </button>

        <button
          type="button"
          className="ltc-btn ltc-btn--ghost"
          onClick={() => {
            const nextPrefs = saveCookiePrefs({ necessary: true, analytics: false, marketing: false });
            setPrefs(nextPrefs);
            props.onSaved?.();
          }}
        >
          Nur notwendig
        </button>
      </div>

      <div className="ltc-meta">
        Gespeichert in <code>localStorage</code> unter <code>{COOKIE_KEY}</code>.
      </div>
    </div>
  );
}
