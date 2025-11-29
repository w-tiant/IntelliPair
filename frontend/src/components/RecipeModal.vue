<template>
  <transition name="modal-fade">
    <div class="modal-overlay" @click="$emit('close')">
      <div class="modal-window" @click.stop>
        
        <!-- 头部 -->
        <header class="modal-header">
          <div class="header-title">
            <span class="icon">📖</span>
            <h3>菜谱佐证</h3>
          </div>
          <button @click="$emit('close')" class="close-btn" title="关闭">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </header>

        <div class="modal-body">
          <!-- 加载状态 -->
          <div v-if="isLoading" class="status-panel loading-panel">
            <div class="spinner-ring"></div>
            <p>正在连接全网数据库...</p>
          </div>

          <!-- 错误状态 -->
          <div v-else-if="error" class="status-panel error-panel">
            <div class="error-icon">⚠️</div>
            <p><strong>检索中断</strong><br>{{ error }}</p>
          </div>

          <!-- 成功且有结果 -->
          <ul v-else-if="recipes && recipes.length > 0" class="recipe-list">
            <li 
              v-for="(recipe, index) in recipes" 
              :key="recipe.url"
              :style="{ animationDelay: `${index * 0.05}s` }"
              class="recipe-item"
            >
              <a :href="recipe.url" target="_blank" rel="noopener noreferrer" class="recipe-link">
                <div class="recipe-info">
                  <span class="recipe-name">{{ recipe.title }}</span>
                  <span class="recipe-source-badge">来自 {{ recipe.source || '全网搜索' }}</span>
                </div>
                <div class="link-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                </div>
              </a>
            </li>
          </ul>

          <!-- 成功但无结果 -->
          <div v-else class="status-panel empty-panel">
            <span class="empty-icon">🍃</span>
            <p>这是一个极其罕见的独特组合。<br>未在公开数据库中找到先例。</p>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  isLoading: Boolean,
  recipes: Array,
  error: String,
});
defineEmits(['close']);
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;

  background-color: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(8px); 
  -webkit-backdrop-filter: blur(8px);

  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal-window {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 24px;
  
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  
  box-shadow: 
    0 20px 50px -10px rgba(0, 0, 0, 0.15), 
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
    
  overflow: hidden;
  transform: translateZ(0); /* 开启 GPU 加速 */
}

/* --- 头部 --- */
.modal-header {
  padding: 1.2rem 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.4);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.header-title .icon { font-size: 1.4rem; }

.modal-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: 0.02em;
}

.close-btn {
  background: rgba(0, 0, 0, 0.05);
  border: none;
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}
.close-btn svg { width: 18px; height: 18px; }

.close-btn:hover {
  background: #ef4444;
  color: white;
  transform: rotate(90deg);
}

/* --- 内容区 --- */
.modal-body {
  padding: 1rem;
  overflow-y: auto;
  background: rgba(241, 245, 249, 0.3);
  flex-grow: 1;
}

/* --- 列表项：悬浮条 --- */
.recipe-list {
  list-style: none !important;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.recipe-item {
  /* 进场动画 */
  opacity: 0;
  transform: translateY(10px);
  animation: slideUp 0.4s ease-out forwards;
  list-style: none !important;
  list-style-type: none !important;
}

.recipe-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.2rem;
  text-decoration: none;
  
  /* 卡片样式 */
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.02);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.recipe-link:hover {
  background: #fff;
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 8px 20px -4px rgba(var(--brand-color-rgb, 249, 115, 22), 0.15);
  border-color: var(--brand-color);
}

.recipe-info {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.recipe-name {
  font-weight: 600;
  color: #334155;
  font-size: 1rem;
}
.recipe-link:hover .recipe-name { color: var(--brand-color); }

.recipe-source-badge {
  font-size: 0.75rem;
  color: #94a3b8;
  background: rgba(0,0,0,0.05);
  padding: 2px 6px;
  border-radius: 4px;
  align-self: flex-start;
}

.link-icon {
  color: #cbd5e1;
  transition: transform 0.2s;
}
.link-icon svg { width: 20px; height: 20px; }

.recipe-link:hover .link-icon {
  color: var(--brand-color);
  transform: translate(2px, -2px);
}

/* --- 状态面板 --- */
.status-panel {
  text-align: center;
  padding: 3rem 1rem;
  color: #64748b;
}

.loading-panel .spinner-ring {
  width: 40px; height: 40px;
  border: 3px solid rgba(var(--brand-color-rgb, 249, 115, 22), 0.2);
  border-top-color: var(--brand-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

.error-panel {
  background: rgba(254, 226, 226, 0.5);
  border-radius: 12px;
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.2);
}
.error-icon { font-size: 2rem; margin-bottom: 0.5rem; }

.empty-panel .empty-icon { font-size: 3rem; display: block; margin-bottom: 1rem; opacity: 0.5; }

/* --- 动画 --- */
.modal-fade-enter-active, .modal-fade-leave-active {
  transition: opacity 0.3s ease;
}
.modal-fade-enter-from, .modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .modal-window {
  animation: popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.modal-fade-leave-active .modal-window {
  animation: popOut 0.2s ease-in;
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
@keyframes popIn { from { opacity: 0; transform: scale(0.9) translateY(20px); } to { opacity: 1; transform: scale(1) translateY(0); } }
@keyframes popOut { to { opacity: 0; transform: scale(0.95) translateY(10px); } }
</style>