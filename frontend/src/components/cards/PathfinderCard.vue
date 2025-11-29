
<template>
  <div class="card-body">
    <!-- 表单区 -->
    <div class="form-section">
      <div class="input-row">
        <div class="input-group">
          <label>起点食材</label>
          <div class="search-wrapper">
            <input 
              type="text" 
              v-model="pathfinderStart" 
              placeholder="例如: 三文鱼" 
              @keyup.enter="findPath"
              @input="handleInputChange($event, 'pathStart')"
            />
            <ul v-if="suggestions.length > 0 && activeSuggestionBox === 'pathStart'" class="suggestions-list">
              <li v-for="s in suggestions" :key="s" @mousedown.prevent="handleSuggestionSelect(s, 'start', false)">{{ s }}</li>
            </ul>
          </div>
        </div>
        <div class="input-group">
          <label>终点食材</label>
          <div class="search-wrapper">
            <input 
              type="text" 
              v-model="pathfinderEnd" 
              placeholder="例如: 咖啡" 
              @keyup.enter="findPath"
              @input="handleInputChange($event, 'pathEnd')"
            />
            <ul v-if="suggestions.length > 0 && activeSuggestionBox === 'pathEnd'" class="suggestions-list">
              <li v-for="s in suggestions" :key="s" @mousedown.prevent="handleSuggestionSelect(s, 'end', false)">{{ s }}</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="input-group">
        <label>桥梁数量</label>
        <select v-model="pathfinderSteps">
          <option value="1">1个 (最直接)</option>
          <option value="2">2个 (更丰富)</option>
          <option value="3">3个 (最大胆)</option>
        </select>
      </div>

      <!-- 操作区 (移动到表单内部) -->
      <div class="action-bar">
        <button @click="findPath" :disabled="isLoading">
          <span v-if="isLoading" class="spinner"></span>
          {{ isLoading ? '正在探索...' : '探索路径' }}
        </button>
      </div>
    </div>

    <!-- 结果区 -->
    <div class="results-section">
      <!-- 简化了HTML结构：v-if 直接放在各自的元素上 -->
      <div v-if="error" class="error-panel">{{ error }}</div>
      
      <!-- v-if 直接放在容器上，并为它添加了 flex-grow: 1 -->
      <div v-if="results.length > 0" class="path-results-container">
        <div class="path-container">
          <template v-for="(item, index) in results" :key="item">
            <div class="path-node">
              {{ item }}
            </div>
            <div v-if="index < results.length - 1" class="path-connector"></div>
          </template>
        </div>
      </div>
      </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { useSuggestions } from '../../composables/useSuggestions'; // --- 引入Composable

// --- 探路者逻辑状态 ---
const pathfinderStart = ref('');
const pathfinderEnd = ref('');
const pathfinderSteps = ref(1);
const results = ref([]);
const isLoading = ref(false);
const error = ref(null);
const API_URL = '/api';

// --- 使用搜索建议Composable ---
const { suggestions, activeSuggestionBox, handleInputChange, selectSuggestion } = useSuggestions();

const inputModels = {
  start: pathfinderStart,
  end: pathfinderEnd,
};

function handleSuggestionSelect(suggestion, modelKey, isMulti) {
  const modelRef = inputModels[modelKey];
  if (modelRef) {
    selectSuggestion(suggestion, modelRef, isMulti);
  }
}

async function findPath() {
  if (!pathfinderStart.value || !pathfinderEnd.value) {
    error.value = '请输入起点和终点食材。';
    return;
  }
  isLoading.value = true;
  error.value = null;
  results.value = [];

  try {
    const params = new URLSearchParams({
      start: pathfinderStart.value,
      end: pathfinderEnd.value,
      steps: pathfinderSteps.value
    });
    const response = await fetch(`${API_URL}/find-bridge?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '服务器返回了错误。');
    results.value = data.path;
  } catch(e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
@import '../card-styles.css';

.input-row { display: flex; gap: 1rem; }
.input-row .input-group { flex: 1; }

/* 确保路径结果有自己的容器，以便未来扩展样式 */
.path-results-container {
  padding-top: 1rem;
}

/* --- 搜索建议相关样式 (与RecommendCard一致) --- */
.search-wrapper {
  position: relative;
}
.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5db;
  border-top: none;
  border-radius: 0 0 6px 6px;
  list-style: none;
  margin: 0;
  padding: 0.25rem 0;
  z-index: 10;
  max-height: 150px;
  overflow-y: auto;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}
.suggestions-list li {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-size: 0.875rem;
}
.suggestions-list li:hover {
  background-color: #f1f5f9;
}
</style>