<template>
  <div id="main-page" class="app-container">
    
    <nav class="nav">
      <button @click="$router.push('/add')">ADD</button>
      <button @click="$router.push('/modify')">MODIFY</button>
      <button @click="$router.push('/delete')">DELETE</button>
    </nav>

    <div class="content-wrapper">
      <div class="config-panel">
        
        <h2>1. Select your model</h2>
        <div class="form-group">
          <select v-model="selectedModel">
            <option disabled value="">Select a model</option>
            <option v-for="model in models" :key="model.id" :value="model.id">
              {{ model.name }} : {{ model.uploaded_by }}
            </option>
          </select>
        </div>
        
        <h2>2. Select the hubs you want to use</h2>
        <table class="hubs-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Info</th>
              <th>Selection</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="hub in filteredHubs" :key="hub.id"> 
              <td>{{ hub.name }}</td>
              <td>{{ hub.type }}</td>
              <td>Stockage : {{ hub.stockage }} GO</td>
              <td><input type="checkbox" v-model="hub.selected" :disabled="!canStartProgram" /></td>
            </tr>
            
            <tr v-if="hubs.length === 0">
              <td colspan="4"> No hubs connected </td>
            </tr>
            </tbody>
        </table>

        <h2>3. Select the execution mode and configure</h2>
        <div class="mode-selector">
            <button :class="{ active: selectedMode === 'FL' }" @click="selectedMode = 'FL'">FL</button>
            <button :class="{ active: selectedMode === 'ML' }" @click="selectedMode = 'ML'">ML</button>
            <button :class="{ active: selectedMode === 'MA' }" @click="selectedMode = 'MA'">MA</button>
        </div>

        <div class="parameters-details">
          <h3> Parameter for {{selectedMode}}</h3>
          
          <div v-if="selectedMode === 'FL' || selectedMode === 'ML'">
            <div>
              <p class="mode-description" v-if="selectedMode === 'FL'">
                Application for Federated Learning with weight management (Initialization & Aggregation).
              </p> 
              <p class="mode-description" v-if="selectedMode === 'ML'">
                Application for Model Learning, that make the model interact with a dataset.
              </p> 
            </div>
            
            <div class="separator"></div> 
            
            <div class="config-item">
              <label> Number of turn</label>
              <input v-model.number="numberOfTurn" type="number" min="1"></input>
            </div>
            
            <div class="separator"></div> 

            <div class="config-item checkbox-group">
              <label>
                <input type="checkbox" v-model="isDifferentTurns" />
                <strong>Configuration per turn </strong>
              </label>
              <p class="helper-text"> Enable each turn to be different, with different datasets or constraints.</p>
            </div>
            
            <div class="separator"></div> 

            <div v-if="!isDifferentTurns">
              <h4 class="sub-section"> Dataset Operation</h4>
              <div class="radio-group">
                <label>
                  <input type="radio" value="classic" v-model="DatasetDecoupage" />
                  Classic mode 
                </label>
                <label>
                  <input type="radio" value="class" v-model="DatasetDecoupage" />
                  Class mode
                </label>
              </div>
              
              <div class="config-item" v-if="DatasetDecoupage=='classic'">
                <label> Number of parts wanted : </label>
                <input v-model.number="NumberOfParts" type="number" min="1" />
              </div>
            </div>
            
            <div class="form-group" v-if="!isDifferentTurns">
              <label for="dataset-select"> <strong> Dataset : </strong></label>
              <select id="dataset-select" v-model="selectedDataset">
                <option disabled value="">Select a dataset</option>
                <option v-for="dataset in datasets" :key="dataset.id" :value="dataset.id">
                  {{ dataset.name }} : {{ dataset.uploaded_by }}
                </option>
              </select>
              <p v-if="!selectedDataset" class="error-text">Veuillez sélectionner un dataset.</p>
            </div>
            <div class="config-item" v-else>
                <label>Dataset utilisé :</label>
                <p class="info-text">(Sélectionné par tour dans la modal de configuration)</p>
            </div>
          </div>
          <div v-else-if="selectedMode==='MA'">
          <p class="mode-description">
            Application for Model application, that can execute a model on all chosen hubs.
          </p> 
              <div class="config-item">
              <label> Number of turn</label>
              <input v-model.number="numberOfTurn" type="number" min="1"></input>
            </div>
      </div>
        </div>


        <div class="action-buttons">
          <button class="start-button"
            @click="startOrContinue"
            :disabled="!isReadyToStart"> 
            {{ isDifferentTurns && selectedMode !== 'MA' ? 'CONFIGURER LES TOURS' : 'START' }}
          </button>
        </div>
      </div>
      
      <div class="log-panel">
        <div class="log-controls">
          <button @click="goBackFiveMinutes">-5 min</button>
          <button @click="AddFiveMinutes">+5 min</button>
        </div>
        <div class="log-window">
          <div v-for="(msg,index) in logs" :key="index" class="log-line">{{ msg }}</div>
        </div>
      </div>
    </div>

    <TurnConfigModal
        v-if="showTurnConfigModal"
        :mode="selectedMode"
        :model-id="selectedModel"
        :initial-dataset-id="selectedDataset"
        :selected-hubs="filteredHubs.filter(h => h.selected)"
        :number-of-turn="numberOfTurn"
        :all-datasets="datasets"
        @turn-config-finished="executeStartMultiTurn"
        @exit="showTurnConfigModal = false"
    />

    <div v-for="hub in popupHubs" :key="hub.id">
      <HubPopup
        :hub="hub"
        :columns="csvColumns"
        @validated="popupValidated"
        @exit="closeHubPopup"
      />
    </div>

  </div>
