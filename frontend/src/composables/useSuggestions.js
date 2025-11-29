
import { ref } from 'vue';

const API_URL = '/api';

export function useSuggestions() {
  // State
  const suggestions = ref([]);
  const activeSuggestionBox = ref(null); // 跟踪哪个输入框是激活的
  let debounceTimer = null;

  // Action
  function handleInputChange(event, source) {
    clearTimeout(debounceTimer);
    activeSuggestionBox.value = source; // 标记当前输入框
    const fullInput = event.target.value;
    const currentWord = fullInput.split(/,|，/).pop().trim();

    if (!currentWord) {
      suggestions.value = [];
      return;
    }

    // 防抖：延迟300ms
    debounceTimer = setTimeout(async () => {
      try {
        const response = await fetch(`${API_URL}/search-suggestions?q=${currentWord}`);
        if (!response.ok) return;
        const data = await response.json();
        suggestions.value = data.suggestions;
      } catch (e) {
        console.error("搜索建议获取失败:", e);
        suggestions.value = [];
      }
    }, 300);
  }

  // Action: 当用户点击一个建议时
  function selectSuggestion(suggestion, currentModelRef, isMultiInput = true) {
    if (isMultiInput) {
      const parts = currentModelRef.value.split(/,|，/);
      parts[parts.length - 1] = suggestion;
      currentModelRef.value = parts.join(', ') + ', ';
    } else {
      // 对于单个输入
      currentModelRef.value = suggestion;
    }
    
    suggestions.value = [];
    activeSuggestionBox.value = null;
  }

  return {
    suggestions,
    activeSuggestionBox,
    handleInputChange,
    selectSuggestion,
  };
}