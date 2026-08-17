# TCP Networking Chat Application

## Project 2A & 2B — Computer Networking, University of Denver (Fall 2024)

A TCP-based client/server chat application written in Python. The project uses sockets and `poll()` to support communication between multiple clients and a server.

Clients can register with a username and one or more channels, send direct messages to other users, and send messages to channels. Messages are serialized using JSON before being transmitted over the TCP connection.

## Features

- TCP client/server communication
- Multiple connected clients
- Username registration
- Channel subscriptions
- Direct messaging between users
- Channel-based messaging
- JSON message serialization
- Non-blocking I/O using `poll()`
- Graceful client disconnection

## Requirements
- Python 3.x
- Python standard library modules: `socket`, `select`, `json`, and `queue`

## Running the Application

The server must be started before connecting any clients.

### 1. Start the server

Run:

```bash
python3 src/server.py <host> <port>
```

For example:

```bash
python3 src/server.py localhost 5000
```

### 2. Start a client

In a separate terminal, run:

```bash
python3 src/client.py <server-host> <port>
```

For example:

```bash
python3 src/client.py localhost 5000
```

Multiple clients can be started in separate terminals using the same server address and port.

## Registering a Client

Registration should be the first message sent by a client.

Enter a username followed by the channels you want to join:

```text
<username> <channel1> <channel2> ...
```

For example:

```text
Miranda networking music
```

This registers the client as `@Miranda` and subscribes them to the `#networking` and `#music` channels.

## Sending a Direct Message

To send a direct message to another user, enter `@` followed by their username and the message:

```text
@<username> <message>
```

For example:

```text
@Prospero O, brave new world!
```

## Sending a Channel Message

To send a message to a channel, enter `#` followed by the channel name and the message:

```text
#<channel> <message>
```

For example:

```text
#networking Hello, world!
```

The message will be sent to clients subscribed to that channel.

## Disconnecting

To disconnect from the server, enter:

```text
quit
```

The client sends a disconnect message to the server before closing the connection.

## Example Session

### Server

```bash
$ python3 src/server.py localhost 5000
```

### Client 1

```bash
$ python3 src/client.py localhost 5000

Miranda networking music
```

### Client 2

```bash
$ python3 src/client.py localhost 5000

Prospero networking
```

Client 1 can then send:

```text
@Prospero Hello!
```

or:

```text
#networking Hello, everyone!
```

## Project Structure

```text
.
├── src/
│   ├── server.py    # TCP server
│   └── client.py    # TCP client
└── README.md        # Project documentation
```

## Technical Overview

The application uses Python's TCP socket interface for reliable communication between clients and the server. The client uses `poll()` to monitor both the network socket and standard input, allowing it to receive server messages while simultaneously accepting user input.

Messages exchanged between the client and server are encoded as JSON objects and transmitted over the TCP connection.
