<script lang="ts">
  export let biens = [] as any[];
</script>

<table class="min-w-full divide-y divide-gray-200">
  <thead class="bg-gray-50">
    <tr>
      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Adresse</th>
      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ville</th>
      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Loyer CC</th>
    </tr>
  </thead>
  <tbody class="bg-white divide-y divide-gray-200">
    {#each biens as bien}
      <tr>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{bien.adresse}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{bien.ville}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{bien.loyer_cc}</td>
      </tr>
    {/each}
  </tbody>
</table>
