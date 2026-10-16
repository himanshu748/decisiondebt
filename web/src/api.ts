export async function api<T>(
  path: string,
  body?: unknown,
  token?: string,
): Promise<T> {
  const r = await fetch("/api" + path, {
    method: body === undefined ? "GET" : "POST",
    headers: {
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: "Bearer " + token } : {}),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await r.json();
  if (!r.ok)
    throw new Error(
      data.error?.message ||
        data.detail?.[0]?.msg ||
        "Request failed (" + r.status + ")",
    );
  return data;
}