</template>

<script>
import HubPopup from "@/components/HubPopup.vue"; 
import TurnConfigModal from "@/components/TurnConfigModal.vue"; 
import InfoBubble from "@/components/InfoBubble.vue";

export default {
  name: 'MainPage',
  components: { HubPopup, TurnConfigModal, InfoBubble }, 
  data() {
    return {
      hubs: [],
      models: [],
      datasets: [],
      filteredHubs: [], 
      
      selectedModel: "",
      selectedDataset: "",
      selectedMode: 'FL', 
      
      numberOfTurn: 2, 
      isDifferentTurns: false, 
      
      DatasetDecoupage: 'classic',
      NumberOfParts: 2, 

      csvColumns: [],
      popupHubs: [],
      arrayResultPopUp: [], 
      pendingPopups: 0,
      showTurnConfigModal: false,
      
      isHubsLoading: true, 
      canStartProgram: false, 
      refreshInterval: null,
      logStartTime: new Date(),
      logs: [],
    };
  },
  computed: {
    onlineHubs() {
        return this.filteredHubs;
    },
    isReadyToStart() {
      const modelSelected = !!this.selectedModel;
      const hubsSelectedAndReady = this.filteredHubs.filter(h => h.selected).length > 0 && this.canStartProgram; 
      const turnValid = this.numberOfTurn >= 1;
      
      // Dataset est obligatoire SAUF si Multi-Turn est activé ou mode MA
      const datasetSelected = this.isDifferentTurns || this.selectedMode === 'MA' ? true : !!this.selectedDataset;
      
      // La vérification des parties n'est nécessaire que si le découpage est classique et NON multi-tour
      const partsValid = (this.isDifferentTurns || this.selectedMode === 'MA') ? true : 
                         (this.DatasetDecoupage === 'classic' ? this.NumberOfParts >= 1 : true);
      
      return modelSelected && datasetSelected && hubsSelectedAndReady && turnValid && partsValid;
    },
  },
  methods: {
    startOrContinue() {
      if (!this.isReadyToStart) return;

      if (this.isDifferentTurns && this.selectedMode !== 'MA') {
        this.showTurnConfigModal = true; 
      } else {
        // Déclenche l'action en fonction du découpage
        if (this.DatasetDecoupage === 'classic' || this.selectedMode === 'MA') {
          this.executeStart(false); 
        } else {
          // Découpage par classe -> déclenche l'appel read-csv et les popups
          this.triggerClassPopups(); 
        }
      }
    },

    executeStart(selectionByClass) {
        const selectedHubs = this.onlineHubs.filter(h => h.selected);
        const numTurns = parseInt(this.numberOfTurn);
        
        const datasetIds = Array(numTurns).fill(this.selectedDataset==="" ? 0: this.selectedDataset);
        const selectionByClassList = Array(numTurns).fill(selectionByClass);
        const numberOfPartsList = Array(numTurns).fill(this.DatasetDecoupage === 'classic' ? this.NumberOfParts : null);

        const rulesListForBackend = selectionByClass ? 
                                    this.arrayResultPopUp.map(r => [r.hub, r.column, r.word, r.number]) : 
                                    [];
        
        const payload = {
            modelId: parseInt(this.selectedModel),
            datasetId: datasetIds, 
            hubs: selectedHubs, 
            selectionByClass: selectionByClassList, 
            rulesList: rulesListForBackend, 
            NumberOfParts: numberOfPartsList,
            parameter: "Language:Python",
            modeOfExecution:this.selectedMode,
            numberOfTurn: numTurns,
        };
        
        this.executeLaunch(payload); 
    },

    executeStartMultiTurn(turnConfigs) {
        const numTurns = parseInt(this.numberOfTurn);
        
        const datasetIds = turnConfigs.map(c => c.datasetId);
        const selectionByClassList = turnConfigs.map(c => c.selectionByClass);
        const numberOfPartsList = turnConfigs.map(c => c.NumberOfParts);
        
        const rulesListForPayload = turnConfigs.map(config => {
            if (!config.selectionByClass) {
                return [];
            }
            
            const turnRules = config.rulesList.map(rule => {
                return [rule.hubName, rule.column, rule.word, rule.number];
            });
            
            return turnRules;
        });

        const selectedHubs = this.onlineHubs.filter(h => h.selected);

        const payload = {
            modelId: parseInt(this.selectedModel),
            datasetId: datasetIds, 
            hubs: selectedHubs, 
            selectionByClass: selectionByClassList, 
            rulesList: rulesListForPayload, 
            NumberOfParts: numberOfPartsList, 
            parameter: "Language:Python",
            modeOfExecution:this.selectedMode,
            numberOfTurn: numTurns,
        };
        
        this.showTurnConfigModal = false;
        this.executeLaunch(payload);
    },

    executeLaunch(payload) {
        console.log("--- PAYLOAD ENVOYÉ (JSON Stringifié) ---");
        console.log(JSON.stringify(payload, null, 2));

        fetch("http://localhost:8000/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (res.ok) alert(`Démarrage du programme en mode ${this.selectedMode} réussi pour ${this.numberOfTurn} tour(s)!`);
            else res.json().then(data => alert("Erreur de démarrage: " + (data.detail || res.statusText)));
        })
        .catch(err => alert("Erreur envoi start: " + err));
    },

    // --- LOGIQUE DE DÉCOUPAGE PAR CLASSE (CORRIGÉE pour envoyer le path) ---
    async triggerClassPopups() {
        if (!this.selectedDataset) {
            alert("Veuillez sélectionner un dataset avant de configurer le découpage par classe.");
            return;
        }

        const selectedDatasetObj = this.datasets.find(d => d.id === this.selectedDataset);
        
        if (!selectedDatasetObj || !selectedDatasetObj.path) {
            alert("Erreur: Impossible de trouver le chemin du dataset sélectionné dans la liste des datasets (Vérifiez si la propriété 'path' est disponible).");
            return;
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
            return;
          }
        } catch(e) {
          alert("Erreur communication backend lors de la lecture CSV (Réseau/CORS). Détail: " + e.message);
          return;
        }

        this.arrayResultPopUp = [];
        this.popupHubs = this.onlineHubs.filter(h => h.selected);
        this.pendingPopups = this.popupHubs.length;
        
        if (this.pendingPopups > 0) {
            console.log(`Déclenchement de ${this.pendingPopups} popups de configuration...`);
        } else {
             alert("Veuillez sélectionner au moins un hub en ligne pour configurer le découpage par classe.");
        }
    },
    popupValidated(result) {
      for (const rule of result.rules) {
        this.arrayResultPopUp.push({
          hub: result.hub.name, 
          column: rule.column,
          word: rule.word,
          number: rule.number
        });
      }
      this.popupHubs = this.popupHubs.filter(h => h.id !== result.hub.id);
      this.pendingPopups--;

      if (this.pendingPopups === 0) {
        this.executeStart(true); 
      }
    },
    closeHubPopup() {
      this.popupHubs = [];
      this.csvColumns = [];
    },

    async fetchHubs() {
      try {
        const res = await fetch("http://localhost:8000/hubs");
        if (!res.ok) throw new Error("Erreur HTTP " + res.status);
        const newHubs = await res.json();
        
        const updatedHubs = [];
        newHubs.forEach(newHub => {
          const existingHub = this.hubs.find(h => h.id === newHub.id);
          if (existingHub) {
            const selectedState = existingHub.selected || false; 
            Object.assign(existingHub, newHub); 
            existingHub.selected = selectedState; 
            updatedHubs.push(existingHub);
          } else {
            updatedHubs.push({ ...newHub, selected: false });
          }
        });
        this.hubs = updatedHubs;
        
        this.filteredHubs = this.hubs.filter(hub => hub.status?.toLowerCase() === "online");

        this.canStartProgram = this.hubs.every(hub => 
            hub.status?.toLowerCase() === "online" || hub.status?.toLowerCase() === "offline"
        );
        
      } catch (err) {
        console.error("Erreur récupération hubs:", err);
        this.hubs = []; 
        this.filteredHubs = [];
        this.canStartProgram = false;
      } finally {
        this.isHubsLoading = false; 
      }
    },
    
    async fetchModels() {
      try {
        const res = await fetch("http://localhost:8000/models");
        if (!res.ok) throw new Error("Erreur HTTP " + res.status);
        this.models = await res.json();
      } catch { this.models = []; }
    },
    async fetchDatasets() {
      try {
        const res = await fetch("http://localhost:8000/datasets");
        if (!res.ok) throw new Error("Erreur HTTP " + res.status);
        this.datasets = await res.json();
      } catch { this.datasets = []; }
    },
    async fetchLogs() {
      try {
        const res = await fetch("http://localhost:8000/logs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ from_timestamp: this.logStartTime })
        });
        if (!res.ok) return;
        const data = await res.json();
        this.logs = data.map(
          l => `[${new Date(l.timestamp).toLocaleString()}] ${l.hub_name}: ${l.logs}`
        );
      } catch {}
    },
