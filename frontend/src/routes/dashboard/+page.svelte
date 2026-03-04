<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchBiens } from '$lib/api';
  let biens = [];
  onMount(async () => {
    biens = await fetchBiens();
  });
</script>

<h2>Dashboard</h2>
<ul>
  {#each biens as b}
    <li>{b.adresse}</li>
  {/each}
</ul>
