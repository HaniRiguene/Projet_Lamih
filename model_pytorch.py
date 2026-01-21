import sys
import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import argparse
import glob

# --- 1. DÉFINITION DU MODÈLE ET UTILITAIRES ---

class ImprovedFinancialModel(nn.Module):
    def __init__(self, input_dim):
        super(ImprovedFinancialModel, self).__init__()
        # Le premier calque est dynamique, dimensionné par input_dim
        self.layer1 = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        self.layer2 = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU()
        )
        self.output = nn.Linear(64, 1)
    
    def forward(self, x):
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.output(x)
        return x

def preprocess_data(df):
    """Effectue le nettoyage, le One-Hot Encoding et la Normalisation."""
    print("Info | Prétraitement des données en cours...", flush=True)
    
    if df['Value'].dtype == object:
        df['Value'] = df['Value'].astype(str).str.replace(',', '').str.strip()
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df = df.dropna(subset=['Value'])
    
    # Les colonnes à encoder (doivent être cohérentes entre les clients)
    cols_to_encode = ['Industry_code_NZSIOC', 'Variable_code', 'Units']
    df_clean = df[['Value'] + [c for c in cols_to_encode if c in df.columns]].copy()
    
    # One-Hot Encoding
    df_encoded = pd.get_dummies(df_clean, columns=[c for c in cols_to_encode if c in df_clean.columns], drop_first=True)
    
    X = df_encoded.drop('Value', axis=1).values.astype(float)
    y = df_encoded['Value'].values.reshape(-1, 1).astype(float)

    # Normalisation
    scaler_X = StandardScaler()
    X = scaler_X.fit_transform(X)
    scaler_y = StandardScaler()
    y = scaler_y.fit_transform(y)
    
    return X, y, X.shape[1]

def evaluate_model(model, X_val, y_val):
    """Fonction d'évaluation."""
    model.eval()
    with torch.no_grad():
        X_tensor = torch.tensor(X_val, dtype=torch.float32)
        predictions = model(X_tensor).numpy()
    return r2_score(y_val, predictions)

def train_model(model, X_data, y_data, epochs=3):
    """Fonction d'entraînement local (utilisée par 'client')."""
    model.train()
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.005)

    X_tensor = torch.tensor(X_data, dtype=torch.float32)
    y_tensor = torch.tensor(y_data, dtype=torch.float32).view(-1, 1)

    # Utilisation de DataLoader pour l'entraînement
    dataset = torch.utils.data.TensorDataset(X_tensor, y_tensor)
    loader = torch.utils.data.DataLoader(dataset, batch_size=32, shuffle=True)
    
    loss_item = 0
    for epoch in range(epochs):
        for inputs, targets in loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            loss_item = loss.item()
    
    # Réévaluation après entraînement
    r2 = evaluate_model(model, X_data, y_data)
    
    return model.state_dict(), loss_item, r2

# --- 2. MODES D'EXÉCUTION ---

