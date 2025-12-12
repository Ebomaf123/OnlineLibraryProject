from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from library_manager import LibraryManager
import json

app = Flask(__name__)
# Permet les requêtes de tous les clients (important pour le frontend local)
CORS(app) 
manager = LibraryManager()

# --- Endpoint 1 & 2: Lister tous les médias ou par catégorie ---
@app.route('/media', methods=['GET'])
def get_all_media():
    """Retourne tous les médias."""
    return jsonify(manager.get_all_media())

@app.route('/media/category/<string:category>', methods=['GET'])
def get_media_by_category(category):
    """Retourne les médias filtrés par catégorie."""
    # Assurez-vous que la catégorie demandée est valide
    if category not in manager.categories_allowed:
        # 400 Bad Request si la catégorie n'est pas supportée
        abort(400, description=f"Invalid category: {category}. Must be one of {manager.categories_allowed}")
        
    media_list = manager.get_media_by_category(category)
    return jsonify(media_list)


# --- Endpoint 3: Recherche ---
@app.route('/media/search', methods=['GET'])
def search_media():
    """Recherche un média par nom exact."""
    name = request.args.get('name')
    if not name:
        # 400 Bad Request si le paramètre 'name' est manquant
        abort(400, description="Missing 'name' query parameter.")
        
    media = manager.search_media_by_name(name)
    if media:
        return jsonify(media)
    # 404 Not Found si aucun média n'est trouvé
    abort(404, description=f"Media with name '{name}' not found.")


# --- Endpoint 4: Détails par ID ---
@app.route('/media/<string:media_id>', methods=['GET'])
def get_media(media_id):
    """Retourne un média par ID."""
    media = manager.get_media_by_id(media_id)
    if media:
        return jsonify(media)
    # 404 Not Found si l'ID n'existe pas
    abort(404, description=f"Media ID {media_id} not found.")


# --- Endpoint 5: Création d'un média (POST) ---
@app.route('/media', methods=['POST'])
def add_media():
    """Ajoute un nouveau média. Gère la validation et les erreurs."""
    if not request.json:
        # 400 Bad Request si le corps de la requête n'est pas JSON
        abort(400, description="Request body must be JSON.")
        
    data = request.json
    required_fields = ["name", "author", "publication_date", "category"]
    
    # Vérification des champs obligatoires
    for field in required_fields:
        if field not in data:
            # 400 Bad Request si un champ obligatoire est manquant
            abort(400, description=f"Missing required field: {field}")
            
    # Validation spécifique de la catégorie
    if data['category'] not in manager.categories_allowed:
        abort(400, description=f"Invalid category: {data['category']}. Must be one of {manager.categories_allowed}")

    try:
        new_media = manager.add_media(
            data['name'],
            data['author'],
            data['publication_date'],
            data['category']
        )
        # 201 Created pour un ajout réussi
        return jsonify(new_media), 201
    except ValueError as e:
        # Gère les erreurs internes comme les formats de date ou d'autres validations du manager
        abort(400, description=str(e))
    except Exception as e:
        # 500 Internal Server Error pour toute autre erreur non gérée
        print(f"Server Error during media creation: {e}")
        abort(500, description="Internal server error during data processing.")


# --- Endpoint 6: Suppression d'un média (DELETE) ---
@app.route('/media/<string:media_id>', methods=['DELETE'])
def delete_media_route(media_id):
    """Supprime un média par ID."""
    if manager.delete_media(media_id):
        # 204 No Content pour une suppression réussie sans corps de réponse
        return '', 204
    else:
        # 404 Not Found si l'ID n'existe pas
        abort(404, description=f"Media ID {media_id} not found for deletion.")


# --- Gestion des erreurs personnalisée pour une meilleure réponse ---
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def handle_error(error):
    """Génère une réponse JSON pour toutes les erreurs HTTP."""
    response = jsonify(error=error.description)
    response.status_code = error.code
    return response

if __name__ == '__main__':
    # Le debug=True permet le rechargement automatique du serveur lors des changements de code
    app.run(debug=True)
    # STATUT: V1.0 - Le serveur Flask est configuré et les endpoints CRUD de l'API sont prêts.
    