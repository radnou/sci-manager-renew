<script lang="ts">
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  onMount(() => { goto('/pricing', { replaceState: true }); });
</script>
<section class="sci-page-shell">
  <p class="text-sm text-slate-500">Redirection vers les tarifs...</p>
</section>
