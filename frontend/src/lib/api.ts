export async function fetchBiens() {
  const res = await fetch('/v1/biens');
  return res.json();
}

export async function fetchLoyers() {
  const res = await fetch('/v1/loyers');
  return res.json();
}
