<script lang="ts">
  import { supabase } from '$lib/supabase';
  let email = '';
  let password = '';

  async function signIn() {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
      alert(error.message);
    } else {
      window.location.href = '/dashboard';
    }
  }
</script>

<h2>Login</h2>
<input type="email" bind:value={email} placeholder="Email" />
<input type="password" bind:value={password} placeholder="Password" />
<button on:click={signIn}>Sign In</button>
