<template>
  <div class="dashboard">
    <h1>PP Dashboard</h1>
    <p>Дашборд пункта выдачи</p>
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
