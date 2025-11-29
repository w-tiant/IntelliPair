
<template>
  <div>
    <!-- 购物篮触发器 -->
    <button class="shopping-list-toggle" @click="store.togglePanel()" title="打开购物清单">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49A1.003 1.003 0 0 0 20 4H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/></svg>
      <span v-if="store.itemCount > 0" class="badge">{{ store.itemCount }}</span>
    </button>

    <!-- 右侧滑出面板 -->
    <transition name="slide-fade">
      <div v-if="store.isPanelVisible" class="shopping-list-panel">
        <header class="panel-header">
          <h3>购物清单</h3>
          <button @click="store.togglePanel()" class="close-panel-btn" title="关闭">×</button>
        </header>
        
        <div class="list-content">
          <ul v-if="store.itemCount > 0">
            <li v-for="item in store.items" :key="item">
              <span>{{ item }}</span>
              <button @click="store.removeItem(item)" class="remove-item-btn" title="移除">×</button>
            </li>
          </ul>
          <div v-else class="empty-state">
            <p>点击食材旁的 "+" 号<br>将它添加到这里吧！</p>
          </div>
        </div>

        <footer v-if="store.itemCount > 0" class="panel-footer">
          <button @click="copyList" class="action-btn copy-btn">{{ copyButtonText }}</button>
          <button @click="store.clearList()" class="action-btn clear-btn">清空</button>
        </footer>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useShoppingListStore } from '../stores/shoppingList';

const store = useShoppingListStore();
const copyButtonText = ref('复制清单');

function copyList() {
  const listText = Array.from(store.items).join('\n');
  navigator.clipboard.writeText(listText).then(() => {
    copyButtonText.value = '已复制!';
    setTimeout(() => {
      copyButtonText.value = '复制清单';
    }, 2000);
  });
}
</script>

<style scoped>
/* 悬浮球按钮 */
.shopping-list-toggle {
  position: fixed;
  bottom: 2rem;
  right: 2.5rem;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  
  /* 渐变球 */
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  color: white;
  border: none;
  cursor: pointer;
  
  box-shadow: 0 10px 25px -5px rgba(249, 115, 22, 0.5);
  
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); /* 弹性动画 */
  z-index: 1001;
}

.shopping-list-toggle:hover {
  transform: scale(1.1) rotate(-10deg); /* 趣味动效 */
  box-shadow: 0 15px 35px -5px rgba(249, 115, 22, 0.6);
}

.badge {
  position: absolute;
  top: 0; right: 0;
  background-color: #ef4444;
  color: white;
  border-radius: 50%;
  width: 24px; height: 24px;
  font-size: 12px;
  font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid white;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

/* 侧边面板 */
.shopping-list-panel {
  position: fixed;
  top: 1.5rem; right: 1.5rem; bottom: 1.5rem;
  width: 280px;
  
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 24px;
  
  box-shadow: -10px 20px 50px -10px rgba(0,0,0,0.15);
  z-index: 1002;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  flex-shrink: 0;
  padding: 1.2rem 1.5rem;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255,255,255,0.4);
}

.panel-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #1e293b;
  font-weight: 600;
}

.close-panel-btn {
  background: rgba(0,0,0,0.05);
  border: none;
  width: 28px; height: 28px;
  border-radius: 50%;
  cursor: pointer;
  color: #64748b;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.close-panel-btn:hover {
  background: #ef4444;
  color: white;
}

/* 列表内容 */
.list-content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 1rem;
}

.list-content ul {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 0.5rem;
}

/* 列表项 */
.list-content li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 1rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.03);
  border: 1px solid rgba(0,0,0,0.02);
  font-size: 0.95rem;
  color: #334155;
  transition: all 0.2s;
}

.list-content li:hover {
  transform: translateX(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}

.remove-item-btn {
  background: transparent;
  border: none;
  color: #cbd5e1;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0 0.5rem;
}
.remove-item-btn:hover { color: #ef4444; }

.empty-state {
  text-align: center;
  color: #94a3b8;
  padding: 3rem 1rem;
  font-size: 0.9rem;
  opacity: 0.8;
}

/* 底部按钮 */
.panel-footer {
  flex-shrink: 0;
  padding: 1rem;
  background: rgba(255,255,255,0.4);
  border-top: 1px solid rgba(0,0,0,0.05);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.8rem;
}

.action-btn {
  padding: 0.7rem;
  border-radius: 10px;
  border: none;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn {
  background: var(--brand-color);
  color: white;
  box-shadow: 0 4px 10px rgba(249, 115, 22, 0.3);
}
.copy-btn:hover { background: var(--brand-color-dark); transform: translateY(-1px); }

.clear-btn {
  background: #f1f5f9;
  color: #64748b;
}
.clear-btn:hover { background: #e2e8f0; color: #334155; }

/* 动画 */
.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-fade-enter-from, .slide-fade-leave-to {
  transform: translateX(120%);
  opacity: 0;
}
</style>