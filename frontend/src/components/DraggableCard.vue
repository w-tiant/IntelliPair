<template>
  <div 
    ref="cardRef"
    class="draggable-card"
    :style="cardStyle"
    @mousedown="onCardMouseDown"
  >
    <!-- 头部 -->
    <header ref="handleRef" class="card-header">
      <div class="header-content">
        <span class="status-dot"></span>
        <span class="card-title">{{ title }}</span>
      </div>
      <button class="close-button" @click.stop="workbench.deleteCard(id)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </header>
    
    <div class="card-content">
      <component :is="cardComponent" :cardData="props.data" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent } from 'vue';
import { useDraggable } from '@vueuse/core';
import { useWorkbenchStore } from '../stores/workbench';

const cardComponentMap = {
  recommend: defineAsyncComponent(() => import('./cards/RecommendCard.vue')),
  alchemy: defineAsyncComponent(() => import('./cards/AlchemyCard.vue')),
  pathfinder: defineAsyncComponent(() => import('./cards/PathfinderCard.vue')),
  concept: defineAsyncComponent(() => import('./cards/ConceptResultCard.vue')),
};

const props = defineProps({
  id: Number, type: String, title: String,
  x: Number, y: Number, width: Number, height: Number, zIndex: Number,
  data: Object,
});

const cardComponent = cardComponentMap[props.type];
const workbench = useWorkbenchStore();
const cardRef = ref(null);
const handleRef = ref(null);

const { x, y } = useDraggable(cardRef, {
  initialValue: { x: props.x, y: props.y },
  handle: handleRef,
});

// --- 卡片主题色 ---
const themeColors = {
  recommend:  '244, 63, 94',  /* Rose-500 */
  alchemy:    '34, 197, 94',  /* Green-500 */
  pathfinder: '59, 130, 246', /* Blue-500 */
  concept:    '249, 115, 22', /* Orange-500 */
  default:    '148, 163, 184' /* Gray-400 */
};

const currentTheme = computed(() => themeColors[props.type] || themeColors.default);

const cardStyle = computed(() => ({
  transform: `translate(${x.value}px, ${y.value}px)`,
  width: `${props.width}px`, 
  height: `${props.height}px`, 
  zIndex: props.zIndex,
  '--card-theme': currentTheme.value,
}));

function onCardMouseDown() {
  workbench.bringToFront(props.id);
}
</script>

<style scoped>
.draggable-card {
  position: absolute;
  top: 0; left: 0;
  display: flex;
  flex-direction: column;
  
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  
  /* --- 彩色环境光阴影 --- */
  box-shadow: 
    0 20px 50px -12px rgba(var(--card-theme), 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
    
  transition: box-shadow 0.3s ease, transform 0.1s;
}

.draggable-card:active {
  box-shadow: 
    0 30px 60px -12px rgba(var(--card-theme), 0.35),
    0 0 0 1px rgba(255, 255, 255, 0.6) inset;
  cursor: grabbing;
}

.card-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  cursor: grab;
  
  background: linear-gradient(to bottom, rgba(var(--card-theme), 0.15) 0%, rgba(var(--card-theme), 0) 100%);
  border-bottom: 1px solid rgba(var(--card-theme), 0.1);
  
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
}
.card-header:active { cursor: grabbing; }

.header-content {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background-color: rgb(var(--card-theme));
  box-shadow: 0 0 8px rgba(var(--card-theme), 0.6); /* 圆点发光 */
}

.card-title {
  font-weight: 600;
  font-size: 1rem;
  color: #1e293b;
  letter-spacing: 0.02em;
}

.close-button {
  background: rgba(var(--card-theme), 0.1);
  border: none;
  width: 28px; height: 28px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  color: rgb(var(--card-theme));
  transition: all 0.2s;
}

.close-button svg { width: 16px; height: 16px; }

.close-button:hover {
  background: rgb(var(--card-theme));
  color: white;
  transform: rotate(90deg);
}

.card-content {
  flex-grow: 1;
  display: flex;
  min-height: 0;
  /* 内容区不需要背景色，直接透出父级的毛玻璃 */
  background: transparent; 
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
}
</style>