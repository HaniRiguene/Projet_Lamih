<template>
  <div class="overlay">
    <div class="hub-popup">
      <h3>{{ hub.name }}</h3>

      <table>
        <thead>
          <tr>
            <th>Category</th>
            <th>Word</th>
            <th>Number (0–1)</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(rule, index) in rules" :key="index">
            <td>
              <select v-model="rule.column">
                <option disabled value="">Select...</option>
                <option v-for="col in columns" :key="col" :value="col">
                  {{ col }}
                </option>
              </select>
            </td>
            <td><input type="text" v-model="rule.word" /></td>
            <td><input type="number" min="0" max="1" step="0.01" v-model.number="rule.number" /></td>
            <td>
              <button
                @click="removeRow(index)"
                :disabled="rules.length === 1"
                title="Remove"
              >
                ➖
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="buttons">
        <button class="add-btn" @click="addRow">➕ Add line</button>
        <div class="action-buttons">
          <button @click="validate">Validate</button>
          <button @click="$emit('exit')">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    hub: { type: Object, required: true },
    columns: { type: Array, required: true }
  },
  data() {
    return {
      // juste rename "category" -> "column"
      rules: [{ column: "", word: "", number: 0 }]
    };
  },
  methods: {
    addRow() {
      this.rules.push({ column: "", word: "", number: 0 });
    },
    removeRow(index) {
      if (this.rules.length > 1) this.rules.splice(index, 1);
    },
    validate() {
      const first = this.rules[0];
      if (!first.column || first.word.trim() === "") {
        alert("Please fill the first line before validating.");
        return;
      }

      const validRules = this.rules.filter(
        r => r.column && r.word.trim() !== ""
      );
      this.$emit("validated", { hub: this.hub, rules: validRules });
    }
  }
};
</script>

<style scoped>
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.hub-popup {
  background: white;
  padding: 25px;
  border-radius: 10px;
  width: 650px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
}

h3 {
  text-align: center;
  font-size: 1.6em;
  margin-bottom: 20px;
  color: #222;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 15px;
}

th, td {
  padding: 10px;
  border-bottom: 1px solid #ddd;
  text-align: center;
  font-size: 14px;
}

/* --- Fond clair pour les cases --- */
select,
input[type="text"],
input[type="number"] {
  width: 95%;
  padding: 6px;
  background: #f5f7fa; /* léger fond gris-bleu */
  border: none;
  border-radius: 5px;
  text-align: center;
  font-size: 14px;
  outline: none;
  transition: background-color 0.2s, border-color 0.2s;
}

select:focus,
input:focus {
  background: #e9f0ff; /* plus clair au focus */
  border: 1px solid #0078ff;
}

/* --- Boutons --- */
.buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.add-btn {
  align-self: flex-start;
  background-color: #0078ff;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s;
}

.add-btn:hover {
  background-color: #005fcc;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.action-buttons button {
  padding: 8px 14px;
  border: none;
  background-color: #0078ff;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.action-buttons button:hover {
  background-color: #005fcc;
}

td button {
  background: transparent;
  color: #444;
  font-size: 18px;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

td button:hover {
  color: #0078ff;
}

td button[disabled] {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
