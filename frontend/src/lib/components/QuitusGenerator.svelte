<script lang="ts">
  let pdfUrl = '';
  async function generate() {
    const res = await fetch('/v1/quitus');
    const blob = await res.blob();
    pdfUrl = URL.createObjectURL(blob);
  }
</script>

<button on:click={generate} class="px-4 py-2 bg-blue-500 text-white rounded">Générer quittus</button>
{#if pdfUrl}
  <iframe src={pdfUrl} class="w-full h-96 mt-4"></iframe>
{/if}
