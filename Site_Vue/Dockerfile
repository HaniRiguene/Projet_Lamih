# Étape 1: Construction (build-stage)
# Utilise une image Node pour compiler l'application Vue.js
FROM node:20 as build-stage
WORKDIR /app

# Copier les fichiers de configuration nécessaires pour installer les dépendances
# Assurez-vous que le sous-dossier 'portail' existe dans votre dossier 'vue_app'
COPY ./portail/package*.json ./portail/

# Aller dans le répertoire de l'application et installer les dépendances
WORKDIR /app/portail
RUN npm install

# Copier le reste du code source de l'application Vue.js
COPY ./portail/ . /app/portail/

# Lancer la compilation de l'application (le résultat va dans /app/portail/dist)
RUN npm run build 

# Étape 2: Production (production-stage)
# Utilise une image Nginx légère pour servir les fichiers statiques compilés
FROM nginx:stable-alpine as production-stage

# Copier le dossier 'dist' (les fichiers optimisés) depuis l'étape de construction précédente
# Le chemin source est : /app/portail/dist
COPY --from=build-stage /app/portail/dist /usr/share/nginx/html 

# Port exposé par Nginx
EXPOSE 80

# Commande par défaut pour lancer Nginx
CMD ["nginx", "-g", "daemon off;"]