import fetch from 'node-fetch';

(async () => {
  try {
    const res = await fetch('http://localhost:8000/rest/v1', {
      headers: { apikey: 'anon_key_example' },
    });
    console.log('supabase rest status', res.status);
    const text = await res.text();
    console.log('body', text.slice(0, 200));
  } catch (err) {
    console.error('fetch error', err);
  }
})();
