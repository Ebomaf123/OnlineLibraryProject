import json
import os
from datetime import datetime
import uuid

# Configuration des chemins d'accès
DATA_DIR = 'data'
# Utilise media_data.json (le typo "meida_data.json" a été corrigé ici)
DATA_FILE = os.path.join(DATA_DIR, 'media_data.json') 

class LibraryManager:
    """
    Gère la lecture, l'écriture et la manipulation des données de la librairie.
    Les données sont stockées en mémoire sous forme de dictionnaire {ID: media_object} 
    pour une recherche et suppression O(1).
    """

    def __init__(self):
        # Assure l'existence du répertoire de données.
        # Comme vous avez confirmé que 'data' existe, cette ligne est une sécurité.
        os.makedirs(DATA_DIR, exist_ok=True)
        self.categories_allowed = ["Book", "Film", "Magazine"]
        self.media_data = self._load_data()
        self._ensure_initial_data()

    def _load_data(self):
        """Charge les données depuis le fichier JSON."""
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 0:
            try:
                with open(DATA_FILE, 'r') as f:
                    # Charge le dictionnaire {ID: media_object}
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error: JSON file '{DATA_FILE}' is corrupted. Starting with empty data.")
                return {}
            except Exception as e:
                print(f"Error reading file '{DATA_FILE}': {e}. Starting with empty data.")
                return {}
        return {}

    def _save_data(self):
        """Sauvegarde les données actuelles dans le fichier JSON."""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.media_data, f, indent=4)
        except Exception as e:
            print(f"FATAL ERROR: Could not write data to '{DATA_FILE}': {e}")

    def _ensure_initial_data(self):
        """S'assure qu'il y a des données de base si le fichier était vide."""
        if not self.media_data:
            print("INFO: Data file was empty. Adding initial dummy media for testing.")
            
            # Ajout des exemples pour initialisation
            self.add_media(
                name="The Hitchhiker's Guide to the Galaxy",
                author="Douglas Adams",
                publication_date="1979-10-12",
                category="Book"
            )
            self.add_media(
                name="Inception",
                author="Christopher Nolan",
                publication_date="2010-07-16",
                category="Film"
            )
            
            self._save_data() # Sauvegarde après l'ajout des exemples

    def get_all_media(self):
        """Retourne la liste complète des médias, incluant l'ID comme champ."""
        # Convertit le dictionnaire {ID: media} en liste de [media avec ID] pour l'API
        return [{"id": k, **v} for k, v in self.media_data.items()]

    def get_media_by_id(self, media_id):
        """Retourne un média par ID (recherche O(1)), ou None s'il n'est pas trouvé."""
        media = self.media_data.get(str(media_id))
        if media:
            return {"id": str(media_id), **media}
        return None

    def get_media_by_category(self, category):
        """Retourne les médias filtrés par catégorie."""
        all_media_list = self.get_all_media()
        return [media for media in all_media_list if media.get('category') == category]

    def search_media_by_name(self, name):
        """Recherche un média par nom exact (insensible à la casse)."""
        name_lower = name.lower()
        for media_id, media in self.media_data.items():
            if media.get('name', '').lower() == name_lower:
                return {"id": media_id, **media}
        return None

    def _get_next_id(self):
        """Génère le prochain ID numérique séquentiel pour la démo."""
        if not self.media_data:
            return "1"
        try:
            # Trouve le max ID numérique et ajoute 1
            max_id = max(int(k) for k in self.media_data.keys() if k.isdigit())
            return str(max_id + 1)
        except ValueError:
            # Fallback à UUID si les IDs sont mélangés (plus robuste)
            return str(uuid.uuid4())
            
    def add_media(self, name, author, publication_date, category):
        """Ajoute un nouveau média et le sauvegarde. Retourne le nouvel objet."""
        
        if category not in self.categories_allowed:
            raise ValueError(f"Invalid category: {category}. Must be one of {self.categories_allowed}")

        # Utilise un ID unique
        media_id = self._get_next_id()
        
        new_media_data = {
            "name": name,
            "author": author,
            "publication_date": publication_date,
            "category": category,
            "creation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.media_data[media_id] = new_media_data
        self._save_data()
        
        return {"id": media_id, **new_media_data}

    def delete_media(self, media_id):
        """Supprime un média par ID. Retourne True si supprimé (O(1)), False sinon."""
        media_id_str = str(media_id)
        if media_id_str in self.media_data:
            del self.media_data[media_id_str]
            self._save_data()
            return True
        return False