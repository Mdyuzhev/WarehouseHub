<template>
  <div class="dashboard">
    <h1>DC Dashboard</h1>
    <p>Дашборд распределительного центра</p>
  </div>
</template>

<script setup>
import { useFacilityStore } from '../../stores/facility'

const facilityStore = useFacilityStore()
</script>

<style scoped>
.dashboard {
  padding: 2rem;
}
</style>
