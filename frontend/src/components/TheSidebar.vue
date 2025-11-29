
<template>
  <nav class="tab-shelf">
    <button class="tab-item is-recommend" @click="workbench.createCard('recommend')">
      <span>常规推荐</span>
    </button>
    <button class="tab-item is-alchemy" @click="workbench.createCard('alchemy')">
      <span>风味炼金术</span>
    </button>
    <button class="tab-item is-pathfinder" @click="workbench.createCard('pathfinder')">
      <span>搭配探路者</span>
    </button>
  </nav>
</template>

<script setup>
import { useWorkbenchStore } from '../stores/workbench';
const workbench = useWorkbenchStore();
</script>

<style scoped>
.tab-shelf {
  position: fixed;
  top: 7rem;
  left: 2rem;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1.25rem;
  perspective: 1000px; 
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.5rem;
  border-radius: 16px;
  
  /* 玻璃质感基础 */
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.6); /* 玻璃边缘高光，比之前更亮一点 */
  
  /* 字体 */
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  
  /* 交互 */
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  
  /* 呼吸动画 */
  animation: float 5s ease-in-out infinite;
}

.icon {
  font-size: 1.2rem;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}


/* 1. 常规推荐 */
.tab-item.is-recommend {
  background: linear-gradient(135deg, rgba(255, 228, 230, 0.6) 0%, rgba(255, 255, 255, 0.4) 100%);
  box-shadow: 0 8px 32px -4px rgba(244, 63, 94, 0.15), 
              inset 0 0 0 1px rgba(255, 255, 255, 0.4);
  color: #9f1239;
  animation-delay: 0s;
}

/* 2. 风味炼金术 */
.tab-item.is-alchemy {
  background: linear-gradient(135deg, rgba(220, 252, 231, 0.6) 0%, rgba(255, 255, 255, 0.4) 100%);
  box-shadow: 0 8px 32px -4px rgba(34, 197, 94, 0.15),
              inset 0 0 0 1px rgba(255, 255, 255, 0.4);
  color: #14532d;
  
  animation-delay: 1.5s;
}

/* 3. 搭配探路者 */
.tab-item.is-pathfinder {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.6) 0%, rgba(255, 255, 255, 0.4) 100%);
  box-shadow: 0 8px 32px -4px rgba(59, 130, 246, 0.15),
              inset 0 0 0 1px rgba(255, 255, 255, 0.4);
  color: #1e3a8a;
  
  animation-delay: 3s;
}

/* 交互状态 ------------------- */

/* 悬停：变亮、上浮、光晕增强 */
.tab-item:hover {
  transform: translateY(-4px) scale(1.02);
  background: rgba(255, 255, 255, 0.85); /* 稍微变白，提高可读性 */
  border-color: #fff;
}

.tab-item.is-recommend:hover {
  box-shadow: 0 15px 40px -4px rgba(244, 63, 94, 0.3);
}
.tab-item.is-alchemy:hover {
  box-shadow: 0 15px 40px -4px rgba(34, 197, 94, 0.3);
}
.tab-item.is-pathfinder:hover {
  box-shadow: 0 15px 40px -4px rgba(59, 130, 246, 0.3);
}

.tab-item:active {
  transform: translateY(0) scale(0.98);
}

/* 浮动动画 */
@keyframes float {
  0% { 
    transform: translateY(0px); 
    box-shadow: var(--original-shadow); 
  }
  50% { 
    transform: translateY(-6px);
  }
  100% { 
    transform: translateY(0px); 
  }
}
</style>