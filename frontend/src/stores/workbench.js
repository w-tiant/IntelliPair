
import { defineStore } from 'pinia'
import { ref } from 'vue'

let nextCardId = 0
let highestZIndex = 100

export const useWorkbenchStore = defineStore('workbench', () => {
  const cards = ref([])

  function createCard(type, payload = null) {
    const cardDefaults = {
        recommend: { title: '常规推荐', width: 600, height: 750 }, 
        alchemy: { title: '风味炼金术', width: 400, height: 680 },
        pathfinder: { title: '搭配探路者', width: 400, height: 600 },
        concept: { title: '菜谱概念', width: 450, height: 520 },
    }
    const defaults = cardDefaults[type] || { title: '新卡片', width: 300, height: 200 }

    highestZIndex++

    const newCard = {
      id: nextCardId++,
      type: type,
      title: defaults.title,
      x: window.innerWidth / 2 - defaults.width / 2 + (Math.random() - 0.5) * 50,
      y: window.innerHeight / 2 - defaults.height / 2 + (Math.random() - 0.5) * 50,
      width: defaults.width,
      height: defaults.height,
      zIndex: highestZIndex, // 新卡片最高的 z-index
      data: payload,
    }
    cards.value.push(newCard)
  }

  function deleteCard(cardId) {
    cards.value = cards.value.filter(card => card.id !== cardId)
  }

  // --- Action：将卡片带到最顶层 ---
  function bringToFront(cardId) {
    const card = cards.value.find(c => c.id === cardId)
    if (card && card.zIndex <= highestZIndex) {
      highestZIndex++
      card.zIndex = highestZIndex // 当前卡片的 z-index 设为最高
    }
  }

  return {
    cards,
    createCard,
    deleteCard,
    bringToFront,
  }
})