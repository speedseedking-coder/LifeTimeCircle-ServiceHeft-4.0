export type TrustFolderContext = { vehicleId: string; addonKey: string };

export function readTrustFolderContextFromHash(hash: string): TrustFolderContext {
  const queryIndex = (hash ?? "").indexOf("?");
  if (queryIndex < 0) return { vehicleId: "", addonKey: "restauration" };

  const query = hash.slice(queryIndex + 1);
  const params = new URLSearchParams(query);

  return {
    vehicleId: (params.get("vehicle_id") ?? "").trim(),
    addonKey: (params.get("addon_key") ?? "restauration").trim() || "restauration",
  };
}