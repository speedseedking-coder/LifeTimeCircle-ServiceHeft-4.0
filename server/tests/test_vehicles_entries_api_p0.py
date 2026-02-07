
# --- LTC PATCH: BYPASS VEHICLES CONSENT DEPENDENCY (P0) ---
class _AsActorCtx:
    def __init__(self, client, actor):
        self.client = client
        self.actor = actor
        self._ga = None
        self._rc = None
        self._had_ga = False
        self._old_ga = None
        self._had_rc = False
        self._old_rc = None

    def __enter__(self):
        ga = globals().get('get_actor')
        if ga is None:
            raise AssertionError('get_actor not available in test module')
        self._ga = ga

        rc = None
        try:
            from app.routers import vehicles as vmod  # type: ignore
            rc = getattr(vmod, 'require_consent', None)  # type: ignore
        except Exception:  # pragma: no cover
            rc = None
        self._rc = rc

        ov = self.client.app.dependency_overrides
        if self._ga in ov:
            self._had_ga = True
            self._old_ga = ov.get(self._ga)
        ov[self._ga] = (lambda: self.actor)

        if self._rc is not None:
            if self._rc in ov:
                self._had_rc = True
                self._old_rc = ov.get(self._rc)
            ov[self._rc] = (lambda *a, **kw: None)

        return self

    def __exit__(self, exc_type, exc, tb):
        ov = self.client.app.dependency_overrides
        if self._ga is not None:
            if self._had_ga:
                ov[self._ga] = self._old_ga
            else:
                ov.pop(self._ga, None)
        if self._rc is not None:
            if self._had_rc:
                ov[self._rc] = self._old_rc
            else:
                ov.pop(self._rc, None)
        return False

def _as_actor(client, actor):
    return _AsActorCtx(client, actor)

def _ensure_consent(client) -> None:
    # Consent wird separat getestet; hier nur Vehicles/Entries-Logik.
    return
