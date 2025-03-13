from flask import Flask, render_template
from flask_socketio import SocketIO, join_room, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

@app.route("/")
def index():
    return render_template("index.html")

def check_winner(board):
    """بررسی برنده شدن"""
    winning_positions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    
    for pos in winning_positions:
        if board[pos[0]] == board[pos[1]] == board[pos[2]] and board[pos[0]] != "":
            return board[pos[0]]
    if "" not in board:
        return "draw"
    return None

@socketio.on("join")
def handle_join(data):
    room = data["room"]
    player = data["player"]

    if room not in rooms:
        rooms[room] = {"board": [""] * 9, "players": [], "turn": "X", "restart_votes": 0}

    if len(rooms[room]["players"]) < 2 and player not in rooms[room]["players"]:
        rooms[room]["players"].append(player)
        join_room(room)
        emit("update_board", rooms[room], room=room)

@socketio.on("move")
def handle_move(data):
    room = data["room"]
    index = data["index"]
    
    if room in rooms and rooms[room]["board"][index] == "" and len(rooms[room]["players"]) == 2:
        current_turn = rooms[room]["turn"]
        
        rooms[room]["board"][index] = current_turn
        winner = check_winner(rooms[room]["board"])
        
        if winner:
            emit("game_over", {"winner": winner}, room=room)
        else:
            rooms[room]["turn"] = "O" if current_turn == "X" else "X"
        
        emit("update_board", rooms[room], room=room)

@socketio.on("restart")
def handle_restart(data):
    room = data["room"]
    if room in rooms:
        rooms[room]["restart_votes"] += 1

        if rooms[room]["restart_votes"] == 2:  # وقتی هر دو بازیکن دکمه شروع مجدد را زدند
            rooms[room]["board"] = [""] * 9
            rooms[room]["turn"] = "X"
            rooms[room]["restart_votes"] = 0
            emit("update_board", rooms[room], room=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)
