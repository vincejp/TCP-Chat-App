import sys
from socket import socket, SOCK_STREAM, AF_INET
from select import poll, POLLIN, POLLOUT, POLLHUP, POLLERR
import traceback
import queue
import json

def print_error(e, f="UNKNOWN"):
	print("Error in %s!" % (f))
	print(e)
	print(type(e))

def recv_data(tcp_sock):
	"""
	Returns the JSON array converted from a string
	Basically returns...the data!
	If no data or error, returns None
	"""
	# TODO: Impose limits on data sizes in main 
	try:
		data = tcp_sock.recv(4096)
		# Indicates client has disconnected
		if len(data) == 0:
			return None
		d = data.decode('utf-8')
		data_string = json.loads(d)
		# Return the data string if nothing went wrong 
		return data_string
	except BlockingIOError as b:
		print("Recv failed due to non-blocking IO, this means the client has disconnected?")
		return None
	except Exception as e:
		print("Error in recv")
		return None

def check_poll_results(ready, socket, event):
	for ready_socket, ready_event in ready:
		if ready_socket == socket.fileno() and (ready_event & event) == event:
			return True
	return False

def main():
	# Get the IP and hostname to run the server on
	ip = ""
	port = 0
	
	if len(sys.argv) >= 3:
		ip = sys.argv[1]
		try:
			port = int(sys.argv[2])
		except:
			print("Port %s unable to be converted to number, run with HOST PORT" % (sys.argv[2]))
			sys.exit(1)
			
	# Open a TCP connection with the client
	# This is the server socket 
	try:
		server_socket = socket(AF_INET, SOCK_STREAM)
	except:
		print("Error opening socket")
		sys.exit(1)
	
	# Bind it to a port 
	try:
		server_socket.bind((ip,port))
	except Exception as e:
		print_error(e)
		sys.exit(1)

	# Listen enables a server to accept connections
	try:
		server_socket.listen()
	except:
		print("Error in listen")
		sys.exit(1)

	# Maintain a list of connected clients 
	connected = []
	# Register the poller
	poller = poll()
	poller.register(server_socket, POLLIN)
	msg_history = {"status": "chat", "history": []}
	# Keep queues of messages destined for each client 
	msg_queues = []
	# {"@Miranda":["#networking", "#music"]}
	users = {}
	# Map username to the socket it has been assigned
	user_sockets = {}
	try:
		while True:
			print(user_sockets)
			try:
				# Poll for 2 seconds(2000 ms)
				poll_ready_fds = poller.poll(2 * 1000)
			except KeyboardInterrupt as k:
				print("Got keyboard interrupt")
				sys.exit(1)
			except Exception as e:
				sys.exit("Error in poll")

			# If a new client has connected, add the connection to the list of connections
			if check_poll_results(poll_ready_fds, server_socket, POLLIN):
				try:
					client_sock, (client_ip, client_port) = server_socket.accept()
					# Set to non-blocking so multiple connections can be handled at the same time 
					client_sock.setblocking(0)
					# Allow data to be read from the socket
					poller.register(client_sock, POLLIN)
					connected.append(client_sock)
					# Additionally, add a new message queue to the message queues 
					msg_queues.append(queue.Queue())
				except KeyboardInterrupt as k:
					print("Got keyboard interrupt")
					# Send a disconnect message to the client
					sys.exit(1)
				except Exception as e:
					print("Got error in accept")
					sys.exit(1)

			for client in connected:
				# If the client sent us data 
				if check_poll_results(poll_ready_fds, client, POLLIN):
					try:
						index_of_client = connected.index(client)
						ret = recv_data(client)
						if not ret:
							print("Closing client")
							# Remove the queue of messages too 
							poller.unregister(client)
							client.close()
							connected.remove(client)
							msg_queues.pop(index_of_client)
							# Remove the user from the list of users
							# Also remove the user from the list of users
							
							# We have received data fromt the client successfully so we need to check if this is a connect message
							# TODO: Check for malformed JSON and other errors
							continue

						if ret["action"] == "connect":
							# If this is a connection request, register the user and store their name and targets in a dictionary with the key as the user name(with @ symbol)
							# print the list of users for testing purposes 
							user = ret["user_name"]
							targets = ret["targets"]
							users[user] = targets
							user_sockets[user] = client
						elif ret["action"] == "message":
							# Add message to the message queue 
							# Queue up the message at the specific message queue in the list of message queues(wow) 
							msg_queues[index_of_client].put(ret)
							# Client isn't ready to receive data yet, so we will wait to put the message into the table until that occurs
							poller.unregister(client)
							poller.register(client, POLLOUT)

						elif ret["action"] == "disconnect":
							# Remove the client from the active clients list and remove from the message queue
							poller.unregister(client)
							connected.remove(client)
							msg_queues.pop(index_of_client)
							username = [user for user, sock in user_sockets.items() if sock == client]
							if username:
								del user_sockets[username[0]]
							# Remove user from list of users
							print("Removing user %s" % (ret["user_name"]))
							del users[ret["user_name"]]
					except Exception as e:
						print("Client shut down")
						# remove the client from the list of connected clients

				# If the client socket is ready to send data
				if check_poll_results(poll_ready_fds, client, POLLOUT):
					# Get the most recent message from the specific message queue 
					index_of_client = connected.index(client)
					if not msg_queues[index_of_client].empty():
						try:
							msg = msg_queues[index_of_client].get()
							user_name = msg["user_name"]
							target = msg["target"]
							message = msg["message"]
							chat_entry = {"target": target, "from": user_name, "message": message}
							msg_history["history"].append(chat_entry)

							if target.startswith("#"):
								# Broadcast to ALL users in the target channel except the sender
								for user, targets in users.items():
									if target in targets and user in user_sockets:
										if user != user_name:
											json_msg_history = json.dumps({"status": "chat", "history": [chat_entry]})
											user_sockets[user].send(json_msg_history.encode('utf-8'))

							elif target in user_sockets:
								# Direct message to specific user
								json_msg_history = json.dumps({"status": "chat", "history": [chat_entry]})
								user_sockets[target].send(json_msg_history.encode('utf-8'))
							# Reset the client to receive data again so we don't get stuck!
							poller.unregister(client)
							poller.register(client, POLLIN)
						except Exception as e:
							print_error(e, "send_data")
							poller.unregister
							connected.remove(client)
							msg_queues.pop(index_of_client)

	except KeyboardInterrupt as k:
		print("Got keyboard interrupt")
		sys.exit(1)
	except Exception as e:
		print_error(e, "main")
		sys.exit(1)
	finally:
		# Close all the sockets and send a disconnect message to all clients
		for client in connected:
			quit_msg = {"status": "disconnect"}
			try:
				client.send(json.dumps(quit_msg).encode('utf-8'))
			except Exception as e:
				print_error(e, "Sending shutdown message")
			finally:
				client.close()
		server_socket.close()

if __name__ == "__main__":
    main()
