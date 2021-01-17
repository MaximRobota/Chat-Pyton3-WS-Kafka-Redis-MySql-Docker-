import os
import pytest
import requests
import socketio
import subprocess
from pathlib import Path
from loguru import logger
from time import sleep
import socketio.exceptions as sex

REPO_ROOT = Path(os.path.realpath(__file__)).parent.parent


@pytest.fixture
def prepare_services():
    # devnull so that there is not output
    subprocess.run(['docker-compose', 'down'], cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # subprocess.run(['docker-compose', 'down'], cwd=REPO_ROOT)
    build = subprocess.run(['docker-compose', 'build'], cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if build.returncode != 0:
        print("\n".join(list(map(lambda s: "Build stderr: "+s, build.stderr.decode().split("\n")))))
        raise Exception("Build failed")
    # subprocess.run(['docker-compose', 'build'], cwd=REPO_ROOT)
    # Popen instead of .run() so that we do not wait for the process to finish
    # -d is removed so that the output comes to the 'docker' variable
    #
    docker = subprocess.Popen(['docker-compose', 'up'], cwd=REPO_ROOT)
    # docker = subprocess.Popen(['docker-compose', 'up', 'websocket_service'], cwd=REPO_ROOT)
    for i in range(8):
        logger.info('Trying to get connection to a microservice')
        try:
            resp = requests.get('http://localhost:5052')
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

    logger.info("Established connection to microservice")
    subprocess.run(['docker-compose', 'ps'], cwd=REPO_ROOT)
    sleep(5)
    yield
    # subprocess.run(['docker-compose', 'ps'], cwd=REPO_ROOT)
    docker.kill()
    subprocess.run(['docker-compose', 'down'], cwd=REPO_ROOT)


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
    token = resp_login['auth_token']
    sio = connect_sio(token)
    assert sio.connected
    return sio


def connect_sio(token):
    host = 'http://localhost:5052'
    sio = socketio.Client()
    logger.info(f"Connecting to socket io on {host} with token: {token}")
    sio.connect(host, {'Authorization': 'Bearer ' + token})
    return sio


# @pytest.mark.usefixtures('prepare_services')
# def test_register():
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
        "state": 1,
        "msg": "Hello Robert"
    }

    data_two = {
        "state": 2,
        "msg": "Hello Vasia"
    }
    sleep(2)
    sio1.emit("my_room_event", {"room": "1", "data": data_one})
    # sio2.emit("my_room_event", {"room": "1", "data": data_two})
    sleep(15)
    # msgs1.sort(key=lambda d: d["data"]["state"])
    # msgs2.sort(key=lambda d: d["data"]["state"])
    # assert msgs1 == msgs2
    # assert len(msgs1) == 2
    # assert msgs1[0]["data"]["state"] == 1
    # assert msgs1[0]["data"]["msg"] == "Hello Robert"
    # assert msgs1[1]["data"]["state"] == 2
    # assert msgs1[1]["data"]["msg"] == "Hello Vasia"
    # assert "uuid" in msgs1[0]["data"]
    # assert "uuid" in msgs1[1]["data"]
    assert msgs1[0]["data"]["uuid"] == 3
    # assert msgs1[1]["data"]["uuid"] == 3
    sio1.disconnect()
    sio2.disconnect()


# @pytest.mark.usefixtures('prepare_services')
# def test_connect_sio_bad_token_does_not_connect():
#     with pytest.raises(sex.ConnectionError):
#         connect_sio("bad-token")
