<template>
  <div class="card-body">
    <!-- 表单区 -->
    <div class="form-section">
      <!-- 锚点食材 -->
      <div class="input-group" :class="{ 'z-top': suggestions.length > 0 && activeSuggestionBox === 'ingredients' }">
        <label>锚点食材 <small>(用逗号分隔)</small></label>
        <div class="search-wrapper">
          <input 
            type="text" 
            v-model="ingredientsInput" 
            placeholder="例如: 牛肉, 番茄" 
            @keyup.enter="getRecommendations"
            @input="handleInputChange($event, 'ingredients')"
            @focus="handleFocus('ingredients')"
            @blur="handleBlur"
          />
          <ul v-if="suggestions.length > 0 && activeSuggestionBox === 'ingredients'" class="suggestions-list">
            <li v-for="s in suggestions" :key="s" @mousedown.prevent="onSelectSuggestion(s, 'ingredients')">
              {{ s }}
            </li>
          </ul>
        </div>
      </div>
      
      <!-- 排除食材 -->
      <div class="input-group" :class="{ 'z-top': suggestions.length > 0 && activeSuggestionBox === 'exclude' }">
        <label>排除食材 <small>(可选)</small></label>
        <div class="search-wrapper">
          <input 
            type="text" 
            v-model="excludedIngredientsInput" 
            placeholder="例如: 香菜" 
            @keyup.enter="getRecommendations"
            @input="handleInputChange($event, 'exclude')"
            @focus="handleFocus('exclude')"
            @blur="handleBlur"
          />
          <ul v-if="suggestions.length > 0 && activeSuggestionBox === 'exclude'" class="suggestions-list">
            <li v-for="s in suggestions" :key="s" @mousedown.prevent="onSelectSuggestion(s, 'exclude')">
              {{ s }}
            </li>
          </ul>
        </div>
      </div>
      
      <fieldset>
        <div class="mode-switcher">
        <button 
          class="mode-btn" 
          :class="{ 'is-active': mode === 'classic' }"
          @click="mode = 'classic'"
        >
          经典搭配
        </button>
        <button 
          class="mode-btn" 
          :class="{ 'is-active': mode === 'innovative' }"
          @click="mode = 'innovative'"
        >
          创新探索
        </button>
      </div>
      </fieldset>

      <!-- 操作区 -->
      <div class="action-bar">
        <button @click="getRecommendations" :disabled="isLoading">
          <span v-if="isLoading" class="spinner"></span>
          {{ isLoading ? '正在计算...' : '获取推荐' }}
        </button>
      </div>
    </div>

    <!-- 结果区 -->
    <div v-if="error || results.length > 0 || recipeIdea" class="results-section">
      <div v-if="error" class="error-panel">{{ error }}</div>
      
      <div v-if="recipeIdea" class="idea-card">
        <div class="pairing-story">
             <strong>💡 搭配灵感:</strong> {{ recipeIdea.pairing_story }}
        </div>
      </div>

      <div v-if="results.length > 0" class="recommend-list-container">
        <div 
            v-for="(item, index) in results" 
            :key="index" 
            class="result-capsule"
            :style="{ animationDelay: `${index * 0.05}s` }" 
        >
            <!-- 分数 -->
            <div class="score-indicator">
                <svg width="44" height="44" viewBox="0 0 44 44" class="progress-ring">
                    <!-- 背景轨道 (半透明) -->
                    <circle
                        class="progress-ring__circle--bg"
                        stroke="rgba(0,0,0,0.06)"
                        stroke-width="3"
                        fill="transparent"
                        r="18"
                        cx="22"
                        cy="22"
                    />
                    <!-- 进度条 (动态) -->
                    <circle
                        class="progress-ring__circle"
                        :stroke="getScoreColor(item.score)"
                        stroke-width="3"
                        stroke-linecap="round"
                        fill="transparent"
                        r="18"
                        cx="22"
                        cy="22"
                        :style="{ strokeDashoffset: calculateOffset(item.score), strokeDasharray: `${18 * 2 * Math.PI} ${18 * 2 * Math.PI}` }"
                    />
                    <!-- 中间文字 -->
                    <text x="22" y="22" class="progress-ring__text" dominant-baseline="central" text-anchor="middle">
                        {{ Math.round(item.score * 100) }}%
                    </text>
                </svg>
            </div>

            <!-- 食材标签组 -->
            <div class="ingredients-wrapper">
                
                <!-- 1. 经典模式 -->
                <template v-if="mode === 'classic' && item.combination">
                    <button 
                        v-for="ing in item.combination"
                        :key="ing"
                        class="ingredient-tag"
                        :class="{ 
                            'is-anchor': anchorIngredients.has(ing),
                            'in-cart': shoppingList.items.has(ing) 
                        }"
                        @click="toggleShoppingItem(ing)"
                        :title="shoppingList.items.has(ing) ? '从购物单移除' : '加入购物单'"
                    >
                        {{ ing }}
                        <!-- 核心修改：现在锚点食材也显示加号/勾勾 -->
                        <span class="tag-icon">
                            {{ shoppingList.items.has(ing) ? '✓' : '+' }}
                        </span>
                    </button>
                </template>

                <!-- 2. 创新模式 -->
                <template v-if="mode === 'innovative' && item.ingredient">
                    <!-- 推荐食材 (绿色系统) -->
                    <button 
                        class="ingredient-tag is-highlight"
                        :class="{ 'in-cart': shoppingList.items.has(item.ingredient) }"
                        @click="toggleShoppingItem(item.ingredient)"
                    >
                        {{ item.ingredient }}
                        <span class="tag-icon">{{ shoppingList.items.has(item.ingredient) ? '✓' : '+' }}</span>
                    </button>
                    
                    <!-- 锚点食材 (核心修改：现在变成了可点击的按钮，橙色系统) -->
                    <button 
                        v-for="anchor in Array.from(anchorIngredients)" 
                        :key="anchor" 
                        class="ingredient-tag is-anchor"
                        :class="{ 'in-cart': shoppingList.items.has(anchor) }"
                        @click="toggleShoppingItem(anchor)"
                        :title="shoppingList.items.has(anchor) ? '从购物单移除' : '加入购物单'"
                    >
                        {{ anchor }}
                        <span class="tag-icon">
                            {{ shoppingList.items.has(anchor) ? '✓' : '+' }}
                        </span>
                    </button>
                </template>
            </div>

            <!-- 按钮组 -->
            <div class="actions-group">
                <button 
                    @click="toggleLike(item)"
                    class="action-mini-btn like-btn"
                    :class="{ 'is-active': isLiked(item) }"
                    title="收藏"
                >
                    <svg viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                </button>

                <button 
                    @click="findRecipesForCard(item)"
                    class="action-mini-btn recipe-btn"
                    title="食谱"
                >
                    <svg viewBox="0 0 24 24"><path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/></svg>
                </button>
                
                 <button
                    @click="generateConceptForCard(item)" 
                    class="action-mini-btn ai-btn" 
                    title="概念"
                    :disabled="isLoadingConcept === (item.ingredient || (item.combination ? item.combination.join(',') : ''))"
                 >
                    <span v-if="isLoadingConcept === (item.ingredient || (item.combination ? item.combination.join(',') : ''))" class="spinner-tiny"></span>
                    <svg v-else viewBox="0 0 24 24"><path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z"/></svg>
                </button>
            </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useUserStore } from '../../stores/user';
