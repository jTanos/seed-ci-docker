"""Flask Web API Application"""

import sys
import os
from flask import Flask, request, jsonify, abort, render_template, json
from flask_restplus import Api, Resource, fields, apidoc
from flask_cors import CORS
from functools import wraps
import inspect
from api.helpers.utilshelper import UtilsHelper
from api.handlers.loghandler import LogHandler
# from urllib3.contrib import pyopenssl


# def auth_ignored(func):
#     """Add to ignore authentication. Add @api.doc(security=None) to the method so that it is not displayed in the UI."""
#     return func

def auth_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):       
        # LogHandler.getCurrentClassLogger().debug("ACA")
        # try:
        #     source = inspect.getsource(f.view_class)
        # except Exception as e:
        #     LogHandler.getCurrentClassLogger().exception("decorator. %s", e)    
        #     raise 
        # LogHandler.getCurrentClassLogger().debug("ACA1")     
        # auth_ignored = False
        # for line in source.split('\n'):
        #     index_auth_ignored = line.find("@auth_ignored") 
        #     if index_auth_ignored != -1 and not line.strip().startswith('#'):
        #         auth_ignored = True
        #         break
        # LogHandler.getCurrentClassLogger().debug("ACA2")     
        # if request.endpoint != "specs" and not auth_ignored:            
        if request.endpoint != "specs":            
            auth = request.authorization
            status = {'Basic Auth': {'type': 'basic','in': 'header','name': 'Authorization'}}

            if not auth or not auth.username or not auth.password:
                raise abort(401, str(status))

            if auth.username != flask_app.config['USERNAME'] or auth.password != flask_app.config['PASSWORD']:
                raise abort(401, "Invalid username or password auth.")
        return f(*args, **kwargs)
       
    return decorator

### DEFINO UNA NUEVA RUTA STATIC PARA LOS ARCHIVOS DE LA INTERFACE SWAGGER UI
@apidoc.apidoc.add_app_template_global
def swagger_static(filename):
    return "./static/{0}".format(filename)
### DEFINO UNA NUEVA RUTA STATIC PARA LOS ARCHIVOS DE LA INTERFACE SWAGGER UI


authorizations = {
    'Basic Auth': {
        'type': 'basic',
        'in': 'header',
        'name': 'Authorization'
    }   
}

flask_app = Flask(__name__, template_folder=UtilsHelper.resourcePath('api\\src\\templates'), static_folder=UtilsHelper.resourcePath('api\\src\\static'))
# Authentication
flask_app.config['USERNAME']='test'
flask_app.config['PASSWORD']='test2020'
flask_app.config['APP_DIRECTORY']= UtilsHelper.originalPath('')
flask_app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


cors = CORS(flask_app, resources={r"/*": {"origins": "*"}})
api = Api(app = flask_app,
        version = 1.0, 
        title = "Web API", 
        description = "Manage the use and configuration of the web api application.",
        # decorators=[auth_required], ### Agrega authentication global usando decoradores
        security='Basic Auth',
        authorizations=authorizations,
        prefix="/api/v1.0")

### TERMINO DE DEFINIR UN LA UI CUSTOM
@api.documentation
def custom_ui():
    return render_template("swagger-ui.html", title=api.title, specs_url= "/specs.json")

### DEFINO ARCHIVO DE SPECIFICACIONES
@flask_app.route("/specs.json")
def create_swagger_spec():
    return jsonify(api.__schema__)

# Import namespaces
from api.src.namespaces import user_namespace