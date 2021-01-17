from .models import User
from app import app, db
from .controllers.auth_controller import AuthController
from .controllers.msg_controller import MsgController
from flask import request
# from flask_cors import CORS
# import os
# CORS(app, origins=[os.environ.get('CLIENT_HOST')])
# from flask import redirect

auth_controller = AuthController()
msg_controller = MsgController()

@app.before_first_request
def before_first_request_func():
    db.create_all()


@app.route('/')
def index():
    return 'identity-service is working!'


@app.route('/auth/register', methods=['POST'])
def register():
    return auth_controller.register(request.form)


@app.route('/auth/login', methods=['POST'])
def auth():
    return auth_controller.login(request.form)


@app.route('/auth/getIdByToken/<int:user_token>', methods=['GET'])
def get_id_by_token(user_token):
    return auth_controller.get_id_by_token(user_token)


@app.route('/auth/status', methods=['GET'])
def status():
    return auth_controller.status()


@app.route('/auth/logout', methods=['GET'])
def logout():
    return auth_controller.logout()


@app.route('/users/<int:id>', methods=['DELETE'])
def delete(id):
    try:
        db.session.delete(User.query.filter_by(id=id).first())
        db.session.commit()
        return 'Deleted user #' + id
    except:
        return 'Error'


@app.route('/message', methods=['POST'])
def message():
    return msg_controller.new_msg(request.form)
