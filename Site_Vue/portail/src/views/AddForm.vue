<template>
  <div class="form-page">
    <h1>Ajouter un Modèle, un Dataset ou un Hub</h1>
    
    <div class="type-selection">
      <label>
        <input type="radio" value="model" v-model="type" /> Modèle
      </label>
      <label>
        <input type="radio" value="dataset" v-model="type" /> Dataset
      </label>
      <label>
        <input type="radio" value="hub" v-model="type" /> Hub
      </label>
    </div>

    <form @submit.prevent="submitForm">
      
      <div v-if="type === 'model' || type === 'dataset'">
        <div class="form-line">
          <label>Nom :</label>
          <input v-model="form.file_name" required maxlength="50" />
        </div>

        <div class="form-line">
          <label>Uploader :</label>
          <input v-model="form.uploaded_by" required maxlength="30" />
        </div>

        <div class="form-line">
          <label>Description :</label>
          <textarea v-model="form.description"></textarea>
        </div>

        <div class="form-line">
          <label>Fichier :</label>
          <input type="file" @change="handleFileSelect" required />
        </div>
      </div>

      <div v-if="type === 'hub'">
        <div class="form-line">
          <label>Adresse MAC :</label>
          <input v-model="form.mac_address" 
                 placeholder="Ex: 00:1A:2B:3C:4D:5E"
                 required />
        </div>
        
        <div class="form-line">
          <label>Type de Hub :</label>
          <input v-model="form.type_hub" placeholder="jetson/raspberry" required/>
        </div>
      </div>
      
      <div class="buttons-vertical">
        <button type="submit">Ajouter</button>
        <button type="button" @click="$router.push('/')">Annuler</button>
      </div>
    </form>

    <div v-if="message" class="message-box">{{ message }}</div>
  </div>
</template>

---

<script>
export default {
  data() {
    return {
      type: "model",
      form: {
        // Champs Modèle/Dataset
        file_name: "",
        uploaded_by: "",
        description: "",
        path: "",
        file: null,

        // Champs Hub
        mac_address: "",
        type_hub: "", // Initialisation du champ type_hub
      },
      message: "",
    };
  },
  methods: {
    handleFileSelect(event) {
      const file = event.target.files[0];
      if (file) {
        this.form.file = file;
        this.form.path = file.name;
        console.log("Fichier sélectionné :", this.form.path);
      }
    },
    
    // --- Logique de soumission principale ---
    async submitForm() {
      this.message = "";
      let res;
      const API_URL = 'http://localhost:8000';
      
      try {
        if (this.type === 'model' || this.type === 'dataset') {
          
          // 1. UPLOAD DE FICHIER (Méthode POST /upload)
          const formData = new FormData();
          formData.append("type_of_upload", this.type === "model" ? "models" : "datasets");
          formData.append("file", this.form.file);
          formData.append("file_name", this.form.file_name);
          formData.append("uploaded_by", this.form.uploaded_by);
          formData.append("description", this.form.description || "");
          
          res = await fetch(`${API_URL}/upload`, {
            method: "POST",
            body: formData,
          });

        } else if (this.type === 'hub') {
          
          // 2. CRÉATION DE HUB (Méthode POST /hub)
          const hubFormData = new FormData();
          hubFormData.append("mac_address", this.form.mac_address);
          hubFormData.append("type", this.form.type_hub); // 'type' est le nom attendu par l'API
          
          res = await fetch(`${API_URL}/hub`, {
            method: "POST",
            body: hubFormData,
          });
        } else {
          return; 
        }

        // --- Gestion des Réponses (CORRIGÉE) ---
        // Tenter de lire la réponse JSON. Utiliser .catch pour gérer les réponses non-JSON (erreurs serveur, etc.)
        const responseData = await res.json().catch(() => null); 

        if (!res.ok) {
          // Si le statut est une erreur (4xx, 5xx), afficher le détail de l'erreur du serveur
          const detail = responseData ? responseData.detail : "Erreur inconnue du serveur.";
          throw new Error(detail);
        }
        
        // Si le statut est 2xx (Succès)
        if (this.type === 'hub') {
            // Utilisation sécurisée de responseData.name pour éviter l'erreur "can't access property of null"
            const hubName = responseData && responseData.name ? responseData.name : 'ajouté';
            this.message = `Hub ${hubName} ajouté avec succès !`;
            this.form.mac_address = ''; // Réinitialiser le champ
            this.form.type_hub = ''; // Réinitialiser le type de hub
        } else {
            this.message = "Ajout réussi !";
            this.form.file_name = ''; // Réinitialiser le nom du fichier/modèle
            this.form.uploaded_by = ''; // Réinitialiser l'uploader
        }
        
        setTimeout(() => this.$router.push("/"), 2000);
        
      } catch (err) {
        this.message = "Erreur lors de l'ajout : " + err.message;
        console.error("Erreur soumission :", err);
      }
    },
  },
};
</script>

---

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
h1 {
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
select { /* Ajout de 'select' */
  padding: 10px;
  font-size: 1em;
  border: 1px solid #ccc;
  border-radius: 6px;
  background-color: #fafafa;
}

input[type="file"] {
    border: none;
    padding: 0;
    background-color: transparent;
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

/* Bouton Ajouter */
button[type="submit"] {
  background-color: #1a237e;
  color: white;
}

button[type="submit"]:hover {
  background-color: #303f9f;
}

/* Bouton Annuler */
button[type="button"] {
  background-color: #b0bec5;
  color: black;
}

button[type="button"]:hover {
  background-color: #78909c;
}

/* ---- Message ---- */
.message-box {
  margin-top: 20px;
  padding: 10px 15px;
  border-radius: 6px;
  font-weight: bold;
  background: #e8eaf6;
  color: #1a237e;
  border-left: 4px solid #1a237e;
  text-align: center;
}
</style>