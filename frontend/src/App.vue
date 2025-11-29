
<template>
  <div class="app-container">
    <TheBackground />
    <TheHero />
    <TheWorkbench />
    <TheSidebar />
    <UserAuth />
    <TheShoppingList />
    <RecipeModal 
      v-if="recipeModal.isVisible"
      :isLoading="recipeModal.isLoading"
      :recipes="recipeModal.recipes"
      :error="recipeModal.error"
      @close="recipeModal.hide"
    />
  </div>
</template>

<script setup>
import TheSidebar from './components/TheSidebar.vue';
import TheWorkbench from './components/TheWorkbench.vue';
import UserAuth from './components/UserAuth.vue';
import TheShoppingList from './components/TheShoppingList.vue';
import RecipeModal from './components/RecipeModal.vue';
import TheBackground from './components/TheBackground.vue';
import TheHero from './components/TheHero.vue'; 

import { useRecipeModalStore } from './stores/recipeModal';
const recipeModal = useRecipeModalStore();

</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
  --brand-color: #f97316;
  --brand-color-dark: #ea580c;
  --accent-color: #148061;
}

*, *::before, *::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: "Noto Sans SC", Inter, system-ui, sans-serif;
  background-color: transparent; 
  color: #1e293b;
}

.app-container {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
</style>