# FrameReject
CS5340 2022 Project.

## Game Client/Server
### How it Works
![Game Loop](./imgs/game_loop.png)
The Game Client/Server interaction is implemented as above. Client will receive user input at every time step, and consequently send the request for frames to the Server. Once Server sends the frames and Client receives it, showing the frames to the player will be done at the nearest timestep from when the frames arrive.

### Requirements
- `pip install pygame`
- `pip install ale_py`

### Using the Game Client/Server
Example Server Command (Run this first)
```
python3 base_game_server.py --main_port 10500 --input_port 10501
```

Example Client Command
```
python3 base_game_client.py --server_address '0.0.0.0' --main_port 10500 --input_port 10501 --frame_delay_ms 0
```
