<template>
  <div class="modal-overlay" @click.self="$emit('exit')">
    <div class="modal-content">
      <header>
        <h2>Configuration des Tours (Mode {{ mode }})</h2>
        <button @click="$emit('exit')" class="close-btn">×</button>
      </header>
      
      <div v-if="!popupsActive" class="config-body">
        <div class="turn-list">
          <div 
            v-for="(turn, index) in turnConfigs" 
            :key="index" 
            :class="['turn-item', { 'active': currentTurnIndex === index }]"
            @click="currentTurnIndex = index">
            Tour {{ index + 1 }}
          </div>
        </div>

        <div class="turn-details">
          <h3>Configuration du Tour {{ currentTurnIndex + 1 }}</h3>
          
          <div class="config-section">
            <label for="dataset-select">Dataset utilisé :</label>
            <select 
              id="dataset-select" 
              v-model="currentTurn.datasetId" 
              @change="resetDecoupage(currentTurn)"
              class="full-width-select">
              <option disabled value="">Sélectionner un dataset</option>
              <option v-for="dataset in allDatasets" :key="dataset.id" :value="dataset.id">
                {{ dataset.name }}
              </option>
            </select>
          </div>

          <h4 class="sub-section">Options de Découpage</h4>
          <div class="selection-mode">
            <label>
              <input type="radio" value="classic" v-model="currentTurn.decoupageType" @change="resetDecoupage(currentTurn)" />
              Découpage classique
            </label>
            <label>
              <input type="radio" value="class" v-model="currentTurn.decoupageType" @change="resetDecoupage(currentTurn)" />
              Découpage par classe
            </label>
          </div>

          <div v-if="currentTurn.decoupageType === 'classic'" class="config-section">
            <label> Nombre de parties : </label>
            <input v-model.number="currentTurn.NumberOfParts" type="number" min="1" />
          </div>
          
          <div v-if="currentTurn.decoupageType === 'class'" class="config-section">
            <p v-if="currentTurn.rulesList.length > 0" style="color: green;">
                ✅ Découpage par classe configuré pour {{ currentTurn.rulesList.length }} règles.
            </p>
            <p v-else style="color: orange;">
                ⚠️ Découpage par classe non configuré. Appuyez sur 'Suivant' pour configurer.
            </p>
          </div>

          <div class="navigation-buttons">
            <button @click="prevTurn" :disabled="currentTurnIndex === 0">Précédent</button>
            
            <button 
              @click="nextTurn" 
              :disabled="!isTurnValid(currentTurn)" 
              class="main-action">
              {{ isLastTurn ? 'TERMINER' : 'SUIVANT' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="popupsActive" class="popup-section">
        <h3>Configuration par Classe (Tour {{ currentTurnIndex + 1 }})</h3>
        <p>Veuillez configurer les règles de découpage pour chaque Hub sélectionné.</p>
        
        <div v-for="hub in popupHubs" :key="hub.id">
            <HubPopup
                :hub="hub"
                :columns="csvColumns"
                @validated="popupValidated"
                @exit="closeHubPopup"
            />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import HubPopup from "./HubPopup.vue";

export default {
  name: "TurnConfigModal",
  components: { HubPopup },
  props: {
    mode: String,
    modelId: [Number, String],
    selectedHubs: Array,
    numberOfTurn: [Number, String],
    allDatasets: Array,
    initialDatasetId: [Number, String],
  },
  data() {
    const numTurns = parseInt(this.numberOfTurn);
    let turnConfigs = [];

    for (let i = 0; i < numTurns; i++) {
      turnConfigs.push({
        datasetId: this.initialDatasetId,
        decoupageType: 'classic',
        NumberOfParts: 2,
        selectionByClass: false,
        rulesList: [], // Stocke les résultats validés
        columns: [], // Colonnes récupérées via /read-csv
      });
    }

    return {
      turnConfigs: turnConfigs,
      currentTurnIndex: 0,
      
      // États pour les Pop-ups
      csvColumns: [],
      popupHubs: [],
      pendingPopups: 0,
      popupsActive: false,
    };
  },
  computed: {
    currentTurn() {
      return this.turnConfigs[this.currentTurnIndex];
    },
    isLastTurn() {
      return this.currentTurnIndex === this.turnConfigs.length - 1;
    },
    // Vérifie si la configuration minimale du tour est complète
    isTurnValid() {
      return (turn) => {
        if (!turn.datasetId) return false;
        if (turn.decoupageType === 'classic' && turn.NumberOfParts < 1) return false;
        
        // En mode classe, on ne bloque pas avant le lancement des popups
        return true; 
      };
    },
  },
  methods: {
    resetDecoupage(turn) {
        if (turn.decoupageType === 'classic') {
            turn.NumberOfParts = 2;
            turn.selectionByClass = false;
            turn.rulesList = [];
        } else { // 'class'
            turn.NumberOfParts = null;
            turn.selectionByClass = true;
            // On conserve rulesList si déjà configuré, sinon il est vide
        }
    },
    
    async nextTurn() {
        if (!this.isTurnValid(this.currentTurn)) return;

        // 1. Gérer la configuration par classe avant d'aller au tour suivant / terminer
        if (this.currentTurn.decoupageType === 'class' && this.currentTurn.rulesList.length === 0) {
            
            // Tente de déclencher les pop-ups
            const success = await this.triggerClassPopupsForCurrentTurn();
            if (!success) {
                // Si l'appel API a échoué ou aucun hub sélectionné, on reste sur ce tour
                return; 
            }
            // Si les pop-ups sont lancées, l'exécution s'arrête ici, la suite se fera dans popupValidated

        } else {
            // 2. Si Découpage Classique ou Découpage par Classe déjà configuré (rulesList > 0)
            
            if (this.isLastTurn) {
                // Terminer la configuration et émettre l'événement
                this.$emit('turn-config-finished', this.turnConfigs);
            } else {
                // Aller au tour suivant
                this.currentTurnIndex++;
            }
        }
    },
    
    prevTurn() {
      if (this.currentTurnIndex > 0) {
        this.currentTurnIndex--;
      }
    },

    // --- Logique Pop-up / read-csv ---

    async triggerClassPopupsForCurrentTurn() {
        this.currentTurn.rulesList = []; // Reset les règles existantes

        const selectedDatasetObj = this.allDatasets.find(d => d.id === this.currentTurn.datasetId);
        
        if (!selectedDatasetObj || !selectedDatasetObj.path) {
            alert("Erreur: Le chemin du dataset sélectionné est introuvable.");
            return false;
        }

        const datasetPathToSend = selectedDatasetObj.path;
        
        let columns = [];
        try {
          const res = await fetch("http://localhost:8000/read-csv", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ path: datasetPathToSend }) 
          });
          
          const data = await res.json();
          if (res.ok) {
            columns = data.columns;
            this.csvColumns = columns;
          } else {
            alert(`Erreur lecture CSV (Backend ${res.status}): ` + (data.detail || res.statusText));
            return false;
          }
        } catch(e) {
          alert("Erreur communication backend lors de la lecture CSV (Réseau/CORS). Détail: " + e.message);
          return false;
        }
        
        // Si la lecture CSV réussit, on active les pop-ups
        this.popupHubs = this.selectedHubs;
        this.pendingPopups = this.popupHubs.length;
        this.popupsActive = true; 
        
        if (this.pendingPopups === 0) {
             alert("Veuillez sélectionner au moins un hub en ligne pour configurer le découpage par classe.");
             this.popupsActive = false;
             return false;
        }

        return true;
    },

    popupValidated(result) {
      // 1. Stocker les règles dans le tour actuel
      for (const rule of result.rules) {
        this.currentTurn.rulesList.push({
          hubName: result.hub.name, 
          column: rule.column,
          word: rule.word,
          number: rule.number
        });
      }
      
      // 2. Gérer le flux des pop-ups
      this.pendingPopups--;
      if (this.pendingPopups === 0) {
        this.popupsActive = false;
        this.closeHubPopup(); 
        
        // 3. Continuer le flux après la configuration des pop-ups
        if (this.isLastTurn) {
            this.$emit('turn-config-finished', this.turnConfigs);
        } else {
            this.currentTurnIndex++;
        }
      }
    },
    
    closeHubPopup() {
      this.popupHubs = [];
      this.csvColumns = [];
    },
  },
};
</script>

