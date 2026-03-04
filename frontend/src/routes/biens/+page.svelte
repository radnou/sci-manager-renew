<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchBiens, createBien } from '$lib/api';
  let biens = [];
  let newAdresse = '';
  let newVille = '';

  onMount(async () => {
    biens = await fetchBiens();
  });

  async function addBien() {
    const payload: any = { adresse: newAdresse };
    if (newVille) payload.ville = newVille;
    const created = await createBien(payload);
    biens = [...biens, created];
    newAdresse = '';
    newVille = '';
  }
</script>

<h2>Biens</h2>
<form on:submit|preventDefault={addBien} class="mb-4">
  <input bind:value={newAdresse} placeholder="Adresse" required class="mr-2" />
  <input bind:value={newVille} placeholder="Ville" class="mr-2" />
  <button type="submit" class="btn btn-primary">Ajouter</button>
</form>

{#if biens.length === 0}
  <p>No properties yet.</p>
{:else}
  <ul>
    {#each biens as b}
      <li>{b.adresse} {#if b.ville}({b.ville}){/if}</li>
    {/each}
  </ul>
{/if}
