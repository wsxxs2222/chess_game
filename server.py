import socket
import random
import time
FORMAT = "utf-8"

def host_game(connection_sockets, game_mode):
    # tell the second clients the game mode
    connection_sockets[1].send(game_mode.encode(FORMAT))
    time.sleep(1)
    choice = random.choice([0, 1])
    if choice == 0:
        color0 = 'w'
        color1 = 'b'
        turn = 0
    else:
        color0 = 'b'
        color1 = 'w'
        turn = 1
    # send message to clients about their assigned colors
    connection_sockets[0].send(color0.encode(FORMAT))
    connection_sockets[1].send(color1.encode(FORMAT))
    print(f"assigned color {color0} to p0")
    # game loop
    run = True
    while run:
        message = connection_sockets[turn].recv(1024).decode(FORMAT)
        if message:
            message_list = message.split(",")
            # parse the message, first represent move, second represent game status
            # send the move to the other player
            connection_sockets[(turn + 1) % 2].send((message_list[0]+","+message_list[1]+","+message_list[2]).encode())
        
            # terminate the game
            if message_list[3] == "end":
                run = False
                connection_sockets[0].close()
                connection_sockets[1].close()
                print("game_ended")
            # switch turn
            turn = (turn + 1) % 2
    pass

def main():
    # set up host and port
    # HOST = '172.30.108.165'
    HOST = '172.26.28.223'
    PORT = 9090
    # create a socket for the server
    # specify socket type and protocal
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # bind the server to ip and port
    server.bind((HOST, PORT))
    server.listen()
    while True:
        connection_socket0, address0 = server.accept()
        print("accepted connection from p0")
        connection_socket0.send("select_mode".encode(FORMAT))
        print("p0 selecting mode")
        game_mode = connection_socket0.recv(64).decode(FORMAT)
        print(f"mode selected is {game_mode}")
        connection_socket1, address1 = server.accept()
        print("accepted connection from p1")
        connection_sockets = [connection_socket0, connection_socket1]
        time.sleep(1)
        host_game(connection_sockets, game_mode)
    server.close()
    
if __name__ == "__main__":
    main()