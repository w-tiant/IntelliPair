
import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useRecipeModalStore = defineStore('recipeModal', () => {
  // --- State ---
  const isVisible = ref(false);
  const isLoading = ref(false);
  const recipes = ref([]);
  const error = ref(null);

  // --- Actions ---

  // 1. 显示“加载中”状态
  function showLoading() {
    isVisible.value = true;
    isLoading.value = true;
    recipes.value = [];
    error.value = null;
  }

  // 2. 显示菜谱数据
  function showRecipes(recipeData) {
    recipes.value = recipeData;
    isLoading.value = false;
    error.value = null;
    isVisible.value = true;
  }

  // 3. 显示错误信息
  function showError(errorMessage) {
    error.value = errorMessage;
    isLoading.value = false;
    recipes.value = [];
    isVisible.value = true;
  }
  
  // 4. 关闭并重置模态框
  function hide() {
    isVisible.value = false;
    setTimeout(() => {
        isLoading.value = false;
        recipes.value = [];
        error.value = null;
    }, 300); // 300ms 对应CSS过渡时间
  }

  return {
    isVisible,
    isLoading,
    recipes,
    error,
    showLoading,
    showRecipes,
    showError,
    hide,
  };
});