import { usePreferenceStore } from '../../stores/preference';
import { useWorkbenchStore } from '../../stores/workbench';
import { useShoppingListStore } from '../../stores/shoppingList';
import { useRecipeModalStore } from '../../stores/recipeModal';
import { useSuggestions } from '../../composables/useSuggestions';

const user = useUserStore();
const prefs = usePreferenceStore();
const workbench = useWorkbenchStore();
const shoppingList = useShoppingListStore();
const recipeModal = useRecipeModalStore();
const { suggestions, activeSuggestionBox, handleInputChange, selectSuggestion: applySuggestion } = useSuggestions();

function onSelectSuggestion(suggestion, type) {
    const targetRef = type === 'ingredients' ? ingredientsInput : excludedIngredientsInput;
    applySuggestion(suggestion, targetRef, true);
}

// 状态
const ingredientsInput = ref('');
const excludedIngredientsInput = ref('');
const mode = ref('classic');
const results = ref([]);
const recipeIdea = ref(null);
const isLoading = ref(false);
const error = ref(null);
const isLoadingConcept = ref(null);
const API_URL = '/api';

const anchorIngredients = computed(() => 
  new Set(ingredientsInput.value.split(/,|，/).map(s => s.trim()).filter(s => s))
);

function handleFocus(source) { activeSuggestionBox.value = source; }
function handleBlur() { setTimeout(() => { suggestions.value = []; activeSuggestionBox.value = null; }, 200); }

