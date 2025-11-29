<template>
  <vue-particles
    id="tsparticles"
    :particlesInit="particlesInit"
    :options="options"
  />
</template>

<script setup>
import { loadSlim } from "tsparticles-slim";

const particlesInit = async (engine) => {
  await loadSlim(engine);
};
const options = {
  style: {
    position: "absolute",
    zIndex: -1,
  },
  background: {
    color: {
      value: "#ffffff",
    },
  },
  fpsLimit: 60,
  interactivity: {
    events: {
      onHover: {
        enable: true,
        mode: "grab",
      },
      onClick: {
        enable: true,
        mode: "push",
      },
      resize: true,
    },
    modes: {
      grab: {
        distance: 180,
        links: {
          opacity: 0.8,
          color: "#f97316" // 鼠标抓取时，线条变橙色
        },
      },
      push: {
        quantity: 2,
      },
    },
  },
  particles: {
    color: {
      value: ["#0ea5e9", "#6366f1", "#8b5cf6"]
    },
    links: {
      enable: true,
      distance: 150,
      color: "#cbd5e1", // 默认连线使用浅灰
      opacity: 0.4,
      width: 1,
      triangles: {
        enable: true,
        color: "#c3ffee",
        opacity: 0.07,
      },
    },
    move: {
      enable: true,
      speed: 1.5,
      direction: "none",
      random: false,
      straight: false,
      outModes: {
        default: "bounce",
      },
    },
    number: {
      density: {
        enable: true,
        area: 800,
      },
      value: 40, // 数量适中
    },
    opacity: {
      value: 0.5,
      animation: {
        enable: true,
        speed: 1,
        minimumValue: 0.1,
        sync: false
      }
    },
    shape: {
      type: "circle",
    },
    size: {
      value: { min: 1, max: 3 },
    },
  },
  detectRetina: true,
};
</script>

<style scoped>
</style>