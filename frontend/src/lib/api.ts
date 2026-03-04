export async function fetchBiens() {
  const res = await fetch('/v1/biens');
  return res.json();
}

export async function createBien(bien: Record<string, any>) {
  const res = await fetch('/v1/biens', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(bien),
  });
  return res.json();
}

export async function fetchLoyers() {
  const res = await fetch('/v1/loyers');
  return res.json();
}

export async function createLoyer(loyer: Record<string, any>) {
  const res = await fetch('/v1/loyers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(loyer),
  });
  return res.json();
}