// 1. 计算 SVG 圆环的偏移量
// r=18, 周长 = 2 * PI * 18 ≈ 113.097
const RADIUS = 18;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

function calculateOffset(score) {
    // score 是 0-1，offset 是剩余不显示的长度
    // 如果 score = 1, offset = 0 (全显示)
    // 如果 score = 0.4, offset = 周长 * (1 - 0.4)
    return CIRCUMFERENCE * (1 - score);
}

// 2. 修改颜色获取函数 (只返回颜色字符串)
function getScoreColor(score) {
    if (score > 0.8) return '#ef4444'; // 极高 - 红/深橙
    if (score > 0.6) return '#f97316'; // 高 - 品牌橙
    if (score > 0.4) return '#fbbf24'; // 中 - 黄
    return '#94a3b8'; // 低 - 灰
}

function toggleShoppingItem(ingredient) {
    if (shoppingList.items.has(ingredient)) {
        shoppingList.removeItem(ingredient);
    } else {
        shoppingList.addItem(ingredient);
        shoppingList.showPanel(); 
    }
}

// --- 核心修复：isLiked 逻辑 ---
function isLiked(item) {
    if (mode.value === 'innovative') {
        return prefs.likedIngredients.has(item.ingredient);
    } else if (item.combination) {
        // 修复：优先使用 combination_en (英文名) 来生成 key
        // 因为 store 内部也是用英文名来存储点赞状态的
        // 如果没有英文名（比如后备情况），才用中文名
        const source = item.combination_en || item.combination;
        const key = [...source].sort().join(',');
        
        return prefs.likedCombinations.has(key);
    }
    return false;
}

function toggleLike(item) {
    if (mode.value === 'innovative') {
        prefs.toggleIngredientLike(item.ingredient);
    } else if (item.combination) {
        const comboZh = item.combination;
        const comboEn = item.combination_en || item.combination; 
        prefs.toggleCombinationLike(comboZh, comboEn);
    }
}

function findRecipesForCard(item) {
    let searchItems = [];
    if (mode.value === 'innovative') {
        searchItems = [item.ingredient, ...Array.from(anchorIngredients.value)];
    } else {
        searchItems = item.combination;
    }
    
    recipeModal.showLoading();
    const params = new URLSearchParams();
    searchItems.forEach(ing => params.append('ingredients', ing));

    fetch(`${API_URL}/find-recipes?${params.toString()}`)
      .then(res => {
          if(!res.ok) throw new Error('API Error');
          return res.json();
      })
      .then(data => recipeModal.showRecipes(data))
      .catch(e => recipeModal.showError(e.message));
}

function generateConceptForCard(item) {
    let conceptItems = [];
    let key = '';
    
    if (mode.value === 'innovative') {
        conceptItems = [...Array.from(anchorIngredients.value), item.ingredient];
        key = item.ingredient;
    } else {
        conceptItems = item.combination;
        key = item.combination.join(',');
    }
    
    isLoadingConcept.value = key;
    
    fetch(`${API_URL}/generate-concept`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ combination: conceptItems })
    })
    .then(res => res.json())
    .then(data => {
        if(data.detail) throw new Error(data.detail);
        workbench.createCard('concept', data);
    })
    .catch(e => workbench.createCard('concept', { error: e.message }))
    .finally(() => { isLoadingConcept.value = null; });
}