goBackFiveMinutes() {
  const d = new Date(this.logStartTime);
  d.setMinutes(d.getMinutes() - 5);
  // Correction : toISOString() envoie la date au format UTC (ex: 2025-12-08T12:00:00.000Z)
  this.logStartTime = d.toISOString();
},
AddFiveMinutes(){
  const d = new Date(this.logStartTime);
  d.setMinutes(d.getMinutes() + 5);
  // Correction : toISOString() envoie la date au format UTC
  this.logStartTime = d.toISOString();
},
  },
  mounted() {
    this.fetchHubs();
    this.fetchModels();
    this.fetchDatasets();
    this.refreshInterval = setInterval(this.fetchHubs, 1000);
    setInterval(this.fetchLogs, 1000);
  },
  beforeUnmount() {
    if (this.refreshInterval) clearInterval(this.refreshInterval);
  }
};
</script>

<style scoped>
/* COULEURS MISES À JOUR:
   Nouveau Bleu Principal (entre les deux) : #334C9E
   Nouveau Bleu d'Accent (entre les deux) : #5C7CDB
   Gris très clair (select/table) : #F7F7F7
   Vert (START) : #4caf50
   Fond clair : #f4f7f9
   Texte foncé : #333
   Bordure : #ccc
*/

/* --- STRUCTURE GÉNÉRALE --- */
.app-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #333;
}

