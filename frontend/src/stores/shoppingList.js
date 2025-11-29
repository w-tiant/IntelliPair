
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useShoppingListStore = defineStore('shoppingList', () => {
  // --- State ---
  const items = ref(new Set());
  const isPanelVisible = ref(false);

  // --- Getters ---
  const itemCount = computed(() => items.value.size);

  // --- Actions ---
  function addItem(ingredient) {
    if (ingredient && typeof ingredient === 'string' && ingredient.trim()) {
      items.value.add(ingredient.trim());
    }
  }

  function removeItem(ingredient) {
    items.value.delete(ingredient);
  }

  function clearList() {
    items.value.clear();
  }

  function togglePanel() {
    isPanelVisible.value = !isPanelVisible.value;
  }
  
  function showPanel() {
      isPanelVisible.value = true;
  }

  return {
    items,
    isPanelVisible,
    itemCount,
    addItem,
    removeItem,
    clearList,
    togglePanel,
    showPanel,
  };
});