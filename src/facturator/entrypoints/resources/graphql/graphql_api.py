from flask import Blueprint, jsonify, request
from ariadne import graphql_sync
from .resolvers import explorer_html, schema

def create_gql_api_blueprint(uow):
    graphql_bp = Blueprint('graphql_bp', __name__)


    @graphql_bp.route("/graphql", methods=["GET"])
    def graphql_explorer():
        return explorer_html, 200


    @graphql_bp.route("/graphql", methods=["POST"])
    def graphql_server():
        data = request.get_json()

        success, result = graphql_sync(
            schema,
            data,
            context_value={"request": request, "uow": uow},
            debug=True
        )

        status_code = 200 if success else 400
        return jsonify(result), status_code
    
    return graphql_bp
