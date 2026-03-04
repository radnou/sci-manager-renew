<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchBiens } from '$lib/api';
  let biens = [];
  onMount(async () => {
    biens = await fetchBiens();
  });
</script>

<h2>Biens</h2>
{#if biens.length === 0}
  <p>No properties yet.</p>
{:else}
  <ul>
    {#each biens as b}
      <li>{b.adresse} ({b.ville})</li>
    {/each}
  </ul>
{/if}
