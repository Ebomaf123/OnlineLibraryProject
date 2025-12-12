import unittest
import json
import os
import shutil
from unittest.mock import patch, mock_open
from library_manager import LibraryManager, DATA_DIR, DATA_FILE

# Configuration spécifique pour les tests
TEST_DATA_DIR = 'test_data_manager'
TEST_DATA_FILE = os.path.join(TEST_DATA_DIR, 'media_data.json')

# Le contenu de test simulé pour les chargements
MOCK_DATA_CONTENT = {
    "100": {
        "name": "Test Entry 1 (Book)",
        "author": "A. Author",
        "publication_date": "2020-01-01",
        "category": "Book"
    },
    "101": {
        "name": "Test Entry 2 (Film)",
        "author": "B. Writer",
        "publication_date": "2021-02-02",
        "category": "Film"
    }
}

class TestLibraryManager(unittest.TestCase):
    """Tests unitaires pour la logique métier de la classe LibraryManager."""

    @classmethod
    def setUpClass(cls):
        """Configure l'environnement de test en utilisant un chemin de données temporaire."""
        cls._original_data_file = DATA_FILE
        cls._original_data_dir = DATA_DIR
        
        # Redirige LibraryManager vers les chemins de test
        LibraryManager.DATA_FILE = TEST_DATA_FILE
        LibraryManager.DATA_DIR = TEST_DATA_DIR

    @classmethod
    def tearDownClass(cls):
        """Nettoyage après l'exécution de tous les tests."""
        # Restaure les chemins de données réels
        LibraryManager.DATA_FILE = cls._original_data_file
        LibraryManager.DATA_DIR = cls._original_data_dir
        # Supprime le répertoire de test, si existant
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)

    def setUp(self):
        """Initialisation avant chaque test : Crée une instance de Manager avec un contenu fixé."""
        # 1. Nettoyage du répertoire
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
        os.makedirs(TEST_DATA_DIR, exist_ok=True)
        
        # 2. Initialise le Manager (il va trouver le fichier vide et ajouter 2 entrées par défaut)
        # Pour forcer le Manager à être dans un état connu, nous allons écraser ses données internes.
        self.manager = LibraryManager()
        
        # 3. Écrase les données internes avec le contenu mocké pour garantir l'état initial (2 entrées)
        self.manager.media_data = MOCK_DATA_CONTENT.copy()
        self.manager._save_data() # Sauvegarde l'état connu dans le fichier de test
        
        # ID spécifique pour les tests
        self.test_delete_id = "101" 

    def tearDown(self):
        """Nettoyage après chaque test : Supprime le répertoire de test."""
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)

    # --- Tests Corrigés ---

    def test_load_data_success(self):
        """Teste le chargement réussi des données initiales à partir du fichier de test."""
        # L'état initial doit être 2 (MOCK_DATA_CONTENT)
        self.assertEqual(len(self.manager.media_data), 2)
        self.assertIn("100", self.manager.media_data)
        self.assertEqual(self.manager.media_data["100"]["name"], "Test Entry 1 (Book)")

    def test_get_all_media_structure(self):
        """Teste la structure de sortie de get_all_media (liste d'objets avec ID intégré)."""
        media_list = self.manager.get_all_media()
        self.assertIsInstance(media_list, list)
        self.assertEqual(len(media_list), 2) # Doit être 2
        
        first_item = media_list[0]
        self.assertIn('id', first_item)
        
    def test_get_media_by_id_success(self):
        """Teste la récupération d'un média par son ID."""
        # Assure l'accès par ID 100
        media = self.manager.get_media_by_id("100")
        self.assertIsNotNone(media)
        self.assertEqual(media['name'], "Test Entry 1 (Book)")
        
    def test_get_media_by_id_not_found(self):
        """Teste la récupération d'un ID qui n'existe pas."""
        media = self.manager.get_media_by_id("999")
        self.assertIsNone(media)

    def test_add_media_success(self):
        """Teste l'ajout réussi d'un nouveau média."""
        initial_count = len(self.manager.media_data) # Devrait être 2
        
        new_media = {
            "name": "New Item",
            "author": "C. Tester",
            "publication_date": "2024-03-03",
            "category": "Magazine"
        }
        
        added_media = self.manager.add_media(**new_media)
        
        self.assertEqual(len(self.manager.media_data), initial_count + 1) # Devient 3
        self.assertIn('id', added_media)
        self.assertEqual(added_media['name'], "New Item")

    def test_delete_media_success(self):
        """Teste la suppression réussie d'un média existant."""
        initial_count = len(self.manager.media_data) # Devrait être 2
        
        # Supprime l'ID 101
        success = self.manager.delete_media(self.test_delete_id)
        
        self.assertTrue(success) # Vérifie que la suppression a réussi
        self.assertEqual(len(self.manager.media_data), initial_count - 1) # Devient 1
        self.assertIsNone(self.manager.get_media_by_id(self.test_delete_id))

    def test_delete_media_not_found(self):
        """Teste la tentative de suppression d'un ID qui n'existe pas."""
        initial_count = len(self.manager.media_data) # Devrait être 2
        
        success = self.manager.delete_media("999")
        
        self.assertFalse(success) # La suppression doit échouer
        self.assertEqual(len(self.manager.media_data), initial_count) # La liste ne doit pas changer (reste 2)

    def test_search_media_by_name_success(self):
        """Teste la recherche par nom (insensible à la casse)."""
        media = self.manager.search_media_by_name("TEST eNtry 1 (book)")
        self.assertIsNotNone(media)
        self.assertEqual(media['id'], "100")
        
    def test_get_media_by_category(self):
        """Teste le filtrage par catégorie (Film)."""
        films = self.manager.get_media_by_category("Film")
        self.assertEqual(len(films), 1)
        self.assertEqual(films[0]['name'], "Test Entry 2 (Film)") # Nom complet corrigé

    def test_add_media_invalid_category(self):
        """Teste l'ajout avec une catégorie non valide."""
        invalid_media = {
            "name": "Bad Item",
            "author": "X",
            "publication_date": "2024-01-01",
            "category": "Podcast"
        }
        with self.assertRaises(ValueError):
            self.manager.add_media(**invalid_media)

if __name__ == '__main__':
    unittest.main()