<template>
  <div class="card-body concept-container">
    
    <!-- 错误状态 -->
    <div v-if="cardData && cardData.error" class="error-panel">
      <div class="error-icon">⚠️</div>
      <div class="error-content">
        <strong>生成中断</strong>
        <p>{{ cardData.error }}</p>
      </div>
    </div>

    <!-- 正常内容 -->
    <div v-if="cardData && !cardData.error" class="concept-content">
      
      <!-- 1. 头部 -->
      <header class="concept-header">
        <div class="ai-badge">AI CHEF GEN.</div>
        <h3 class="dish-title">{{ cardData.dish_name }}</h3>
        <div class="divider"></div>
      </header>
      
      <!-- 2. 描述 -->
      <div class="description-box">
        <span class="quote-mark">“</span>
        <p class="description-text">
          {{ displayedDescription }}
          <span v-if="isDescTyping" class="cursor-block"></span>
        </p>
        <span class="quote-mark end">”</span>
      </div>
      
      <!-- 3. 关键步骤 -->
      <div v-if="startShowingSteps" class="steps-container">
        <h4 class="section-label">EXECUTION STEPS</h4>
        <div class="steps-list">
          <div 
            v-for="(step, index) in displayedSteps" 
            :key="index" 
            class="step-card"
            :class="{ 'is-active': currentStepIndex === index }"
          >
            <div class="step-number">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="step-text">
              {{ step }}
              <span v-if="currentStepIndex === index && isStepsTyping" class="cursor-line">|</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. 风味亮点 -->
      <div v-if="showFlavorTags" class="flavor-section">
        <h4 class="section-label">FLAVOR PROFILE</h4>
        <div class="flavor-grid">
          <div 
            v-for="(profile, index) in flavorList" 
            :key="profile" 
            class="flavor-chip"
            :style="{ animationDelay: `${index * 0.1}s` }"
          >
            <span class="chip-icon">●</span>
            {{ profile.trim() }}
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, toRef, watch, computed } from 'vue';
import { useTypewriter } from '../../composables/useTypewriter';

const props = defineProps({
  cardData: Object, 
});

// --- 1. 描述打字机 ---
const descriptionRef = toRef(() => props.cardData?.description || '');
const { displayedText: displayedDescription, isTyping: isDescTyping } = useTypewriter(
    descriptionRef, 
    30, 
    startSteps 
);

// --- 2. 步骤打字机逻辑 ---
const fullSteps = computed(() => props.cardData?.key_steps || []);
const displayedSteps = ref([]); 
const startShowingSteps = ref(false); 
const currentStepIndex = ref(0); 
const isStepsTyping = ref(false);
const showFlavorTags = ref(false); 

function startSteps() {
  if (fullSteps.value.length === 0) {
      showFlavorTags.value = true; 
      return;
  }
  startShowingSteps.value = true;
  isStepsTyping.value = true;
  typeNextStep(0);
}

function typeNextStep(index) {
  if (index >= fullSteps.value.length) {
    isStepsTyping.value = false;
    showFlavorTags.value = true; 
    return;
  }

  currentStepIndex.value = index;
  const textToType = fullSteps.value[index];
  let charIndex = 0;
  displayedSteps.value[index] = ''; 

  const interval = setInterval(() => {
    if (charIndex < textToType.length) {
      displayedSteps.value[index] += textToType.charAt(charIndex);
      charIndex++;
    } else {
      clearInterval(interval);
      setTimeout(() => {
        typeNextStep(index + 1);
      }, 100);
    }
  }, 15); // 打字速度加快
}

watch(() => props.cardData, () => {
    displayedSteps.value = [];
    startShowingSteps.value = false;
    showFlavorTags.value = false;
    currentStepIndex.value = 0;
});

// --- 3. 风味标签 ---
const flavorList = computed(() => {
    if (!props.cardData?.flavor_profile) return [];
    return props.cardData.flavor_profile.split(/,|，/);
});
</script>

<style scoped>
.concept-container {
  padding: 0;
  height: 100%;
  overflow-y: auto;
  /* 隐约的网格背景图 */
  background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
  background-size: 20px 20px;
  background-position: 0 0;
}

.concept-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* --- 1. 头部样式 --- */
.concept-header {
  text-align: center;
  position: relative;
}

.ai-badge {
  display: inline-block;
  font-size: 0.6rem;
  letter-spacing: 2px;
  font-weight: 800;
  color: var(--brand-color);
  border: 1px solid var(--brand-color);
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  opacity: 0.7;
}

.dish-title {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 800;
  line-height: 1.2;
  /* 渐变文字 */
  background: linear-gradient(135deg, #1e293b 0%, #475569 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.1), transparent);
  margin-top: 1rem;
  width: 100%;
}

/* --- 2. 描述区 --- */
.description-box {
  position: relative;
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.8);
  padding: 1.2rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.03);
  backdrop-filter: blur(4px);
}

.quote-mark {
  position: absolute;
  font-size: 3rem;
  color: rgba(var(--brand-color-rgb, 249, 115, 22), 0.2);
  font-family: serif;
  line-height: 1;
}
.quote-mark { top: -10px; left: 10px; }
.quote-mark.end { bottom: -20px; right: 10px; transform: rotate(180deg); }

.description-text {
  margin: 0;
  font-size: 1rem;
  line-height: 1.6;
  color: #334155;
  font-style: italic;
  min-height: 3em;
}

/* 方块光标 */
.cursor-block {
  display: inline-block;
  width: 8px;
  height: 1em;
  background-color: var(--brand-color);
  vertical-align: text-bottom;
  animation: blink 1s step-end infinite;
}

/* --- 通用标签 --- */
.section-label {
  font-size: 0.7rem;
  letter-spacing: 1px;
  color: #94a3b8;
  font-weight: 700;
  margin: 0 0 0.8rem 0;
  text-transform: uppercase;
}

/* --- 3. 步骤区 --- */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.step-card {
  display: flex;
  gap: 1rem;
  padding: 0.8rem;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 10px;
  transition: all 0.3s;
}

/* 当前正在打印的步骤高亮 */
.step-card.is-active {
  background: rgba(255, 255, 255, 0.8);
  border-color: var(--brand-color);
  box-shadow: 0 4px 12px rgba(249, 115, 22, 0.1);
  transform: translateX(5px);
}

.step-number {
  font-family: 'Monaco', monospace;
  font-size: 1.2rem;
  font-weight: 700;
  color: rgba(0,0,0,0.15);
  line-height: 1;
}
.step-card.is-active .step-number { color: var(--brand-color); }

.step-text {
  font-size: 0.95rem;
  color: #475569;
  line-height: 1.5;
}

.cursor-line {
  border-right: 2px solid var(--brand-color);
  margin-left: 2px;
  animation: blink 1s step-end infinite;
}

/* --- 4. 风味区 --- */
.flavor-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.flavor-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(16, 185, 129, 0.1);
  color: #047857;
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  
  opacity: 0;
  transform: scale(0.8);
  animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}

.chip-icon { font-size: 0.6rem; color: #10b981; }

/* --- 错误面板 --- */
.error-panel {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  margin: 2rem;
  background: rgba(254, 226, 226, 0.5);
  border: 1px solid #fecaca;
  border-radius: 12px;
  color: #b91c1c;
}
.error-icon { font-size: 2rem; }

/* 动画 */
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes popIn { to { opacity: 1; transform: scale(1); } }
</style>