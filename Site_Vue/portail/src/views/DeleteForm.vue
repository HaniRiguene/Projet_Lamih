<template>
  <div class="form-page">
    <h2>Supprimer un modèle / dataset</h2>

    <!-- Choix type -->
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

    <!-- Informations -->
    <div v-if="itemData" class="info-box">
      <p><strong>Nom :</strong> {{ itemData.name }}</p>
      <p><strong>Uploader :</strong> {{ itemData.uploaded_by }}</p>
      <p><strong>Date d'upload :</strong> {{ itemData.upload_date }}</p>
      <p><strong>Description :</strong> {{ itemData.description }}</p>
      <p><strong>Chemin :</strong> {{ itemData.path }}</p>
    </div>

    <!-- Boutons -->
    <div class="buttons-vertical">
      <button @click="deleteItem" :disabled="!itemData">Supprimer</button>
      <button @click="$router.push('/')">Annuler</button>
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
      itemData: null
    };
  },
  computed: {
    filteredItems() {
      return this.selectedType === "models" ? this.models : this.datasets;
    }
  },
  async mounted() {
    await this.fetchItems();
  },
  methods: {
    async fetchItems() {
      const [modelsRes, datasetsRes] = await Promise.all([
        fetch("http://localhost:8000/models"),
        fetch("http://localhost:8000/datasets")
      ]);

      this.models = await modelsRes.json();
      this.datasets = await datasetsRes.json();

      if (this.filteredItems.length) {
        this.selectedItemId = this.filteredItems[0].id;
        this.loadItem();
      }
    },
    loadItem() {
      this.itemData = this.filteredItems.find(
        (i) => i.id === this.selectedItemId
      );
    },
    async deleteItem() {
      if (!this.itemData) return;

      if (!confirm(`Voulez-vous vraiment supprimer "${this.itemData.name}" ?`))
        return;

      const payload = {
        type: this.selectedType,
        id: this.selectedItemId.toString()
      };

      try {
        const res = await fetch("http://localhost:8000/delete", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Erreur suppression");

        alert("Supprimé avec succès !");
        this.$router.push("/");
      } catch (err) {
        console.error(err);
        alert("Erreur lors de la suppression");
      }
    }
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
    }
  }
};
</script>

<style scoped>
/* ---- Conteneur ---- */
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
  text-align: center;
  color: #1a237e;
  margin-bottom: 25px;
}

/* ---- Type Selection ---- */
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

/* ---- Lignes de formulaire ---- */
.form-line {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

label {
  font-weight: bold;
  margin-bottom: 6px;
}

select {
  padding: 10px;
  font-size: 1em;
  background-color: #fafafa;
  border-radius: 6px;
  border: 1px solid #ccc;
}

/* ---- Boîte d'infos ---- */
.info-box {
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 6px;
  margin: 20px 0;
  line-height: 1.6;
}

/* ---- Boutons ---- */
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

/* Delete */
button:first-child {
  background-color: #b71c1c;
  color: white;
}

button:first-child:hover {
  background-color: #d32f2f;
}

/* Cancel */
button:last-child {
  background-color: #b0bec5;
  color: black;
}

button:last-child:hover {
  background-color: #78909c;
}

/* Disabled */
button:disabled {
  background-color: #ccc;
  color: #666;
  cursor: not-allowed;
}
</style>
