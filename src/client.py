import json
import sys
from socket import socket, SOCK_STREAM, AF_INET
from select import poll, POLLIN, POLLOUT, POLLERR, POLLHUP

# Register user: <user_name> <channel1> <channel2> ... : Miranda networking music
# Send direct message: @<user_name> <message> : @Prospero O, brave new world!
# Send message to channel: #<channel_name> <message> : #networking Hello, world!

def check_poll_results(ready, socket, event):
	for ready_socket, ready_event in ready:
		if ready_socket == socket.fileno() and (ready_event & event) == event:
			return True
	return False

def print_error(e, f="UNKNOWN"):
	print("Error in %s!" % (f))
	print(e)
	print(type(e))

def send_data(tcp_sock, data):
	try:
		ret = tcp_sock.send(bytes(data, 'utf-8'))
	except KeyboardInterrupt as k:
		raise KeyboardInterrupt()
	except Exception as e:
		print_error(e, "send")
	except json.JSONDecodeError as j:
		print_error(j, "send")

def recv_data(tcp_sock, user_name, targets):
	try:
		data = tcp_sock.recv(4096)
		if len(data) == 0:
			return False
		display_messages(json.loads(data.decode("utf-8")), user_name, targets)
		return True
	except Exception as e:
		print_error(e, "recv")

def display_messages(chat_history, user_name, channels):
	if chat_history["status"] == "disconnect":
		print("Server has disconnected")
		sys.exit(1)
	if chat_history["status"] == "error":
		print("ERROR: " + chat_history["message"])
		return
	# This part performs direct messaging and displaying all chat history
	if chat_history["status"] == "chat":
		# Otherwise, display the message history 
		message_history = chat_history["history"]
		for message in message_history:
			print(message)

		for message in message_history:
			# Get who the message is destined for 
			target = message["target"]
			# Get who the message is from 
			from_user = message["from"]
			# Get the message
			msg = message["message"]
			# Print the message if it is addressed to the user
			if target == user_name:
				print("DIRECT MESSAGE")
				print(from_user + ": " + msg)
			elif target[0] == "#" and target in channels:
				print("CHANNEL MESSAGE")
				print(target + ": " + msg)
		

def create_connect_message(action, user_name, targets) -> str:
	"""
	Creates the connect message to send to the server
	"""
	msg = {}
	msg["action"] = action
	msg["user_name"] = user_name
	msg["targets"] = targets

	# We don't have to account for the message field in this case because we are just
	# establishing the initial connection
	if action == "connect":
		return json.dumps(msg)

def create_client_message(user_name, target, message) -> str:
	"""
	This function will create a direct message to a user or a message to a channel
	"""
	msg = {}
	# Action is always message in this case 
	msg["action"] = "message"
	# User doesn't have to type @ symbol 
	msg["user_name"] = user_name
	msg["target"] = target
	msg["message"] = message

	return json.dumps(msg)

def create_disconnect_message() -> str:
	msg = {}
	msg["action"] = "disconnect"
	return msg

def main():
	# Primarily adapted from the given in-class code
	if len(sys.argv) >= 3:
		ip = sys.argv[1]
		try:
			port = int(sys.argv[2])
		except:
			print("Port %s unable to be converted to number, run with HOST PORT" % (sys.argv[2]))
			sys.exit(1)

	# Create socket to connect to the server
	try:
		tcp_sock = socket(AF_INET, SOCK_STREAM)
	except Exception as e:
		print_error(e, "socket")

	# Create poll object
	poller = poll()

	# Attempt to connect to server
	try:
		tcp_sock.connect((ip, port))
	except Exception as e:
		print_error(e, "connect")

	# We're using select, so set socket to non-blocking just in case
	
	# Add client (tcp_sock) and stdin to list of read FDs
	poller.register(tcp_sock, POLLIN)
	poller.register(sys.stdin, POLLIN)
	user_name = ""
	targets = None
	data = ""
	data_to_send = None
	try:
		while data != 'quit':
			poller.register(tcp_sock, POLLIN)
			write_sockets = []
			if data_to_send is not None: # only check if we have data to actually send!
				poller.register(tcp_sock, POLLOUT)
			try:
				poll_ready_fds = poller.poll(1000)
			except KeyboardInterrupt as e:
				print("Got keyboard kill")
				data = 'quit'
                # Send the quit message to the server
				quit_msg = create_disconnect_message()
				try:
					send_data(tcp_sock, json.dumps(quit_msg))
					print("sent quit message")
				except Exception as e:
					print_error(e, "send_data")

			try:
				if check_poll_results(poll_ready_fds, tcp_sock, POLLIN):
					if not recv_data(tcp_sock, user_name, targets):
						print("Server went away, shutting down.")
						data = 'quit'

				if check_poll_results(poll_ready_fds, tcp_sock, POLLERR):
					print("Server went away, shutting down.")
					data = 'quit'

				if data_to_send != None and check_poll_results(poll_ready_fds, tcp_sock, POLLOUT):
					# now we are _sure_ it's okay to send the data
					send_data(tcp_sock, data_to_send)
					data_to_send = None
					# Have to unregister and re-register so we don't end up in an infinite loop of POLLOUT
					poller.unregister(tcp_sock)
					poller.register(tcp_sock, POLLIN)
				if check_poll_results(poll_ready_fds, sys.stdin, POLLIN):
					data = sys.stdin.readline().strip()
					# Split the data into a list 
					data_list = data.split(" ")
					if data != 'quit':
						# If the first character is an @ symbol, then we are sending a direct message
						msg = data.replace(data_list[0], "").strip()
						# get length of message
						encoded_msg = msg.encode("utf-8")
						byte_len = len(encoded_msg)
						if byte_len > 3800:
							print("Message too long")
							continue
						if data_list[0][0] == "@" and user_name != "": 
							json_client_msg_str = create_client_message(user_name, data_list[0], data.replace(data_list[0], "").strip())
							data_to_send = json_client_msg_str
						# Channel message
						elif data_list[0][0] == "#" and user_name != "":
							json_client_msg_str = create_client_message(user_name, data_list[0], data.replace(data_list[0], "").strip())
							data_to_send = json_client_msg_str
						# Connect message otherwise
						else:
							# Then we are registering the client
							# If the length in bytes of user name plus the at symbol is greater than 60, then we have an error
							user_name = "@" + data_list[0]
							encoded_str = user_name.encode("utf-8")
							byte_len = len(encoded_str)
							if byte_len > 60:
								print("Username too long")
								continue
							print(user_name)
							targets = ["#" + target for target in data_list[1:]]
							for target in targets:
								encoded_str = target.encode("utf-8")
								byte_len = len(encoded_str)
								if byte_len > 60:
									print("Channel name too long")
									continue
							json_connect_msg_str = create_connect_message("connect", user_name, targets)
							print(json_connect_msg_str)
							data_to_send = json_connect_msg_str
					else:
						print("Got client quit.")
						# Send the quit message to the server
						quit_msg = create_disconnect_message()
						print(quit_msg)
						try:
							send_data(tcp_sock, json.dumps(quit_msg))
						except Exception as e:
							print_error(e, "send_data")
						sys.exit(1)

			except KeyboardInterrupt as e:
				data = 'quit'
				print("Got keyboard kill")
				# Send the quit message to the server
				quit_msg = create_disconnect_message()
				print(quit_msg)
				try:
					send_data(tcp_sock, json.dumps(quit_msg))
				except Exception as e:
					print_error(e, "send_data")
				
	except Exception as e:
		print_error(e, "send_data")

	finally:
		tcp_sock.close()

if __name__ == "__main__":
	main()