def mode_initialization(input_dim, output_path):
    """Mode 'init' : Crée le modèle initial avec la dimension imposée."""
    print(f"Info | Initialisation du Modèle Global avec input_dim={input_dim} (valeur du scientifique/serveur)...", flush=True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not output_path.endswith('.pth'):
        print("Erreur | Le chemin de sortie doit être un fichier .pth.", file=sys.stderr, flush=True)
        sys.exit(1)
        
    initial_model = ImprovedFinancialModel(input_dim)
    torch.save(initial_model.state_dict(), output_path)
    
    print(f"RESULTAT_INIT | Poids initiaux sauvegardés ici : {output_path}", flush=True)
    

def mode_federated_learning(dataset_path, model_path, output_path):
    """Mode 'client' : Entraînement local avec adaptation de la dimension."""
    print(f"Info | Démarrage FL sur les données : {dataset_path}", flush=True)
    
    try:
        # 1. DÉTERMINER la dimension attendue à partir du modèle global reçu
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Poids du modèle non trouvés à l'emplacement : {model_path}.")
            
        loaded_state_dict = torch.load(model_path)
        # On lit la dimension attendue sur la deuxième dimension du premier calque de poids (200 dans votre cas)
        expected_input_dim = loaded_state_dict['layer1.0.weight'].shape[1] 
        print(f"Info | Modèle global (Serveur) attend une dimension de : {expected_input_dim}", flush=True)


        # 2. Chargement et Préparation des données LOCALES
        df = pd.read_csv(dataset_path)
        X, y, local_input_dim = preprocess_data(df) 
        print(f"Info | Données locales ont une dimension calculée de : {local_input_dim}", flush=True)

        # La ligne "local_input_dim=500000" a été retirée.

        # 3. ADAPTATION (Padding) si la dimension locale est plus petite
        if local_input_dim < expected_input_dim:
            padding_size = expected_input_dim - local_input_dim
            print(f"Info | Adaptation : Ajout de {padding_size} features de zéros (padding) pour atteindre {expected_input_dim}.", flush=True)
            
            # Ajout des colonnes de zéros à droite
            padding = np.zeros((X.shape[0], padding_size))
            X = np.hstack([X, padding])
            
            # Mise à jour de la dimension locale pour vérification (optionnel, mais propre)
            local_input_dim = X.shape[1] 
            
        elif local_input_dim > expected_input_dim:
            # Cas critique : le client a des features inconnues du modèle global
            raise ValueError(f"Erreur fatale: Le Client a des features ({local_input_dim}) qui sont plus nombreuses que la dimension attendue ({expected_input_dim}).")
        
        # DEBUG : CONFIRMATION DE LA DIMENSION DE X AVANT ENTRAÎNEMENT
        print(f"DEBUG FL | Dimension finale de X avant entraînement : {X.shape[1]}", flush=True)
        # FIN DEBUG

        # 4. Créer et charger le modèle (avec la dimension standardisée)
        # Le modèle est créé avec la dimension attendue (expected_input_dim=200)
        client_model = ImprovedFinancialModel(expected_input_dim)
        client_model.load_state_dict(loaded_state_dict)
        
        # 5. Entraînement local (utilise les données X qui ont la bonne dimension)
        trained_weights, final_loss, final_r2 = train_model(client_model, X, y, epochs=3)
        
        # 6. Sauvegarde du résultat
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        torch.save(trained_weights, output_path)
        
        print(f"RESULTAT_CLIENT | Loss: {final_loss:.4f} | R2 Score: {final_r2:.4f} | Output Path: {output_path}", flush=True)

    except Exception as e:
        print(f"Erreur FL | Échec : {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
        sys.exit(1)


def mode_aggregation(weights_dir, output_path):
    """Mode 'aggregate' : Agrégation FedAvg par le serveur."""
    
    # 1. Collecte de tous les fichiers .pth
    weight_files = glob.glob(os.path.join(weights_dir, '*.pth'))
    
    if not weight_files:
        print(f"Erreur AG | Aucun fichier .pth trouvé dans le répertoire de poids : {weights_dir}", file=sys.stderr, flush=True)
        sys.exit(1)
        
    print(f"Info | Agrégation de {len(weight_files)} fichiers de poids...", flush=True)

    # 2. Chargement de tous les state_dicts
    all_client_weights = [torch.load(file_path) for file_path in weight_files]
    
    avg_state_dict = {}
    
    # 3. FedAvg (Moyenne mathématique)
    for key in all_client_weights[0].keys():
        stack_of_tensors = torch.stack([sd[key] for sd in all_client_weights])
        avg_state_dict[key] = torch.mean(stack_of_tensors, dim=0)
        
    # 4. Sauvegarde du nouveau modèle global
    # La dimension est déduite du calque d'entrée des poids agrégés
    input_dim = all_client_weights[0]['layer1.0.weight'].shape[1] 
    global_model = ImprovedFinancialModel(input_dim)
    global_model.load_state_dict(avg_state_dict)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.save(global_model.state_dict(), output_path)
    
    print(f"RESULTAT_AGGR | Agrégation réussie. Nouveau modèle global sauvegardé ici : {output_path}", flush=True)


# --- 3. BLOC PRINCIPAL (ANALYSE DES ARGUMENTS) ---

def main():
    parser = argparse.ArgumentParser(description="Orchestrateur universel pour l'Apprentissage Fédéré.")
    
    parser.add_argument('--mode', type=str, choices=['client', 'init', 'aggregate'], 
                        default='client', 
                        help="Mode d'exécution ('init', 'client', 'aggregate'). Défaut: client (Client Training).")
    
    # Arguments pour tous les modes ou spécifiques
    parser.add_argument('--dataset', type=str, help="Chemin vers le dataset (requis pour mode 'client').")
    parser.add_argument('--model-path', type=str, help="Chemin vers le modèle à charger (requis pour mode 'client').")
    parser.add_argument('--output-path', type=str, help="Chemin COMPLET de sauvegarde du fichier .pth de sortie (requis pour 'init', 'client', 'aggregate').")
    
    # Arguments spécifiques
    parser.add_argument('--weights-dir', type=str, help="Dossier contenant les poids des clients (requis pour mode 'aggregate').")
    # --input-dim est requis qu'en mode 'init' pour le définir une fois.
    parser.add_argument('--input-dim', type=int, help="Dimension d'entrée initiale du modèle (requis pour mode 'init').")

    args = parser.parse_args()
    
    try:
        if args.mode == 'init':
            if not args.input_dim or not args.output_path:
                raise ValueError("Le mode 'init' requiert --input-dim et --output-path.")
            mode_initialization(args.input_dim, args.output_path)

        elif args.mode == 'client':
            if not args.dataset or not args.model_path or not args.output_path:
                raise ValueError("Le mode 'client' requiert --dataset, --model-path et --output-path.")
            
            # La dimension pour l'adaptation est lue depuis le modèle global lui-même
            mode_federated_learning(args.dataset, args.model_path, args.output_path)

        elif args.mode == 'aggregate':
            if not args.weights_dir or not args.output_path:
                raise ValueError("Le mode 'aggregate' requiert --weights-dir et --output-path.")
            mode_aggregation(args.weights_dir, args.output_path)
            
    except Exception as e:
        print(f"Erreur d'orchestration : {type(e).__name__}: {str(e)}", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()