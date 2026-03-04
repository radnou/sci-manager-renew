<script lang="ts">
  export let title: string;
  export let value: string | number;
</script>

<div class="p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
  <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</h3>
  <p class="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">{value}</p>
</div>
