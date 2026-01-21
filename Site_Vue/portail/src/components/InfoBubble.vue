<template>
  <div class="info-bubble-container">
    <span class="info-icon" @click="togglePopup">
      (i)
    </span>

    <div v-if="isVisible" class="info-popup">
      <div class="popup-header">
        <span class="popup-title">{{ title }}</span>
        <button class="close-btn" @click="isVisible = false">×</button>
      </div>
      <div class="popup-content">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'InfoBubble',
  props: {
    // Titre de la pop-up
    title: {
      type: String,
      default: 'Information'
    }
  },
  data() {
    return {
      isVisible: false
    };
  },
  methods: {
    togglePopup() {
      this.isVisible = !this.isVisible;
    }
  }
};
</script>

<style scoped>
/* --- STYLES DU COMPOSANT INFO-BULLE --- */

.info-bubble-container {
  display: inline-block;
  position: relative;
  /* Assure que l'info-bulle flotte au-dessus */
  z-index: 1000; 
}

.info-icon {
  cursor: pointer;
  color: #334C9E; /* Bleu Principal */
  font-weight: bold;
  font-size: 0.9em;
  border: 1px solid #334C9E;
  border-radius: 50%;
  padding: 0px 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1; /* Aligne le texte */
  transition: background-color 0.2s;
  user-select: none;
}

.info-icon:hover {
  background-color: #5C7CDB; /* Bleu d'Accent */
  color: white;
}

/* --- POPUP (FENÊTRE CONTEXTUELLE) --- */
.info-popup {
  position: absolute;
  /* Positionne la pop-up à droite du (i) */
  top: 0;
  left: 100%;
  margin-left: 10px;
  
  width: 300px;
  max-width: 80vw;
  background-color: white;
  border: 1px solid #5C7CDB; /* Bleu d'Accent */
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  padding: 10px;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 5px;
  margin-bottom: 5px;
}

.popup-title {
  font-weight: bold;
  color: #334C9E; /* Bleu Principal */
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2em;
  cursor: pointer;
  color: #333;
  line-height: 1;
  padding: 0;
}
</style>