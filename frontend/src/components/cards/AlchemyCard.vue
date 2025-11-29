
<template>
  <div class="card-body">
    <!-- 表单区 -->
    <div class="form-section">
      <div class="input-group">
        <label>基础食材</label>
        <div class="search-wrapper">
          <input 
            type="text" 
            v-model="alchemyBase" 
            placeholder="例如: 番茄" 
            @keyup.enter="performAlchemy"
            @input="handleInputChange($event, 'alchemyBase')"
          />
          <ul v-if="suggestions.length > 0 && activeSuggestionBox === 'alchemyBase'" class="suggestions-list">
            <li v-for="s in suggestions" :key="s" @mousedown.prevent="handleSuggestionSelect(s, 'base', false)">{{ s }}</li>
          </ul>
        </div>
      </div>
      <div class="input-group">
        <label>增加风味 <small>(可选, 逗号分隔)</small></label>
        <div class="search-wrapper">
          <input 
            type="text" 
            v-model="alchemyAdd" 
            placeholder="例如: 蘑菇, 土豆" 
            @keyup.enter="performAlchemy"
            @input="handleInputChange($event, 'alchemyAdd')"
          />
          <ul v-if="suggestions.length > 0 && activeSuggestionBox === 'alchemyAdd'" class="suggestions-list">
            <li v-for="s in suggestions" :key="s" @mousedown.prevent="handleSuggestionSelect(s, 'add', true)">{{ s }}</li>
          </ul>
        </div>
      </div>
      <div class="input-group">
        <label>减少风味 <small>(可选, 逗号分隔)</small></label>
        <div class="search-wrapper">
          <input 
            type="text" 
            v-model="alchemySubtract" 
            placeholder="例如: 柠檬" 
            @keyup.enter="performAlchemy"
            @input="handleInputChange($event, 'alchemySubtract')"
          />
          <ul v-if="suggestions.length > 0 && activeSuggestionBox === 'alchemySubtract'" class="suggestions-list">
            <li v-for="s in suggestions" :key="s" @mousedown.prevent="handleSuggestionSelect(s, 'subtract', true)">{{ s }}</li>
          </ul>
        </div>
      </div>

      <!-- 操作区 -->
      <div class="action-bar">
        <button @click="performAlchemy" :disabled="isLoading">
          <span v-if="isLoading" class="spinner"></span>
          {{ isLoading ? '正在计算...' : '开始炼金' }}
        </button>
      </div>
    </div>

    <!-- 结果区 -->
    <div class="results-section"> 
      <div v-if="error || results.length > 0">
        <div v-if="error" class="error-panel">{{ error }}</div>
        <div v-if="results.length > 0" class="recommend-list">
          <table>
            <thead>
                <tr>
                <th>结果</th>
                <th>相似度</th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="item in results" :key="item.ingredient">
                <td>{{ item.ingredient }}</td>
                <td>{{ parseFloat(item.score).toFixed(4) }}</td>
                </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useSuggestions } from '../../composables/useSuggestions'; // --- 引入Composable

// --- 炼金术逻辑状态 ---
const alchemyBase = ref('');
const alchemyAdd = ref('');
const alchemySubtract = ref('');
const results = ref([]);
const isLoading = ref(false);
const error = ref(null);
const API_URL = '/api';

const { suggestions, activeSuggestionBox, handleInputChange, selectSuggestion } = useSuggestions();

const inputModels = {
  base: alchemyBase,
  add: alchemyAdd,
  subtract: alchemySubtract,
};

function handleSuggestionSelect(suggestion, modelKey, isMulti) {
  const modelRef = inputModels[modelKey];
  if (modelRef) {
    selectSuggestion(suggestion, modelRef, isMulti);
  }
}

async function performAlchemy() {
  if (!alchemyBase.value) {
    error.value = '请输入基础食材。';
    return;
  }
  isLoading.value = true;
  error.value = null;
  results.value = [];

  try {
    const params = new URLSearchParams({
      base: alchemyBase.value,
      add: alchemyAdd.value,
      subtract: alchemySubtract.value
    });
    const response = await fetch(`${API_URL}/alchemy?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || '服务器返回了错误。');
    results.value = data.recommendations;
  } catch(e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
@import '../card-styles.css';

/* --- 搜索建议相关样式 --- */
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