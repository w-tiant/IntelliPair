<template>
  <div class="hero-container" :class="{ 'is-minimized': hasCards }">
    <div class="hero-content">
      <!-- 主标题 -->
      <h1 class="hero-title">
        <span class="word">IntelliPair</span>
      </h1>
      <!-- 副标题 -->
      <p class="hero-subtitle">——— 探索风味的分子级连接 ———</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useWorkbenchStore } from '../stores/workbench';

const workbench = useWorkbenchStore();
const hasCards = computed(() => workbench.cards.length > 0);
</script>

<style scoped>
.hero-container {
  position: fixed;
  z-index: 0; /* 在背景之上，卡片之下 */
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  
  pointer-events: none;
  transition: all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  
  white-space: nowrap;
  text-align: center;
}

/* 最小化状态 (飞往左上角) */
.hero-container.is-minimized {
  top: 1.5rem;
  left: 2rem;
  transform: translate(0, 0) scale(0.35);
  transform-origin: top left;
}

/* 主标题样式 */
.hero-title {
  margin: 0;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  font-weight: 900;
  font-size: 5rem;
  letter-spacing: -0.02em;
  line-height: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  
  background: linear-gradient(135deg, #334155 0%, #57534e 20%, #ea580c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 20px 30px rgba(249, 115, 22, 0.15));
}

.hero-container.is-minimized .hero-title {
  background: linear-gradient(135deg, #1e293b 0%, #f97316 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  
  filter: none;
}

.word {
  display: block;
}

/* 副标题样式 */
.hero-subtitle {
  margin-top: 1.5rem;
  font-size: 1.2rem;
  color: #78716c; 
  font-weight: 500;
  letter-spacing: 0.3em;
  opacity: 1;
  transition: all 0.5s ease;
}

/* 最小化时，副标题消失 */
.hero-container.is-minimized .hero-subtitle {
  opacity: 0;
  transform: translateY(-20px);
  pointer-events: none;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .hero-title { font-size: 3rem; }
  .hero-container.is-minimized { 
    transform: translate(0, 0) scale(0.5);
  }
}
</style>