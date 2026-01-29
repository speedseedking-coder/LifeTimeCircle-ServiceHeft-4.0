export const PERMISSIONS = [
  // Public-QR
  "publicQr.open",
  "publicQr.viewIndicators",

  // Serviceheft: Fahrzeuge & Einträge
  "vehicle.create",
  "vehicle.read.own",
  "vehicle.read.granted",
  "vehicle.read.any",
  "entry.create.own",
  "entry.update.own",
  "entry.delete.own",

  // Dokumente/Bilder
  "document.upload.own",
  "document.meta.read.own",
  "document.meta.read.granted",
  "document.content.read.own",
  "document.content.read.granted",
  "document.content.read.any",
  "image.vipOnly.view",

  // Verkauf/Übergabe
  "transfer.generate",
  "sale.internal.start",
  "audit.read.own",
  "audit.read.any",

  // Blog/News
  "blog.read",
  "blog.write",
  "blog.delete.own",
  "blog.delete.any",

  // Newsletter
  "newsletter.subscription.manage.own",
  "newsletter.send",

  // Admin/Governance
  "admin.roles.assign",
  "admin.moderator.accredit",
  "admin.vipBusiness.staff.approve",
  "admin.holderData.read",

  // Exports
  "export.redacted",
  "export.full"
] as const;

export type Permission = typeof PERMISSIONS[number];
