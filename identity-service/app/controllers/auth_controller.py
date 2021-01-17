from ..models import User, BlacklistToken
from app import app, db, bcrypt
from flask import request, make_response, jsonify


class AuthController:
    @staticmethod
    def register(form):
        email = form['email']
        password = form['password']

        user = User.query.filter_by(email=email).first()
        if not user:
            try:
                user = User(
                    email=email,
                    password=password)

                db.session.add(user)
                db.session.commit()
                auth_token = user.encode_auth_token(user.id)
                responseObject = {
                    'auth_token': auth_token.decode(),
                    "meta": {
                        'status': 'success',
                        'message': 'Successfully registered.'
                    },
                    "user": {
                        'id': user.id,
                        'email': user.email,
                        'password': user.password
                    }
                }
                return make_response(jsonify(responseObject)), 201
            except Exception as e:
                return {"error": f'Some error occurred. Please try again. {e}'}, 401

        return {"error": 'User already exists. Please Log in.'}, 202

    @staticmethod
    def login(form):
        email = form['email']
        password = form['password']

        try:
            user = User.query.filter_by(email=email).first()
            if user or bcrypt.check_password_hash(user.password, password):
                auth_token = user.encode_auth_token(user.id)
                if auth_token:
                    return {
                                'auth_token': auth_token.decode(),
                                "user": {
                                    'id': user.id,
                                    'email': user.email,
                                    'password': user.password
                                }
                           }, 200
            else:
                return {"error": 'User does not exist.'}, 404

        except Exception as e:
            return {"error": f'Try again. {e}'}, 500

    @staticmethod
    def get_id_by_token(self, user_token):
        try:
            user = User.query.get(user_token)

            if not user:
                return {"error": 'Invalid token.'}, 403

            return {"user": user.id}
        except Exception as e:
            return {"error": str(e)}, 500

    @staticmethod
    def status():
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]
            except IndexError:
                responseObject = {
                    'status': 'fail',
                    'message': 'Bearer token malformed.'
                }
                return make_response(jsonify(responseObject)), 401
        else:
            auth_token = None
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                user = User.query.filter_by(id=resp).first()
                responseObject = {
                    'status': 'success',
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'admin': user.admin,
                        'registered_on': user.registered_on
                    }
                }
                return make_response(jsonify(responseObject)), 200
            responseObject = {
                'status': 'fail',
                'message': resp
            }
            return make_response(jsonify(responseObject)), 401
        else:
            responseObject = {
                'status': 'fail',
                'message': 'Provide a valid auth token.'
            }
            return make_response(jsonify(responseObject)), 401

    @staticmethod
    def logout():
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        if auth_token:
            resp = User.decode_auth_token(auth_token)
            if not isinstance(resp, str):
                blacklist_token = BlacklistToken(token=auth_token)
                try:
                    db.session.add(blacklist_token)
                    db.session.commit()
                    responseObject = {
                        'status': 'success',
                        'message': 'Successfully logged out.'
                    }
                    return make_response(jsonify(responseObject)), 200
                except Exception as e:
                    responseObject = {
                        'status': 'fail',
                        'message': e
                    }
                    return make_response(jsonify(responseObject)), 200
            else:
                responseObject = {
                    'status': 'fail',
                    'message': resp
                }
                return make_response(jsonify(responseObject)), 401
        else:
            responseObject = {
                'status': 'fail',
                'message': 'Provide a valid auth token.'
            }
            return make_response(jsonify(responseObject)), 403

