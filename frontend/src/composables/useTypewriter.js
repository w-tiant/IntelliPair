import { ref, watch } from 'vue';

/**
 * @param {Ref<string>} fullTextRef - 完整的文本引用
 * @param {number} speed - 打字速度 (ms)
 * @param {Function} onComplete - 打字完成后的回调函数
 */
export function useTypewriter(fullTextRef, speed = 30, onComplete = null) {
  const displayedText = ref('');
  const isTyping = ref(false);

  watch(fullTextRef, (newText) => {
    if (!newText) {
        displayedText.value = '';
        isTyping.value = false;
        return;
    }
    
    // 初始化
    displayedText.value = '';
    isTyping.value = true;
    let currentIndex = 0;

    const interval = setInterval(() => {
      if (currentIndex < newText.length) {
        displayedText.value += newText.charAt(currentIndex);
        currentIndex++;
      } else {
        clearInterval(interval);
        isTyping.value = false;
        if (onComplete) {
            onComplete();
        }
      }
    }, speed);

  }, { immediate: true });

  return {
    displayedText,
    isTyping
  };
}