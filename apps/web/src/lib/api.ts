export const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
export const API_PUBLIC_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_INTERNAL_URL}/api/v1${path}`, {
    cache: "no-store",
    signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) throw new Error(`API ${path} returned ${response.status}`);
  return response.json() as Promise<T>;
}

export const money = (value: number | string) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(Number(value));

export const percent = (value: number | string) =>
  new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 2 }).format(Number(value));
