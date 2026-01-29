import test from "node:test";
import assert from "node:assert/strict";

import { computePublicQrTrust, PUBLIC_QR_DISCLAIMER } from "../src/publicQr/trustscore.js";

test("grün bei guter Doku, regelmäßig, Unfall ok", () => {
  const res = computePublicQrTrust({
    hasHistory: true,
    verification: "t3",
    isRegularlyUpdated: true,
    hasAccident: true,
    accidentClosedWithEvidence: true
  });
  assert.equal(res.light, "gruen");
  assert.equal(res.disclaimer, PUBLIC_QR_DISCLAIMER);
});

test("rot ohne Historie", () => {
  const res = computePublicQrTrust({
    hasHistory: false,
    verification: "t3",
    isRegularlyUpdated: true,
    hasAccident: false,
    accidentClosedWithEvidence: false
  });
  assert.equal(res.light, "rot");
});

test("orange bei Unfall offen/ohne Belege", () => {
  const res = computePublicQrTrust({
    hasHistory: true,
    verification: "t2",
    isRegularlyUpdated: true,
    hasAccident: true,
    accidentClosedWithEvidence: false
  });
  assert.equal(res.light, "orange");
});

test("keine Public-Metriken: keine Zahlen/Counts/Prozente/Zeiträume im Output", () => {
  const res = computePublicQrTrust({
    hasHistory: true,
    verification: "t1",
    isRegularlyUpdated: false,
    hasAccident: false,
    accidentClosedWithEvidence: false
  });

  const joined = [res.light, ...res.indicators, res.disclaimer].join(" ");
  assert.equal(/[0-9]/.test(joined), false);
});
