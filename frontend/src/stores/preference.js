
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useUserStore } from './user'

export const usePreferenceStore = defineStore('preference', () => {
  const likedIngredients = ref(new Set());
  const likedCombinations = ref(new Set());
  const API_URL = '/api';

  // Action: 从后端同步用户的偏好数据
  async function syncPreferences() {
    const userStore = useUserStore();
    if (!userStore.currentUser) return;
  }

  // Action: 切换单个食材的点赞状态
  async function toggleIngredientLike(ingredientName) {
    const userStore = useUserStore();
    if (!userStore.currentUser) return;

    const wasLiked = likedIngredients.value.has(ingredientName);
    // 乐观更新 UI
    wasLiked ? likedIngredients.value.delete(ingredientName) : likedIngredients.value.add(ingredientName);

    try {
      const response = await fetch(`${API_URL}/users/${userStore.currentUser}/preferences?ingredient=${ingredientName}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('API request failed');
    } catch (e) {
      // 如果失败，回滚状态
      wasLiked ? likedIngredients.value.add(ingredientName) : likedIngredients.value.delete(ingredientName);
      alert('操作失败，请检查网络连接。');
    }
  }

  // Action: 切换组合的点赞状态
  async function toggleCombinationLike(combination_zh, combination_en) {
    const userStore = useUserStore();
    if (!userStore.currentUser || !combination_en) return;

    const signatureKey = [...combination_en].sort().join(',');
    const wasLiked = likedCombinations.value.has(signatureKey);
    // 乐观更新 UI
    wasLiked ? likedCombinations.value.delete(signatureKey) : likedCombinations.value.add(signatureKey);
    
    try {
      const response = await fetch(`${API_URL}/users/${userStore.currentUser}/combinations/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ combination: combination_zh })
      });
      if (!response.ok) throw new Error('API request failed');
    } catch (e) {
       wasLiked ? likedCombinations.value.add(signatureKey) : likedCombinations.value.delete(signatureKey);
      alert('操作失败，请检查网络连接。');
    }
  }

  return {
    likedIngredients,
    likedCombinations,
    syncPreferences,
    toggleIngredientLike,
    toggleCombinationLike,
  }
})