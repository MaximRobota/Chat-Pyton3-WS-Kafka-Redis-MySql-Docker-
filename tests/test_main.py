import os
import pytest
import requests
import socketio
import subprocess
from pathlib import Path
from loguru import logger
from time import sleep

REPO_ROOT = Path(os.path.realpath(__file__)).parent.parent


@pytest.fixture
def prepare_services():
    # devnull so that there is not output
    # subprocess.run(['docker-compose', 'down'], cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['docker-compose', 'down'], cwd=REPO_ROOT)
    # subprocess.run(['docker-compose', 'build'], cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['docker-compose', 'build'], cwd=REPO_ROOT)
    # Popen instead of .run() so that we do not wait for the process to finish
    # -d is removed so that the output comes to the 'docker' variable
    #
    docker = subprocess.Popen(['docker-compose', 'up'], cwd=REPO_ROOT)
    # docker = subprocess.Popen(['docker-compose', 'up', 'websocket_service'], cwd=REPO_ROOT)
    for i in range(8):
        logger.info('Trying to get connection to a microservice')
        try:
            resp = requests.get('http://localhost:5053')
            resp.raise_for_status()
            break
        except Exception as e:
            logger.error(e)
            pass
        sleep(5)
    else:
        docker.kill()
        subprocess.run(['docker-compose', 'down'], cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise Exception("Couldn't start microservice")
        # pytest.raise("Couldn't start microservice")

    sleep(5)
    # remove this, this is so we wait some time and then start a test,
    # just let the logs settle a little, and stop spamming
    for _ in range(5):
        logger.info("Established connection to microservice")
        sleep(1)
    subprocess.run(['docker-compose', 'ps'], cwd=REPO_ROOT)
    sleep(5)
    yield
    docker.kill()
    subprocess.run(['docker-compose', 'down'], cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def register_user(email, password):
    return requests.post(
        'http://localhost:5051/auth/register', data={'email': email, 'password': password}).json()


def login_user(email, password):
    return requests.post(
        'http://localhost:5051/auth/login', data={'email': email, 'password': password}).json()

def connect_socket(user_email, password):
    register_user(user_email, password)
    resp_login = login_user(user_email, password)

    assert 'auth_token' in resp_login

    headers = {'Authorization': 'Bearer ' + resp_login['auth_token']}
    resp_status = requests.get('http://localhost:5051/auth/status', headers=headers)
    resp_status_json = resp_status.json()
    assert resp_status_json['user']['email'] == user_email
    assert 'id' in resp_status_json['user']

    sio = socketio.Client()
    sio.connect('http://localhost:5053', {"token": resp_login['auth_token']})
    assert sio.connected
    return sio


# @pytest.mark.usefixtures('prepare_services')
# def test_registrer():
#     user_email = 'Vasiya@gm.com'
#     password = 'pass'
#     resp_register = register_user(user_email, password)
#     assert 'user' in resp_register
#     assert resp_register['user']['email'] == user_email
#     assert 'id' in resp_register['user']
#
#
# @pytest.mark.usefixtures('prepare_services')
# def test_login():
#     user_email = 'Vasiya@gm.com'
#     password = 'pass'
#     resp_register = register_user(user_email, password)
#     resp_login = login_user(user_email, password)
#     assert 'auth_token' in resp_login
#     assert resp_login['user']['email'] == user_email
#     assert 'id' in resp_login['user']
#
#
# @pytest.mark.usefixtures('prepare_services')
# def test_user_status():
#     user_email = 'Vasiya@gm.com'
#     password = 'pass'
#     resp_register = register_user(user_email, password)
#     assert 'user' in resp_register
#     assert 'auth_token' in resp_register
#
#     resp_login = login_user(user_email, password)
#
#     assert 'user' in resp_login
#     assert 'auth_token' in resp_login
#
#     headers = {'Authorization': 'Bearer ' + resp_login['auth_token']}
#     resp_status = requests.get('http://localhost:5051/auth/status', headers=headers)
#     resp_status_json = resp_status.json()
#     assert resp_status_json['user']['email'] == user_email
#     assert 'id' in resp_status_json['user']
#
#
# @pytest.mark.usefixtures('prepare_services')
# def test_user_status_fake_token():
#     user_email = 'Vasiya@gm.com'
#     password = 'pass'
#     resp_register = register_user(user_email, password)
#     assert 'user' in resp_register
#     assert 'auth_token' in resp_register
#
#     headers = {'Authorization': 'Bearer 123asd23asd23'}
#     resp_status = requests.get('http://localhost:5051/auth/status', headers=headers)
#     resp_status_json = resp_status.json()
#     assert resp_status_json['status'] == 'fail'


@pytest.mark.usefixtures('prepare_services')
def test_connect_send_message_ws():
    sio1 = connect_socket('Vasiya1@gm.com', 'pass1')
    sio2 = connect_socket('Vasiya2@gm.com', 'pass2')

    sio1.emit("join", {"room": "1"})
    sio2.emit("join", {"room": "1"})
    msgs1 = []
    msgs2 = []
    def message_handler_one(msg):
        logger.warning(f"1 {msg}")
        msgs1.append(msg)

    def message_handler_two(msg):
        logger.warning(f"2 {msg}")
        msgs2.append(msg)

    sio1.on('my_room_event', message_handler_one)
    sio2.on('my_room_event', message_handler_two)

    data_one = {
        "uuid": 1,
        "msg": "Hello Robert"
    }

    data_two = {
        "uuid": 2,
        "msg": "Hello Vasia"
    }
    sleep(2)
    sio1.emit("my_room_event", {"room": "1", "data": data_one})
    sio2.emit("my_room_event", {"room": "1", "data": data_two})
    sleep(10)
    msgs1.sort(key=lambda d: d["data"]["uuid"])
    msgs2.sort(key=lambda d: d["data"]["uuid"])
    assert msgs1 == msgs2
    assert len(msgs1) == 2
    assert msgs1[0]["data"]["uuid"] == 1
    assert msgs1[0]["data"]["msg"] == "Hello Robert"
    assert msgs1[1]["data"]["uuid"] == 2
    assert msgs1[1]["data"]["msg"] == "Hello Vasia"
    sio1.disconnect()
    sio2.disconnect()
