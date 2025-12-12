<template>
  <div class="dashboard">
    <h1>WH Dashboard</h1>
    <p>Дашборд склада</p>
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
