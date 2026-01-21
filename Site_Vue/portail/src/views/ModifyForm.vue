<template>
  <div class="form-page">
    <h2>Modifier un modèle / dataset</h2>

    <!-- Choix du type -->
    <div class="type-selection">
      <label>
        <input type="radio" value="models" v-model="selectedType" /> Modèle
      </label>
      <label>
        <input type="radio" value="datasets" v-model="selectedType" /> Dataset
      </label>
    </div>

    <!-- Sélecteur -->
    <div class="form-line">
      <label>Sélectionner {{ selectedType }} :</label>
      <select v-model="selectedItemId" @change="loadItem">
        <option v-for="item in filteredItems" :key="item.id" :value="item.id">
          {{ item.name }} : {{ item.uploaded_by }}
        </option>
      </select>
    </div>

    <!-- Détails -->
    <div v-if="itemData">
      <div class="form-line">
        <label>Nom :</label>
        <input type="text" v-model="itemData.name" />
      </div>

      <div class="form-line">
        <label>Uploader :</label>
        <input type="text" v-model="itemData.uploaded_by" />
      </div>

      <div class="form-line">
        <label>Date d'upload :</label>
        <input type="date" v-model="itemData.upload_date" />
      </div>

      <div class="form-line">
        <label>Description :</label>
        <textarea v-model="itemData.description"></textarea>
      </div>

      <div class="form-line">
        <label>Fichier :</label>
        <input type="file" @change="handleFileSelect" />
      </div>

      <div class="buttons-vertical">
        <button @click="updateItem">Mettre à jour</button>
        <button @click="$router.push('/')">Annuler</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      models: [],
      datasets: [],
      selectedType: "models", 
      selectedItemId: null,
      itemData: null,
      selectedFile: null,
    };
  },
  computed: {
    filteredItems() {
      return this.selectedType === "models" ? this.models : this.datasets;
    },
  },
  async mounted() {
    await this.fetchItems();
  },
  methods: {
    async fetchItems() {
      try {
        const [modelsRes, datasetsRes] = await Promise.all([
          fetch("http://localhost:8000/models"),
          fetch("http://localhost:8000/datasets"),
        ]);
        this.models = await modelsRes.json();
        this.datasets = await datasetsRes.json();

        if (this.filteredItems.length) {
          this.selectedItemId = this.filteredItems[0].id;
          this.loadItem();
        }
      } catch (err) {
        console.error("Erreur chargement :", err);
      }
    },
    loadItem() {
      this.itemData = this.filteredItems.find(
        (i) => i.id === this.selectedItemId
      );
    },
    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        this.selectedFile = file;
        console.log("Fichier sélectionné :", file.name);
      }
    },
    async updateItem() {
      if (!this.itemData) return alert("Aucun élément sélectionné");

      try {
        const formData = new FormData();
        formData.append("type_of_upload", this.selectedType);
        formData.append("id", this.itemData.id);
        formData.append("file_name", this.itemData.name);
        formData.append("uploaded_by", this.itemData.uploaded_by);
        formData.append("upload_date", this.itemData.upload_date);
        formData.append("description", this.itemData.description || "");
        formData.append("selectedFile", this.selectedFile ? "true" : "false");

        if (this.selectedFile) formData.append("file", this.selectedFile);

        const res = await fetch("http://localhost:8000/update", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error("Erreur serveur");

        alert("Mise à jour réussie !");
        this.$router.push("/");
      } catch (err) {
        console.error("Erreur update :", err);
        alert("Erreur lors de la mise à jour");
      }
    },
  },
  watch: {
    selectedType() {
      if (this.filteredItems.length) {
        this.selectedItemId = this.filteredItems[0].id;
        this.loadItem();
      } else {
        this.selectedItemId = null;
        this.itemData = null;
      }
    },
  },
};
</script>

<style scoped>
/* ---- Conteneur principal ---- */
.form-page {
  max-width: 800px;
  margin: 30px auto;
  padding: 25px;
  background-color: #ffffff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  font-family: Arial, sans-serif;
}

/* ---- Titre ---- */
h2 {
  color: #1a237e;
  text-align: center;
  margin-bottom: 25px;
}

/* ---- Type selection ---- */
.type-selection {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 25px;
}

.type-selection label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: bold;
}

/* ---- Champs ---- */
.form-line {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

label {
  font-weight: bold;
  margin-bottom: 6px;
}

input,
textarea,
select,
input[type="file"] {
  padding: 10px;
  font-size: 1em;
  border: 1px solid #ccc;
  border-radius: 6px;
  background-color: #fafafa;
}

textarea {
  resize: vertical;
  min-height: 100px;
}

/* ---- Boutons verticaux ---- */
.buttons-vertical {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 30px;
}

button {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  transition: 0.2s;
}

/* Bouton Update */
button:first-child {
  background-color: #1a237e;
  color: white;
}

button:first-child:hover {
  background-color: #303f9f;
}

/* Bouton Cancel */
button:last-child {
  background-color: #b0bec5;
  color: black;
}

button:last-child:hover {
  background-color: #78909c;
}
</style>
