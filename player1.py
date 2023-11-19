#!/usr/bin/env python
import uuid
import pika
import random
import json
import time


class Player1(object):

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

        self.board = None
        self.corr_id = None


    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            received_converted = json.loads(body)
            print(f'Received message from rpc: {received_converted}')


            self.board = received_converted
            player_move = self.random_place()
            player_move_json = json.dumps(player_move)

            print('Thinking about next move..')
            time.sleep(5)

            self.channel.basic_publish(
                            exchange='',
                            routing_key='Player 1',
                            body=player_move_json)
            print(" [x] Move published ")
        else:
            self.connection.close()

            

    def call(self):

        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_board_status',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body='Player1 requests board status')
        self.connection.process_data_events(time_limit=None)
    


    def possibilities(self):
        l = []
    
        for i in range(len(self.board)):
            for j in range(len(self.board)):
    
                if self.board[i][j] == 0:
                    l.append((i, j))
        return(l)
    

    def random_place(self):
        selection = self.possibilities()
        current_loc = random.choice(selection)
        return current_loc
        


# MAIN FUNCTION

player_1 = Player1()

print('Object player_1 created')


def on_response_player1(ch, method, props, body):
    print(json.loads(body))

    if str(json.loads(body)) == "It is your turn to play." :
        player_1.call()
    else:
        player_1.connection.close()
        connection.close()


connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='Turn_queue1', exclusive=False)

channel.basic_consume(
            queue='Turn_queue1',
            on_message_callback=on_response_player1,
            auto_ack=True)

player_1.call()
print('First rpc to start the game')

channel.start_consuming()