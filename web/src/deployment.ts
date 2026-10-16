export const RECORDED_DEMO = "https://youtu.be/_a0vrYwOlME";
export const PUBLIC_WRITE_REASON =
  "Public read-only demo: writes are disabled.";

export function deploymentMode() {
  const declared = document.querySelector<HTMLMetaElement>(
    'meta[name="decisiondebt-mode"]',
  )?.content;
  if (declared === "local-admin" || declared === "public-readonly")
    return declared;
  return import.meta.env.DEV ? "local-admin" : "public-readonly";
}
