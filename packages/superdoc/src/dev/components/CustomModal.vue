<script setup>
import { computed } from 'vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  message: {
    type: String,
    default: '',
  },
  type: {
    type: String, // 'success' | 'error' | 'info'
    default: 'info',
  },
});

const emit = defineEmits(['update:visible', 'close']);

const colors = computed(() => {
  switch (props.type) {
    case 'success':
      return {
        bg: '#d1fae5', // green-100
        text: '#065f46', // green-900
        icon: '#059669', // green-600
        btn: '#10b981', // green-500
        btnHover: '#059669', // green-600
      };
    case 'error':
      return {
        bg: '#fee2e2', // red-100
        text: '#991b1b', // red-900
        icon: '#dc2626', // red-600
        btn: '#ef4444', // red-500
        btnHover: '#dc2626', // red-600
      };
    default:
      return {
        bg: '#e0f2fe', // blue-100
        text: '#075985', // blue-900
        icon: '#0284c7', // blue-600
        btn: '#3b82f6', // blue-500
        btnHover: '#2563eb', // blue-600
      };
  }
});

const close = () => {
  emit('update:visible', false);
  emit('close');
};
</script>

<template>
  <Transition name="modal">
    <div v-if="visible" class="modal-overlay" @click.self="close">
      <div class="modal-container">
        <!-- Icon -->
        <div class="modal-header" :style="{ backgroundColor: colors.bg }">
          <div class="icon-wrapper" :style="{ backgroundColor: 'white' }">
             <!-- Success Check (Rosette Style) -->
            <svg v-if="type === 'success'" viewBox="0 0 512 512" class="icon" style="width: 100%; height: 100%;" xmlns="http://www.w3.org/2000/svg">
              <path fill="#22c55e" d="M256 0C114.6 0 0 114.6 0 256s114.6 256 256 256 256-114.6 256-256S397.4 0 256 0zm0 472c-119.3 0-216-96.7-216-216S136.7 40 256 40s216 96.7 216 216-96.7 216-216 216z" opacity="0"/>
              <!-- Rosette/Burst Shape approximation -->
              <path fill="#22c55e" d="M464 256c0-114.87-93.13-208-208-208S48 141.13 48 256s93.13 208 208 208 208-93.13 208-208z"/> 
              <!-- Checkmark -->
               <path fill="white" d="M372.3 154.3c-7.2-6.5-18.1-5.8-24.6 1.3L208.6 309.5l-68.3-61.7c-7.1-6.4-18-5.9-24.5 1.2s-5.9 18 1.2 24.5l82.6 74.6c3.4 3.1 7.8 4.7 12.3 4.6 4.5-.1 8.8-1.9 12-5.4L373.6 179c6.5-7.1 5.8-18-1.3-24.7z"/>
               <!-- Wavy edge detail (simplified as a stroke or second path if needed, but filled circle is good for 'flat' look. 
                   To match the 'wavy' look exactly without downloading, I'll stick to a smooth verified badge for now as it's cleaner than a bad hand-coded wavy path.
                   Actually, I can use a polygon for the wavy effect. -->
            </svg>
            <!-- Error X -->
            <svg v-else-if="type === 'error'" xmlns="http://www.w3.org/2000/svg" class="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor" :style="{ color: colors.icon }">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
             <!-- Info i -->
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor" :style="{ color: colors.icon }">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>

        <div class="modal-body">
          <h3 class="modal-title">{{ title }}</h3>
          <p class="modal-message">{{ message }}</p>
        </div>

        <div class="modal-footer">
          <button class="modal-btn" :style="{ backgroundColor: colors.btn }" @mouseover="e => e.target.style.backgroundColor = colors.btnHover" @mouseleave="e => e.target.style.backgroundColor = colors.btn" @click="close">
            OK
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.modal-container {
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  width: 90%;
  max-width: 400px;
  overflow: hidden;
  transform: scale(1);
  transition: all 0.3s ease;
}

.modal-header {
  height: 100px;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  position: absolute;
  bottom: -32px;
}

.icon {
  width: 32px;
  height: 32px;
}

.modal-body {
  padding: 48px 24px 24px;
  text-align: center;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.modal-message {
  font-size: 1rem;
  color: #4b5563;
  line-height: 1.5;
}

.modal-footer {
  padding: 0 24px 24px;
  display: flex;
  justify-content: center;
}

.modal-btn {
  width: 100%;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  outline: none;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.9);
}
</style>
