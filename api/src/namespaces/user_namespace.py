from flask import request
from flask_restplus import Resource, fields
from werkzeug.security import generate_password_hash, check_password_hash
from api.src.app import api, auth_required


user_namespace = api.namespace('user', description='Manage users functions.')

login_request_model = api.model('Login Request Model', 
    {
        'Username': fields.String(required = True, description="Username to login", help="Username cannot be blank."),
        'Password': fields.String(required = True, description="Password to login", help="Password cannot be blank.")
    }
)

user_response_model = api.model('User Response Model', 
    {
        'Username': fields.String,
        'Rol': fields.Integer,
        'Endpoint': fields.String,
        # 'Password': fields.String(attribute=lambda x: x.PasswordSql)
    })

@user_namespace.route("/login")
class LoginClass(Resource):

    @api.response(200, 'Success', user_response_model)
    @api.response(400, 'Invalid Argument')
    @api.response(404, 'Not Found')
    @api.response(500, 'Mapping Key Error')
    @api.expect(login_request_model)
    @api.marshal_with(user_response_model)
    @auth_required
    def post(self):
        username = request.json.get("Username", None)
        password = request.json.get("Password", None)
        if username is not None and password is not None:
            user = {}
            user["Username"] = username 
            user["Rol"] = "Admin"
            user["Endpoint"] = "test"
            if user is None:
                raise user_namespace.abort(404, message="Username or Password is invalid", description="", status = "Could not save information", statusCode = "404")
            return user
        else:
            raise user_namespace.abort(400, message="Username and Password is required", description="", status = "Could not save information", statusCode = "400")


@user_namespace.route("/test")
class TestClass(Resource):

    @api.response(400, 'Invalid Argument')
    @api.response(404, 'Not Found')
    @api.response(500, 'Mapping Key Error')
    def get(self):
        return "Ok"