async function getRecommendations() {
  if (!ingredientsInput.value.trim()) {
    error.value = '请输入至少一种食材。';
    return;
  }
  isLoading.value = true;
  error.value = null;
  results.value = [];
  recipeIdea.value = null;

  try {
    const params = new URLSearchParams({
      mode: mode.value,
      ingredients: ingredientsInput.value,
      exclude: excludedIngredientsInput.value,
    });
    if (user.currentUser) params.append('username', user.currentUser);
    
    const response = await fetch(`${API_URL}/recommend?${params.toString()}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail);

    if (mode.value === 'classic') {
        data.recommendations.forEach(rec => {
             if (!rec.combination_en) rec.combination_en = rec.combination;
        });
    }

    results.value = data.recommendations;
    
    // 同步用户的点赞状态到 store (确保刷新后红心还在)
    if (data.liked_ingredients) {
        prefs.likedIngredients = new Set(data.liked_ingredients);
    }
    if (data.liked_combinations) {
        prefs.likedCombinations = new Set(data.liked_combinations);
    }
    
    const coreIngredients = ingredientsInput.value.split(/,|，/).filter(s => s.trim());
    if (coreIngredients.length > 1) {
        const ideaParams = new URLSearchParams({ ingredients: ingredientsInput.value });
        fetch(`${API_URL}/generate-idea?${ideaParams.toString()}`)
            .then(r => r.json())
            .then(d => { if(d) recipeIdea.value = d; });
    }

  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}
</script>

<style scoped>
@import '../card-styles.css';

/* === 核心修复 1: 按钮颜色逻辑 === */

/* 基础小按钮 */
.action-mini-btn {
  width: 30px; height: 30px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  
  /* 修改：去掉 !important，允许被覆盖 */
  color: #475569; 
  
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 0;
}

/* 强制 SVG 填充当前颜色 */
.action-mini-btn svg {
  width: 20px; height: 20px;
  min-width: 20px;
  fill: currentColor; /* 关键：跟随文字颜色 */
  transition: fill 0.2s;
}

/* 悬停效果 */
.action-mini-btn:hover {
  background: rgba(255,255,255,0.9);
  transform: scale(1.15); /* 稍微放大一点 */
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* --- 点赞按钮的特定状态 --- */

/* 悬停时变粉红 */
.like-btn:hover {
  color: #f87171; 
}

/* 激活状态（点赞后）：强制变红 */
.like-btn.is-active {
  color: #ef4444 !important; /* 强制覆盖基础颜色 */
  opacity: 1 !important;
  transform: scale(1.1); /* 保持稍微放大的状态 */
}

/* 确保激活状态下的 SVG 也是红色的 */
.like-btn.is-active svg {
  fill: #ef4444 !important;
  filter: drop-shadow(0 2px 4px rgba(239, 68, 68, 0.3)); /* 加一点红色光晕 */
}

/* 其他按钮悬停色 */
.recipe-btn:hover { color: #3b82f6; }
.ai-btn:hover { color: #8b5cf6; }


/* === 核心修复 2: 锚点食材勾选样式 === */

/* 锚点食材默认 */
.ingredient-tag.is-anchor {
  background: transparent;
  color: #94a3b8;
  border: 1px dashed rgba(0,0,0,0.15);
  cursor: pointer;
}

/* 锚点食材被选中 (加入购物单)：橙色高亮 */
.ingredient-tag.is-anchor.in-cart {
  background: rgba(255, 237, 213, 0.95) !important; /* 不透明度高一点 */
  color: #c2410c !important;
  border-color: rgba(249, 115, 22, 0.5) !important;
  border-style: solid !important;
  box-shadow: 0 2px 5px rgba(249, 115, 22, 0.15);
}

/* 推荐食材被选中：保持绿色 */
.ingredient-tag.in-cart:not(.is-anchor) {
  background: rgba(220, 252, 231, 0.95);
  color: #15803d;
  border-color: rgba(34, 197, 94, 0.5);
}

/* --- 滑动切换器 (Segmented Control) --- */
.mode-switcher {
  display: flex;
  background: rgba(0, 0, 0, 0.05); /* 轨道背景：极淡灰 */
  padding: 4px;
  border-radius: 12px;
  margin-bottom: 1rem;
  position: relative;
  /* 内阴影，制造凹槽感 */
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.06);
}

.mode-btn {
  flex: 1;
  border: none;
  background: transparent;
  padding: 8px 0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  color: #64748b;
  font-weight: 600;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* 激活状态：变成白色悬浮块 */
.mode-btn.is-active {
  background: #fff;
  color: var(--brand-color);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1); /* 浮起阴影 */
  transform: scale(1.02);
}

.mode-btn .icon {
  font-size: 1.1em;
  filter: grayscale(1); /* 未选中时灰色 */
  transition: filter 0.3s;
}

.mode-btn.is-active .icon {
  filter: grayscale(0); /* 选中时彩色 */
}

.mode-btn:hover:not(.is-active) {
  color: #334155;
  background: rgba(255,255,255,0.5);
}

/* === 以下样式保持不变 === */

.input-group { position: relative; z-index: 1; margin-bottom: 8px; }
.input-group.z-top { z-index: 100 !important; }
.search-wrapper { position: relative; }

.suggestions-list {
  position: absolute; top: 100%; left: 0; right: 0;
  list-style: none; padding: 0; margin: 0;
  background: white; border: 1px solid rgba(0, 0, 0, 0.1);
  border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;
  max-height: 200px; overflow-y: auto; box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}
.suggestions-list li {
  padding: 10px 12px; cursor: pointer; font-size: 0.9rem; color: #334155; border-bottom: 1px solid #f1f5f9;
}
.suggestions-list li:hover { background-color: #f1f5f9; color: var(--brand-color); }

.actions-group { display: flex; gap: 0.25rem; margin-left: 0.5rem; opacity: 0.6; transition: opacity 0.2s; align-items: center; }
.result-capsule:hover .actions-group { opacity: 1; }

.recommend-list-container { display: flex; flex-direction: column; gap: 0.75rem; padding-bottom: 1rem; }
.result-capsule {
  display: flex; align-items: center; padding: 0.6rem 0.85rem;
  background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.5); border-radius: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: all 0.2s;
  opacity: 0; transform: translateY(10px); animation: slideIn 0.4s ease-out forwards;
}
.result-capsule:hover {
  background: rgba(255, 255, 255, 0.75); transform: translateY(-2px); box-shadow: 0 6px 16px rgba(0,0,0,0.05);
}

/* --- 左侧：分数环 (SVG) --- */
.score-indicator {
  width: 44px;
  flex-shrink: 0;
  margin-right: 0.8rem;
  display: flex;
  justify-content: center;
  align-items: center;
}

.progress-ring {
  transform: rotate(-90deg); /* 让进度从顶部开始 */
}

.progress-ring__circle {
  transition: stroke-dashoffset 0.5s ease-in-out;
  /* 给进度条加一点发光效果，增加质感 */
  filter: drop-shadow(0 0 2px rgba(0,0,0,0.1));
}

.progress-ring__text {
  font-size: 10px;
  font-weight: 700;
  fill: #475569; /* 文字颜色 */
  /* 文字不旋转，所以要把父级旋转抵消掉，或者不旋转父级 */
  transform: rotate(90deg); 
  transform-origin: center;
  font-family: 'Consolas', 'Monaco', monospace; /* 科技感字体 */
}

.ingredients-wrapper { flex-grow: 1; display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }
.ingredient-tag {
  display: inline-flex !important; align-items: center; gap: 4px;
  background: rgba(241, 245, 249, 0.6); border: 1px solid rgba(0,0,0,0.05);
  color: #475569; padding: 4px 10px; border-radius: 6px; font-size: 0.9rem;
  cursor: pointer; transition: all 0.2s;
}
.ingredient-tag:hover:not(.readonly) {
  background: white; transform: scale(1.05); box-shadow: 0 2px 5px rgba(0,0,0,0.05); color: var(--brand-color);
}
.ingredient-tag.is-highlight {
  background: rgba(255, 237, 213, 0.6); color: #c2410c; border-color: rgba(253, 186, 116, 0.3); font-weight: 600;
}
.tag-icon { font-size: 0.8em; opacity: 0.7; font-weight: bold; }
.spinner-tiny {
  width: 14px; height: 14px; border: 2px solid currentColor; border-top-color: transparent; border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes slideIn { to { opacity: 1; transform: translateY(0); } }
</style>