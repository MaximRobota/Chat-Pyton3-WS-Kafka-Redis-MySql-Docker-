#!/usr/bin/env python
import logging
import time

import requests
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, rooms
from kafka_util import create_topic, create_producer, OUTBOUND_TOPIC_NAME, create_consumer, INBOUND_TOPIC_NAME
from loguru import logger
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

@app.route("/")
def index():
    return "OK !"


@socketio.on('connect')
def connect():
    app.logger.info("Connected!")
    auth = request.headers['Authorization']
    headers = {'Authorization': auth}
    app.logger.info(f"Auth {auth}")
    resp_status = requests.get(
        'http://identity-service:80/auth/status',
        headers=headers
    )
    if resp_status.status_code != 200:
        return False
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('join')
def join(message):
    join_room(message['room'])
    emit('my_response',
         {'data': 'In rooms: ' + ', '.join(rooms())})


@socketio.on('my_room_event')
def send_room_message(message):
    logger.info(f"Got message from websocket {message}")

    consumer = create_consumer()

    create_producer().send(OUTBOUND_TOPIC_NAME, message)

    logger.info(f"Sent message to kafka on topic {OUTBOUND_TOPIC_NAME!r} {message}")

    for msg in consumer:
        # data = next(consumer)
        data = msg.value
        logger.info(f"Got persisted message from kafka on topic {INBOUND_TOPIC_NAME!r} {data}")
        emit(
            'my_room_event',
            data,
            room=message['room']
        )
        logger.info(f"Sent persisted message to WS client topic 'my_room_event'")
        break


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    create_topic()
    socketio.run(app, host='0.0.0.0', port=80, debug=True, use_reloader=False)
