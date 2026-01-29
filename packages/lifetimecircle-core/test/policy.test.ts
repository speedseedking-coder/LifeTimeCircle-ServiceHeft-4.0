import test from "node:test";
import assert from "node:assert/strict";

import { can } from "../src/rbac/policy.js";
import type { Subject } from "../src/rbac/roles.js";

const publicSubject: Subject = { userId: null, role: "public" };
const userSubject: Subject = { userId: "u1", role: "user" };
const vipSubject: Subject = { userId: "v1", role: "vip" };
const dealerSubject: Subject = { userId: "d1", role: "dealer", orgId: "org1" };
const adminSubject: Subject = { userId: "a1", role: "admin", isSuperAdmin: true };

test("public kann Public-QR öffnen", () => {
  assert.equal(can({ subject: publicSubject, permission: "publicQr.open" }), true);
});

test("public kann kein Fahrzeug anlegen", () => {
  assert.equal(can({ subject: publicSubject, permission: "vehicle.create" }), false);
});

test("user kann eigenes Fahrzeug lesen", () => {
  assert.equal(
    can({
      subject: userSubject,
      permission: "vehicle.read.own",
      resource: { type: "vehicle", id: "veh1", ownerUserId: "u1" }
    }),
    true
  );
});

test("user kann fremdes Dokument nicht lesen", () => {
  assert.equal(
    can({
      subject: userSubject,
      permission: "document.content.read.own",
      resource: { type: "document", id: "doc1", ownerUserId: "x" }
    }),
    false
  );
});

test("vip kann Dokument nur wenn berechtigt (granted) lesen", () => {
  assert.equal(
    can({
      subject: vipSubject,
      permission: "document.content.read.any",
      resource: { type: "document", id: "doc1", ownerUserId: "x", grantedUserIds: ["v1"] }
    }),
    true
  );
});

test("vip kann Übergabe-QR erzeugen", () => {
  assert.equal(can({ subject: vipSubject, permission: "transfer.generate" }), true);
});

test("user kann Übergabe-QR NICHT erzeugen", () => {
  assert.equal(can({ subject: userSubject, permission: "transfer.generate" }), false);
});

test("dealer kann Übergabe-QR erzeugen", () => {
  assert.equal(can({ subject: dealerSubject, permission: "transfer.generate" }), true);
});

test("moderator kann nur blog schreiben (auth) aber sonst nichts", () => {
  const mod: Subject = { userId: "m1", role: "moderator" };
  assert.equal(can({ subject: mod, permission: "blog.write" }), true);
  assert.equal(can({ subject: mod, permission: "vehicle.create" }), false);
});

test("admin full export nur mit superadmin-claim", () => {
  const adminNoSuper: Subject = { userId: "a2", role: "admin", isSuperAdmin: false };
  assert.equal(can({ subject: adminNoSuper, permission: "export.full" }), false);
  assert.equal(can({ subject: adminSubject, permission: "export.full" }), true);
});
