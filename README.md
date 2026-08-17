# Networking Chat Application

**Project 2A & 2B — Computer Networking, University of Denver (Fall 2024)**

A TCP client/server chat application written in Python. The project uses TCP sockets and `poll()` to support communication between multiple clients, with JSON used to serialize messages. Clients can register with a username and subscribe to channels, send direct messages to other users, and communicate through shared channels.

## Features

* TCP client/server communication
* Multiple simultaneous clients
* Username registration
* Channel subscriptions
* Direct messaging between users
* Channel-based messaging
* JSON message serialization
* I/O multiplexing with `poll()`
* Graceful client disconnection

## Requirements

* Python 3.x
* No third-party Python packages are required.

The project uses modules from the Python standard library, including `socket`, `select`, `json`, and `queue`.

## Project Structure

```text
.
├── src/
│   ├── server.py    # TCP server
│   └── client.py    # TCP client
└── README.md        # Project documentation
```

## Running the Application

The server must be started before connecting any clients.

### 1. Start the Server

From the project root, run:

```bash
python3 src/server.py <host> <port>
```

For local development:

```bash
python3 src/server.py localhost 5000
```

### 2. Start a Client

Open a new terminal and run:

```bash
python3 src/client.py <server-host> <port>
```

For example:

```bash
python3 src/client.py localhost 5000
```

Additional clients can be started in separate terminals using the same server address and port.

## Registering a Client

After starting a client, the first message should register the client with a username and one or more channels.

Use the following format:

```text
<username> <channel1> <channel2> ...
```

For example:

```text
Miranda networking music
```

This registers the client as `@Miranda` and subscribes them to:

* `#networking`
* `#music`

## Sending Direct Messages

To send a direct message to another user, enter `@` followed by their username and the message:

```text
@<username> <message>
```

For example:

```text
@Prospero Hello!
```

The message will be delivered directly to `@Prospero`.

## Sending Channel Messages

To send a message to a channel, enter `#` followed by the channel name and the message:

```text
#<channel> <message>
```

For example:

```text
#networking Hello, everyone!
```

The message will be delivered to users who are subscribed to that channel.

## Example

Start the server:

```bash
python3 src/server.py localhost 5000
```

Then start two clients in separate terminals.

### Client 1

```bash
python3 src/client.py localhost 5000
```

Register:

```text
Miranda networking music
```

### Client 2

```bash
python3 src/client.py localhost 5000
```

Register:

```text
Prospero networking
```

Miranda can then send a channel message:

```text
#networking Hello, Prospero!
```

Or send Prospero a direct message:

```text
@Prospero Hello!
```

## Disconnecting

To disconnect a client, enter:

```text
quit
```

The client will send a disconnect request to the server before closing its connection.

## Technical Overview

The application uses TCP sockets to establish reliable communication between the server and connected clients.

The server uses `poll()` to monitor multiple sockets for incoming data and outgoing messages without blocking on a single client. Each connected client has an associated message queue for managing messages waiting to be sent.

Messages between the client and server are represented as JSON objects. The client sends connection, message, and disconnect requests, while the server routes messages to the appropriate users or channels.

## Academic Context

This project was developed as **Project 2A & 2B for Computer Networking at the University of Denver in Fall 2024**.