<style scoped>
/* Collez vos styles ici */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 1000px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}
header {
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
header h2 {
    margin: 0;
    color: #1a237e;
}
.close-btn {
  background: none;
  border: none;
  font-size: 1.5em;
  cursor: pointer;
  color: #aaa;
}
.config-body {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
  height: 60vh;
}
.turn-list {
  flex: 0 0 150px;
  background-color: #f4f4f4;
  border-right: 1px solid #ddd;
  overflow-y: auto;
}
.turn-item {
  padding: 15px;
  cursor: pointer;
  border-bottom: 1px solid #e0e0e0;
  font-weight: bold;
  transition: background-color 0.2s;
}
.turn-item:hover {
  background-color: #e9e9e9;
}
.turn-item.active {
  background-color: #ff9800;
  color: white;
  border-left: 4px solid #1a237e;
}
.turn-details {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
.config-section {
    margin-bottom: 15px;
}
.full-width-select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.selection-mode {
  display: flex;
  gap: 20px;
  margin: 10px 0;
}
.sub-section {
    color: #3949ab;
    font-size: 1em;
    font-weight: bold;
    margin-top: 15px;
    margin-bottom: 5px;
}
.navigation-buttons {
    display: flex;
    justify-content: space-between;
    padding-top: 20px;
    border-top: 1px solid #eee;
    margin-top: 20px;
}
.navigation-buttons button {
    padding: 10px 15px;
    border: none;
    cursor: pointer;
    border-radius: 4px;
}
.navigation-buttons button:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}
.main-action {
    background-color: #4CAF50;
    color: white;
}
.popup-section {
    padding: 20px;
    max-height: 80vh;
    overflow-y: auto;
}
</style>