import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import date 

# --- Configuration ---
# Adresse de base de votre API Flask
API_BASE_URL = "http://127.0.0.1:5000"

# --- Classe de l'application Tkinter (Objet principal du GUI) ---
class LibraryApp:
    def __init__(self, master):
        self.master = master
        master.title("Online Library Management System (Tkinter Client)")
        master.geometry("850x550")

        self.categories = ["All", "Book", "Film", "Magazine"]
        self.current_media_list = [] # Stocke la liste des médias chargés

        # 1. Cadre de Contrôle (Haut)
        control_frame = ttk.Frame(master, padding="10 10 10 10")
        control_frame.pack(fill='x')

        # Dropdown Catégorie
        ttk.Label(control_frame, text="Catégorie:").pack(side='left', padx=(0, 5))
        # La variable category_var gère l'état et l'affichage du Combobox
        self.category_var = tk.StringVar(master, value=self.categories[0])
        category_menu = ttk.Combobox(control_frame, textvariable=self.category_var, values=self.categories, width=15, state="readonly")
        category_menu.pack(side='left', padx=5)
        # Appel de filter_media lors de la sélection
        category_menu.bind('<<ComboboxSelected>>', self.filter_media) 

        # Bouton Load (Charger tout)
        ttk.Button(control_frame, text="Charger tout", command=lambda: self.load_media(reset_category=True)).pack(side='left', padx=10)

        # Champ de recherche
        ttk.Label(control_frame, text="Recherche Nom:").pack(side='left', padx=(20, 5))
        self.search_entry = ttk.Entry(control_frame, width=30)
        self.search_entry.pack(side='left', padx=5)
        # Bind pour la touche Entrée
        self.search_entry.bind('<Return>', lambda event: self.search_media())
        ttk.Button(control_frame, text="Rechercher", command=self.search_media).pack(side='left', padx=5)

        # 2. Zone d'affichage (Milieu) - Treeview (Table)
        self.tree = ttk.Treeview(master, columns=("ID", "Name", "Author", "Date", "Category"), show='headings')
        self.tree.heading("ID", text="ID", anchor=tk.W)
        self.tree.heading("Name", text="Nom", anchor=tk.W)
        self.tree.heading("Author", text="Auteur / Réalisateur", anchor=tk.W)
        self.tree.heading("Date", text="Date de Publication", anchor=tk.W)
        self.tree.heading("Category", text="Catégorie", anchor=tk.W)

        # Ajustement des largeurs de colonnes
        self.tree.column("ID", width=50, stretch=tk.NO)
        self.tree.column("Name", width=250, stretch=tk.YES)
        self.tree.column("Author", width=200, stretch=tk.YES)
        self.tree.column("Date", width=120, stretch=tk.NO)
        self.tree.column("Category", width=100, stretch=tk.NO)

        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Correction pour le double-clic (liaison de l'événement)
        self.tree.bind("<Double-1>", self.show_media_details)
        
        # 3. Cadre d'Actions (Bas)
        action_frame = ttk.Frame(master, padding="0 0 10 10")
        action_frame.pack(fill='x')
        
        # Boutons d'action
        ttk.Button(action_frame, text="Nouveau Média", command=self.open_create_window).pack(side='left', padx=10)
        ttk.Button(action_frame, text="Supprimer Sélectionné", command=self.delete_selected_media).pack(side='left', padx=10)

        # Chargement initial des données
        self.load_media()

    # --- Fonctions de Communication HTTP ---

    def _safe_request(self, method, endpoint, **kwargs):
        """Fonction utilitaire pour gérer l'erreur de connexion HTTP et les erreurs API."""
        try:
            response = requests.request(method, f"{API_BASE_URL}{endpoint}", **kwargs)
            
            # Vérifie les erreurs HTTP (4xx et 5xx)
            if 400 <= response.status_code < 600: 
                try:
                    error_data = response.json().get('error', response.text)
                    if response.status_code != 404 and response.status_code != 204: 
                        messagebox.showerror("Erreur API", f"Requête échouée ({response.status_code}): {error_data}")
                except json.JSONDecodeError:
                    messagebox.showerror("Erreur API", f"Requête échouée ({response.status_code}). Le serveur n'a pas retourné de JSON.")
                return None
                
            return response
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erreur de Connexion", "Impossible de se connecter au serveur Flask. Assurez-vous que backend_server.py est en cours d'exécution.")
            return None
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur inattendue s'est produite: {e}")
            return None

    def load_media(self, endpoint="/media", reset_category=False):
        """Charge tous les médias ou selon un endpoint spécifique. Réinitialise la catégorie si demandé."""
        self.search_entry.delete(0, tk.END) # Efface la recherche
        
        if reset_category:
            # Réinitialise la variable du Combobox à "All"
            self.category_var.set(self.categories[0]) 

        response = self._safe_request('GET', endpoint)

        if response is None:
            self.update_treeview([]) 
            return

        if response.status_code == 200:
            data = response.json()
            # Gère les cas où l'API renvoie un objet unique (comme la recherche)
            if isinstance(data, dict):
                 self.current_media_list = [data]
            elif isinstance(data, list):
                 self.current_media_list = data
            else:
                 self.current_media_list = []
                 
            self.update_treeview(self.current_media_list)
        else:
             self.update_treeview([])

    def filter_media(self, event=None):
        """Filtre les médias selon la catégorie sélectionnée (Corrigé)."""
        selected_category = self.category_var.get() 
        if selected_category == "All":
            # Si "All" est sélectionné, on charge tout (sans réinitialiser la variable d'état, car elle est déjà "All")
            self.load_media(reset_category=False) 
        else:
            # Charge l'endpoint de catégorie
            self.load_media(endpoint=f"/media/category/{selected_category}", reset_category=False)

    def search_media(self):
        """Recherche un média par nom exact."""
        search_name = self.search_entry.get().strip()
        if not search_name:
            messagebox.showwarning("Avertissement", "Veuillez entrer un nom à rechercher.")
            self.load_media(reset_category=True) 
            return
            
        # Réinitialise la catégorie affichée pour montrer qu'on est en mode recherche
        self.category_var.set("All") 

        response = self._safe_request('GET', f"/media/search?name={search_name}")
        
        if response is None:
            return

        if response.status_code == 200:
            found_media = response.json() 
            messagebox.showinfo("Résultat de Recherche", f"Média trouvé: {found_media['name']}")
            self.update_treeview([found_media])
        elif response.status_code == 404:
            messagebox.showinfo("Résultat de Recherche", f"Média '{search_name}' non trouvé.")
            self.update_treeview([]) 


    def delete_selected_media(self):
        """Supprime le média sélectionné."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un média à supprimer.")
            return

        media_id = self.tree.item(selected_item, 'values')[0]
        
        if not messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer le média ID {media_id}?"):
            return

        response = self._safe_request('DELETE', f"/media/{media_id}")

        if response is None:
            return

        if response.status_code == 204: # 204 NO CONTENT = succès
            messagebox.showinfo("Succès", "Média supprimé avec succès.")
            self.load_media(reset_category=True) # Recharger la liste et réinitialiser la catégorie

    # Correction pour le double-clic: utilise self.tree.selection()
    def show_media_details(self, event):
        """Affiche les métadonnées détaillées au double-clic."""
        # Récupère la sélection actuelle
        selected_items = self.tree.selection()
        if not selected_items:
            return

        # L'ID est dans la première colonne de l'élément sélectionné
        media_id = self.tree.item(selected_items[0], 'values')[0]

        response = self._safe_request('GET', f"/media/{media_id}")
        
        if response is None:
            return

        if response.status_code == 200:
            media = response.json()
            details = (
                f"ID: {media.get('id', 'N/A')}\n"
                f"Nom: {media.get('name', 'N/A')}\n"
                f"Auteur / Réalisateur: {media.get('author', 'N/A')}\n"
                f"Catégorie: {media.get('category', 'N/A')}\n"
                f"Date de Publication: {media.get('publication_date', 'N/A')}\n"
                f"Date de Création: {media.get('creation_date', 'N/A')}" 
            )
            messagebox.showinfo(f"Détails du Média ID {media_id}", details)

    # --- Fonctions d'Interface ---

    def update_treeview(self, media_list):
        """Met à jour le contenu de la table (Treeview). (Optimisé pour la réactivité)"""
        # Efface les lignes existantes
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Insère les nouvelles lignes
        for media in media_list:
            self.tree.insert('', 'end', values=(
                media.get('id', 'N/A'),
                media.get('name', ''),
                media.get('author', ''),
                media.get('publication_date', ''),
                media.get('category', '')
            ))

    def open_create_window(self):
        """Ouvre une nouvelle fenêtre pour la création de médias."""
        CreateMediaWindow(self.master, self.load_media)


class CreateMediaWindow:
    def __init__(self, master, callback):
        self.callback = callback
        self.top = tk.Toplevel(master)
        self.top.title("Créer un Nouveau Média")
        self.top.geometry("400x300")
        self.top.grab_set() 
        self.top.resizable(False, False)

        ttk.Label(self.top, text="Métadonnées du Nouveau Média").pack(pady=10)

        fields = ["Nom:", "Auteur:", "Date de Publication (AAAA-MM-JJ):"]
        self.entries = {}
        
        default_date = date.today().strftime("%Y-%m-%d")

        for field in fields:
            row = ttk.Frame(self.top)
            row.pack(fill='x', padx=5, pady=5)
            ttk.Label(row, text=field, width=25, anchor='w').pack(side='left')
            entry = ttk.Entry(row)
            entry.pack(side='right', expand=True, fill='x', padx=5)
            
            if "Date" in field:
                entry.insert(0, default_date)
                
            self.entries[field.replace(":", "")] = entry

        # Catégorie (Dropdown)
        row = ttk.Frame(self.top)
        row.pack(fill='x', padx=5, pady=5)
        ttk.Label(row, text="Catégorie:", width=25, anchor='w').pack(side='left')
        
        creation_categories = ["Book", "Film", "Magazine"]
        
        self.category_var = tk.StringVar(self.top, value=creation_categories[0]) 
        
        category_menu = ttk.Combobox(
            row, 
            textvariable=self.category_var, 
            values=creation_categories, 
            state="readonly"
        )
        category_menu.pack(side='right', expand=True, fill='x', padx=5)
        
        category_menu.set(creation_categories[0]) 

        ttk.Button(self.top, text="Créer", command=self.submit_media).pack(pady=10)

    def submit_media(self):
        """Envoie la nouvelle donnée via POST à l'API."""
        category_selected = self.category_var.get()
        
        data = {
            "name": self.entries["Nom"].get(),
            "author": self.entries["Auteur"].get(),
            "publication_date": self.entries["Date de Publication (AAAA-MM-JJ)"].get(),
            "category": category_selected 
        }
        
        # Validation côté client (basique)
        if not all(data.values()):
            messagebox.showwarning("Erreur de Validation", "Tous les champs doivent être remplis.")
            return

        try:
            # IMPORTANT: Le paramètre json=data dans requests.post gère la sérialisation en JSON
            response = requests.post(f"{API_BASE_URL}/media", json=data) 
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erreur de Connexion", "Impossible de se connecter au serveur Flask.")
            return
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur inattendue s'est produite: {e}")
            return
        
        if response.status_code == 201: # 201 CREATED
            messagebox.showinfo("Succès", f"Média '{data['name']}' créé avec succès!")
            self.top.destroy()
            # Appel de la callback pour recharger la liste (avec reset_category=True)
            self.callback(reset_category=True) 
        elif 400 <= response.status_code < 500: 
            try:
                error_details = response.json().get('error', 'Erreur inconnue')
            except json.JSONDecodeError:
                error_details = response.text or 'Réponse de serveur invalide.'

            messagebox.showerror(f"Échec de la Création ({response.status_code})", f"Erreur: {error_details}")
        else:
            # Gère les erreurs serveur (500)
            messagebox.showerror("Erreur Serveur", f"Échec de la création. Statut: {response.status_code}")


# --- Point d'entrée de l'application ---
if __name__ == '__main__':
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()