<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchLoyers, createLoyer } from '$lib/api';
  let loyers = [];
  let newIdBien = '';
  let newDate = '';
  let newMontant: number | string = '';

  onMount(async () => {
    loyers = await fetchLoyers();
  });

  async function addLoyer() {
    const payload: any = {
      id_bien: newIdBien,
      date_loyer: newDate,
      montant: parseFloat(newMontant as string),
    };
    const created = await createLoyer(payload);
    loyers = [...loyers, created];
    newIdBien = '';
    newDate = '';
    newMontant = '';
  }
</script>

<h2>Loyers</h2>
<form on:submit|preventDefault={addLoyer} class="mb-4">
  <input bind:value={newIdBien} placeholder="ID Bien" required class="mr-2" />
  <input bind:value={newDate} type="date" required class="mr-2" />
  <input bind:value={newMontant} type="number" placeholder="Montant" required class="mr-2" />
  <button type="submit" class="btn btn-primary">Ajouter</button>
</form>

{#if loyers.length === 0}
  <p>No rents recorded.</p>
{:else}
  <ul>
    {#each loyers as l}
      <li>{l.date_loyer} – {l.montant}€</li>
    {/each}
  </ul>
{/if}