.content-wrapper {
  display: flex;
  gap: 20px;
  padding: 20px;
}

/* --- PANELS (Panneaux de configuration et Logs) --- */
.config-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px; 
  min-width: 50%;
}

.log-panel {
  flex: 0 0 45%;
  display: flex;
  flex-direction: column;
}

/* --- NAVIGATION (.nav) --- */
.nav {
  display: flex;
  width: 100%;
  height: 60px;
  background-color: #334C9E; /* Nouveau Bleu Principal */
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.nav button {
  flex: 1;
  border: none;
  background-color: transparent;
  color: white;
  font-weight: bold;
  font-size: 1em;
  cursor: pointer;
  transition: background 0.2s;
}
.nav button:not(:last-child) {
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}
.nav button:hover {
  background-color: #5C7CDB; /* Nouveau Bleu d'Accent */
}

/* --- TITRES --- */
h2 {
    color: #334C9E; /* Nouveau Bleu Principal */
    margin: 5px 0 8px 0;
    border-bottom: 2px solid #5C7CDB; /* Nouveau Bleu d'Accent */
    padding-bottom: 5px;
    font-size: 1.4em;
    font-weight: 600;
}
h3 {
    color: #5C7CDB; /* Nouveau Bleu d'Accent */
    margin-top: 0;
    border-bottom: 1px dashed #ccc;
    padding-bottom: 5px;
    margin-bottom: 10px;
    font-size: 1.2em;
}
h4.sub-section {
    color: #334C9E; /* Nouveau Bleu Principal */
    font-size: 1em;
    font-weight: bold;
    margin-top: 15px;
    margin-bottom: 5px;
}

/* --- FORMULAIRES & INPUTS --- */
.form-group {
    margin-bottom: 15px;
}
.config-item {
    margin-bottom: 10px;
}

/* SELECTS (Models/Datasets) - NOUVEAU GRIS CLAIR */
select {
  width: 100%;
  padding: 10px 12px;
  font-size: 1em;
  background-color: #F7F7F7; /* Gris très clair */
  color: #333;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  appearance: none; 
  /* Centrage du texte dans le select */
  text-align: center; 
  text-align-last: center; 
}
select option {
    text-align: left;
}

.config-item label, .form-group label {
    display: flex;
    align-items: center;
    gap: 5px;
    margin-top: 5px;
}

.config-item input[type="number"] {
    width: 80px;
    padding: 4px;
    border: 1px solid #ccc;
    border-radius: 3px;
    margin-left: 5px;
}

.radio-group {
  display: flex;
  gap: 20px;
  margin: 10px 0;
}

.error-text {
    color: #d9534f;
    font-size: 0.9em;
    margin-top: 5px;
}
.info-text {
    color: #5C7CDB; /* Nouveau Bleu d'Accent */
    font-size: 0.9em;
    margin-top: 5px;
}
.helper-text, .mode-description {
    font-size: 0.9em;
    color: #666;
    margin-top: 5px;
}

/* --- BARRE DE SÉPARATION --- */
.separator {
    height: 1px;
    background-color: #5C7CDB; /* Nouveau Bleu d'Accent */
    margin: 15px 0;
    opacity: 0.5;
}

/* --- TABLE DES HUBS --- */
.hubs-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #F7F7F7; /* Gris très clair pour le fond de table */
  color: #000;
  border-radius: 6px;
  overflow: hidden;
}
.hubs-table th {
  background-color: #5C7CDB; /* Nouveau Bleu d'Accent */
  color: white;
  padding: 10px;
  /* Centrage du titre du tableau */
  text-align: center; 
  font-weight: 600;
}
.hubs-table td {
  border: 1px solid #e0e0e0;
  padding: 8px;
  text-align: left;
}
.hubs-table tr:nth-child(even) {
    background-color: #eef1f3;
}

