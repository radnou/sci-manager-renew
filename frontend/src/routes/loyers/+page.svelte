<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchLoyers } from '$lib/api';
  let loyers = [];
  onMount(async () => {
    loyers = await fetchLoyers();
  });
</script>

<h2>Loyers</h2>
{#if loyers.length === 0}
  <p>No rents recorded.</p>
{:else}
  <ul>
    {#each loyers as l}
      <li>{l.date_loyer} – {l.montant}€</li>
    {/each}
  </ul>
{/if}
