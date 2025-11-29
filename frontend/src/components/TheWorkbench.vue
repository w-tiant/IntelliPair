
<template>
  <main class="workbench-canvas">
    <DraggableCard 
      v-for="card in workbench.cards" 
      :key="card.id"
      :id="card.id"
      :type="card.type"
      :title="card.title"
      :x="card.x"
      :y="card.y"
      :width="card.width"
      :height="card.height"
      :z-index="card.zIndex"
      :data="card.data"
    />
  </main>
</template>

<script setup>
import { useWorkbenchStore } from '../stores/workbench';
import DraggableCard from './DraggableCard.vue';

const workbench = useWorkbenchStore();
</script>

<style scoped>
.workbench-canvas {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}
</style>