/* --- SÉLECTION DES MODES (FL/ML/MA) --- */
.mode-selector {
    display: flex;
    gap: 10px;
    margin-bottom: 10px;
}
.mode-selector button {
    flex: 1;
    padding: 12px;
    border: 1px solid #ccc;
    background-color: white;
    cursor: pointer;
    font-weight: bold;
    border-radius: 5px;
    transition: all 0.2s;
    color: #333;
}
.mode-selector button.active {
    background-color: #334C9E; /* Nouveau Bleu Principal */
    color: white;
    border-color: #334C9E;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

/* --- DÉTAILS DE LA CONFIGURATION (.parameters-details) --- */
.parameters-details {
    border: 1px solid #5C7CDB; /* Nouveau Bleu d'Accent */
    border-radius: 8px;
    padding: 20px;
    background-color: #f4f7f9; /* Fond clair */
}

/* --- BOUTONS D'ACTION --- */
.action-buttons {
    margin-top: 10px;
}

.start-button {
  width: 100%;
  background-color: #4caf50; /* Vert */
  color: white;
  font-size: 1.3em;
  padding: 14px 20px;
  border: none;
  cursor: pointer;
  border-radius: 5px;
  font-weight: bold;
  transition: background-color 0.2s;
}
.start-button:hover:not(:disabled) {
    background-color: #449d48;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}
.start-button:disabled {
  background-color: #b0b0b0;
  cursor: not-allowed;
}

/* --- LOGS --- */
.log-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 5px;
}
.log-controls button {
  padding: 8px 12px;
  border: 1px solid #ccc;
  background-color: white;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
  color: #333;
}
.log-controls button:hover {
    background-color: #eef1f3;
}
.log-window {
  flex-grow: 1;
  height: 50vh;
  background-color: #263238;
  color: #c0c6c9; 
  padding: 15px;
  overflow-y: auto;
  border-radius: 6px;
  font-family: 'Consolas', 'Courier New', monospace;
  border: 1px solid #1a1a1a;
}
.log-line {
  margin: 2px 0;
  white-space: pre-wrap;
  font-size: 0.9em;
}
</style>