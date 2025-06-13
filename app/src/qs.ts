export function stringify(result: Record<string, string | undefined>) {
  const res = new URLSearchParams(
    Object.entries(result)
      .filter(([, value]) => value !== undefined)
      .map(([key, value]) => [key, value] as [string, string]),
  );
  return res.toString();
}
