import pika, json
import numpy as np


def create_board():
    return(np.array([[0, 0, 0],
                     [0, 0, 0],
                     [0, 0, 0]]))

#Update board by addding the player's move
def update_board(player_move,player):
    board[player_move[0],player_move[1]] = player



#Checks whether the player has three
# of their marks in a horizontal row
 
def row_win(board, player):
    for x in range(len(board)):
        win = True
 
        for y in range(len(board)):
            if board[x, y] != player:
                win = False
                continue
 
        if win == True:
            return(win)
    return(win)

# Checks whether the player has three
# of their marks in a vertical row

def col_win(board, player):
    for x in range(len(board)):
        win = True
 
        for y in range(len(board)):
            if board[y][x] != player:
                win = False
                continue
 
        if win == True:
            return(win)
    return(win)
 

# Checks whether the player has three
# of their marks in a diagonal row
 
def diag_win(board, player):
    win = True
    y = 0
    for x in range(len(board)):
        if board[x, x] != player:
            win = False
    if win:
        return win
    win = True
    if win:
        for x in range(len(board)):
            y = len(board) - 1 - x
            if board[x, y] != player:
                win = False
    return win
 
# Evaluates whether there is
# a winner or a tie
 
 
def evaluate(board):
    winner = 0
 
    for player in [1, 2]:
        if (row_win(board, player) or
                col_win(board, player) or
                diag_win(board, player)):
 
            winner = player
 
    if np.all(board != 0) and winner == 0:
        winner = -1
    return winner



# ======CALLBACK FUNCTION FOR RECEIVED MESSAGES========

def on_request(ch, method, properties, body):


    # RECOGNISE IF PLAYER REQUESTS BOARD STATUS OR PUBLISHED GAME COMMANDS AND ACT ACCORDINGLY:
    if method.routing_key == 'rpc_board_status':

        print(f"Received Request: {properties.correlation_id}")
        print(f"Received RPC message: {body}")
        # Handle requests for board status
        board_status = board.tolist()
        board_status = json.dumps(board_status)

        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=board_status
        )
        # ch.basic_ack(delivery_tag=method.delivery_tag)
        print('Board status sent.')
    else:

        body_converted = json.loads(body)
        print(f"Received message: {body_converted}")

        # Handle player moves and update the game state
        player_name = method.routing_key
        print(f'Move published by {player_name}')

        # Your game logic to process player moves and update the board
        if player_name == "Player 1" :
            update_board(body_converted, 1)
            print(board)
        else:
            update_board(body_converted, 2)
            print(board)
        
        winner = evaluate(board)
        print(f'Player {winner} has won the game')

        match winner:
            case 1:
                message = 'Player 1 has won the game.'
                message_json = json.dumps(message)

                ch.basic_publish(
                    exchange='',
                    routing_key='Turn_queue1',
                    body=message_json
                )
                ch.basic_publish(
                    exchange='',
                    routing_key='Turn_queue2',
                    body=message_json
                )
                connection.close()

            case 2:
                message = 'Player 2 has won the game.'
                message_json = json.dumps(message)

                ch.basic_publish(
                    exchange='',
                    routing_key='Turn_queue1',
                    body=message_json
                )
                ch.basic_publish(
                    exchange='',
                    routing_key='Turn_queue2',
                    body=message_json
                )
                connection.close()

            case -1:
                message = 'The game ended as a draw.'
                message_json = json.dumps(message)
            
                ch.basic_publish(
                    exchange='',
                    routing_key='Turn_queue1',
                    body=message_json
                )
                ch.basic_publish(
                    exchange='',
                    routing_key='Turn_queue2',
                    body=message_json
                )
                connection.close()

            case 0:
                # Determine the next player
                next_player = "Turn_queue2" if player_name == "Player 1" else "Turn_queue1"
                print(next_player)
                message = 'It is your turn to play.'
                message_json = json.dumps(message)

                # Send a message to the next player to indicate their turn
                ch.basic_publish(
                    exchange='',
                    routing_key=next_player,
                    body=message_json
                )
                print('Message for turn sent')


#======================================================

# =======CHANNEL CONFIGURATIONS========

connection_parameters = pika.ConnectionParameters('localhost')

connection = pika.BlockingConnection(connection_parameters)

channel = connection.channel()


# Create named queues for players and the board status
channel.queue_declare(queue='Player 1', exclusive=False)
channel.queue_declare(queue='Player 2', exclusive=False)
channel.queue_declare(queue='rpc_board_status', exclusive=True)
channel.queue_declare(queue='Turn_queue2', exclusive=False)

channel.basic_qos(prefetch_count=1)

# Set up consumers for player queues and the board status
channel.basic_consume(queue='Player 1', on_message_callback=on_request, auto_ack=True)
channel.basic_consume(queue='Player 2', on_message_callback=on_request, auto_ack=True)
channel.basic_consume(queue='rpc_board_status', on_message_callback=on_request, auto_ack=True)

#========================================

print("Starting Server")

board = create_board()


channel.start_consuming()
