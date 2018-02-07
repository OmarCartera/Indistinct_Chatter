#/******************************
# *     Author: Omar Gamal     *
# *   c.omargamal@gmail.com    *
# *                            *
# *     Language: Python       *
# *                            *
# *         15/1/2018          *
# *                            *
# *      TCP Multi-Client      *
# *      Chat Application      *
# ******************************/

#!/usr/bin/env python
###########################################
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QThread, SIGNAL

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import loadUiType

# import design.py for GUI things
import design
import sys

# to open files and sleep()
import os
import time

#socket things
import socket
from thread import *

# to play sound files
import pygame

# wireless part
from wireless import Wireless

import platform

if(platform.system() == 'Linux'):
	from gi.repository import Notify, GdkPixbuf

# progress bar GUI thread
class progress_bar_thread(QtCore.QThread):
	def __init__(self):
		super(progress_bar_thread, self).__init__()

	# call the function that updates the bar from the secondary thread
	def run(self):
		self.emit(SIGNAL('update_progress_bar()'))




# main GUI class
class mainApp(QtGui.QMainWindow, design.Ui_MainWindow):
	def __init__(self):
		super(mainApp, self).__init__()
		self.setupUi(self)

		# GUI thread things
		self.progress_bar_thread = progress_bar_thread()
		self.connect(self.progress_bar_thread, SIGNAL('update_progress_bar()'), self.update_progress_bar)
		

		# starting pygame
		pygame.init()

		# initialize notification object
		if(platform.system() == 'Linux'):
			Notify.init('indistinct chatter')
			self.bubble = Notify.Notification.new('!', '?')
			image = GdkPixbuf.Pixbuf.new_from_file('egg.png')
			self.bubble.set_icon_from_pixbuf(image)

		# flag to tell if this host is a server
		self.isServer = False

		# data received from clients
		self.data = ['.', '.']

		# ip and connection info about chat clients
		self.addr_list = []
		self.conn_list = []

		# clients counter: chat client i .. media client j
		self.i = 0
		self.j = 0

		# setting text color for 'is typing...', chat area and error label
		self.lbl_typing.setStyleSheet("color: rgb(170, 0, 0)")
		self.txt_chat.setTextColor(QColor(50, 50, 50))
		self.lbl_error.setStyleSheet("color: rgb(255, 0, 0)")

		# connecting the GUI objects to their methods
		self.lndt_host.setFocus(True)

		try:
			wireless = Wireless()

			if (wireless.current() == 'RUN'):
				self.lndt_host.setText('192.168.1.')

			else:
				self.lndt_host.setText('172.28.130.')

		except:
			self.lndt_host.setText('172.28.130.')


		self.btn_send.clicked.connect(self.send_chat)
		self.btn_server.clicked.connect(self.server_conn)
		self.btn_client.clicked.connect(self.client_conn)
		self.btn_attach.clicked.connect(self.attach_file)

		# press enter to send a message instead of clicking send button
		self.lndt_msg.returnPressed.connect(self.send_chat)

		# press enter to connect as a client to the given server
		self.lndt_host.returnPressed.connect(self.client_conn)

		# send the 'I am typing' signal whenever the msg box text changes
		self.lndt_msg.textChanged.connect(self.typing_notification)

		# setting the chat socket connection parameters
		self.host = ''
		self.port = 5557

		# establishing a TCP connection for the chat server
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# this line allows re-using the same socket even if it was closed improperly
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


		################
		## media part ##
		################

		# ip and connection info about media clients
		self.media_addr_list = []
		self.media_conn_list = []

		# setting the media socket connection parameters
		self.media_host = ''
		self.media_port = 3245

		# establishing a TCP connection for the media server
		self.media_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		# this line allows re-using the same socket even if it was closed improperly
		self.media_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)




	# sending messages to the chat room
	def send_chat(self):
		if (self.lndt_msg.text() == ''):
			# set the chat box borders to red if sending blank
			self.lndt_msg.setStyleSheet("border: 1px solid red")

		else:
			# set the chat box borders to grey if sending anything other than blank
			self.lndt_msg.setStyleSheet("border: 1px solid grey")

			# try sending to every client in the room
			# clients only send to the server,
			# while the server sends to all clients
			for i in range(len(self.conn_list)):
				# every packet I send is in the form (my_computer_name`my_msg)
				# getfqdn() gets my computer name
				self.conn_list[i].send(socket.getfqdn() + '`' + str(self.lndt_msg.text()))
			
			# setting Your message clolr to RED
			self.txt_chat.setTextColor(QColor(200, 0, 0))
			self.txt_chat.append('You: ' + self.lndt_msg.text())

			# scroll down the chat box to the end after every appending
			self.txt_chat.moveCursor(QtGui.QTextCursor.End)

			# setting the color back to BLACK
			self.txt_chat.setTextColor(QColor(50, 50, 50))

			# send the 'I finished typing' signal
			self.conn_list[0].send(socket.getfqdn() + '`' + 'typn-')

			# clear the message box
			self.lndt_msg.clear()



	# when this host is the server
	def server_conn(self):
		# raising the server flag
		self.isServer = True

		self.lndt_msg.setFocus(True)
		self.lndt_host.clear()

		# starting a thread to keep listening to any connecting client
		# threaded to work in the background without interrupting the main thread
		start_new_thread(self.threaded_server, ())
		start_new_thread(self.media_server, ())


	# when this host is the server brdo
	def media_server(self):
		while True:
			try:
				# creating a media server at the given port
				self.media_s.bind((self.media_host,self.media_port))
			
			except socket.error:
				pass


			self.media_s.listen(10)

			print('Waiting for Media...')

			# accept the incoming media clients connection request
			self.med_conn, self.med_addr = self.media_s.accept()

			# get the IP of this client
			self.med_addr = self.med_addr[0]

			# append the new client's IP and connection to their lists
			self.media_addr_list.append(self.med_addr)
			self.media_conn_list.append(self.med_conn)

			print('Media connected to: ' + self.med_addr)

			# if this is the first client
			if (self.j == 0):
				# run the first client thread
				start_new_thread(self.media_client_1, ())

			# if this is the second client
			elif (self.j == 1):
				# run another thread for the second client
				start_new_thread(self.media_client_2, ())

			# increment the number of connecting clients
			self.j += 1




	# server thread
	def threaded_server(self):
		while True:
			try:
				# creating a chat server at the given port
				self.s.bind((self.host, self.port))

			except socket.error:
				pass


			self.s.listen(5)
			print('Waiting for connection...')

			try:
				# accept the incoming clients connection request
				self.conn, self.addr = self.s.accept()

				# get the IP of this client
				self.addr = self.addr[0]

				# append the new client's IP and connection to their lists
				self.addr_list.append(self.addr)
				self.conn_list.append(self.conn)

				self.txt_online.append(self.addr)


				print('Connected to:' + self.addr)

				print self.addr_list
				print self.conn_list

				# if this is the first client
				if(self.i == 0):
					# run the first client thread
					start_new_thread(self.threaded_client_1, (self.conn_list[0],))

				# if this is the second client
				elif(self.i == 1):
					# run another thread for the second client
					start_new_thread(self.threaded_client_2, (self.conn_list[1],))

				# increment the number of connecting clients
				self.i += 1


			except KeyboardInterrupt:
				if self.conn:
					self.conn.close()



	# if this host is a client
	def client_conn(self):
		if (self.lndt_host.text() == ''):
			# setting host ip box borders to red if blank
			self.lndt_host.setStyleSheet("border: 1px solid red")

		else:
			try:
				# setting host ip box borders to grey if not blank
				self.lndt_host.setStyleSheet("border: 1px solid grey")

				# give it the server host IP, connect to it
				self.host = str(self.lndt_host.text())
				self.s.connect((self.host, self.port))
				self.conn = self.s
				self.conn_list.append(self.conn)

				# run a client thread to receive chat messages from the server
				start_new_thread(self.threaded_client_1, (self.conn,))

				# give it the server host IP, connect to it 'media things'
				self.media_host = str(self.lndt_host.text())
				self.media_s.connect((self.media_host, self.media_port))
				self.media_conn = self.media_s
				self.media_conn_list.append(self.media_conn)

				# run a client thread to receive media from the server
				start_new_thread(self.media_client_1, ())
				self.lbl_error.clear()
				self.lndt_msg.setFocus(True)

			except socket.error:
				self.lbl_error.setText("No server at this IP!")



	# method to listen to incoming media from the first client/sender
	def media_client_1(self):
		while True:
			# waiting for a media file to be sent
			print 'Waiting for a file'

			# receive whatever is being sent by the first sender
			self.media_data = self.media_conn_list[0].recv(2048)
			print self.media_data

			try:
				# take the string before the ` --> the sender name
				self.media_sender = self.media_data[:self.media_data.index('`')]
				# take the string between ` and | --> media file name
				self.filename = self.media_data[self.media_data.index('`')+1:self.media_data.index('|')]
				# take the string after | --> integer representing media file size
				self.filesize = int(self.media_data[self.media_data.index('|')+1:])

				# if the sender isn't me
				if (self.media_sender != socket.getfqdn()):
					# if you are the server
					if (self.isServer):
						# you must accept whatever data is coming
						# to broadcast it to all the connectd clients
						self.media_response = 'y'

					# if you are a client
					else:
						# you have the freedom to either accept or reject the incoming media file
						#self.media_response = raw_input(self.media_sender + ' is sending ' + self.filename + ' of ' + str(self.filesize) + " Bytes, download? (Y/N)? -> ")
						if(platform.system() == 'Linux'):
							self.bubble.update('Incoming Media!', 'Open the app to accept or reject the file')
							self.bubble.show()
						
						self.lbl_error.setText('Incoming file!')
						while ((not(self.radio_yes.isChecked())) and (not(self.radio_no.isChecked()))):
							pass

						if (self.radio_yes.isChecked()):
							self.media_response = 'y'

						elif (self.radio_no.isChecked()):
							self.media_response = 'n'

					# if the client accepts the media file
					if (self.media_response == 'y'):
						# receive the incoming bytes and reconstruct the media file
						with open('new_' + self.filename, 'wb') as f:
							self.media_data = self.media_conn_list[0].recv(2048)
							self.total_recv = len(self.media_data)
							f.write(self.media_data)

							# if we received less than the size of the file --> keep receiving
							while (self.total_recv < self.filesize):
								self.media_data = self.media_conn_list[0].recv(2048)
								self.total_recv += len(self.media_data)
								f.write(self.media_data)

								# start the GUI thread that updates the progress bar
								self.progress_bar_thread.start()
							print "Download Completed!"

						self.lbl_error.clear()

						# close the file properly, I think 'with' automatically closes the file after using it
						f.close()

						# after receiving, if I'm the server --> broadcast to the other client
						if (self.isServer):
							self.filename = 'new_' + self.filename
							self.filepath = self.filename
							self.which = 0
							self.send_file()

					# if didn't accept the media file, receive to empty the buffers and get rid of the data
					else:
						self.media_data = self.media_conn_list[0].recv(2048)
						self.total_recv = len(self.media_data)

						while (self.total_recv < self.filesize):
							self.media_data = self.media_conn_list[0].recv(2048)
							self.total_recv += len(self.media_data)

				# if the sender is me --> discard the incoming data bytes
				else:
					self.media_data = self.media_conn_list[0].recv(2048)
					self.total_recv = len(self.media_data)

					while (self.total_recv < self.filesize):
						self.media_data = self.media_conn_list[0].recv(2048)
						self.total_recv += len(self.media_data)
						
			# if file is corrupted, empty the buffers
			except ValueError:
				self.lbl_error.setText("Corrupted File!")
				rubbish = self.media_conn_list[0].recv(10000)

		# eeh da??
			self.radio_yes.setChecked(False)
			self.radio_no.setChecked(False)
			self.radio_7amada.setChecked(True)
			self.lbl_error.clear()
		s.close()



	# nafs el comments elly foo2 b2a msh ha3od akteb tany
	def media_client_2(self):
		while True:
			print 'Waiting for a file'

			self.media_data = self.media_conn_list[1].recv(2048)
			print self.media_data

			try:
				self.media_sender = self.media_data[:self.media_data.index('`')]
				self.filename = self.media_data[self.media_data.index('`')+1:self.media_data.index('|')]
				self.filesize = int(self.media_data[self.media_data.index('|')+1:])

				if (self.media_sender != socket.getfqdn()):
					if (self.isServer):
						self.media_response = 'y'

					else:
						# you have the freedom to either accept or reject the incoming media file
						#self.media_response = raw_input(self.media_sender + ' is sending ' + self.filename + ' of ' + str(self.filesize) + " Bytes, download? (Y/N)? -> ")
						if(platform.system() == 'Linux'):
							self.bubble.update('Incoming Media!', 'Open the app to accept or reject the file')
							self.bubble.show()

						self.lbl_error.setText('Incoming file!')
						while ((not(self.radio_yes.isChecked())) and (not(self.radio_no.isChecked()))):
							pass

						if (self.radio_yes.isChecked()):
							self.media_response = 'y'

						elif (self.radio_no.isChecked()):
							self.media_response = 'n'

					if (self.media_response == 'y'):
						with open('new_' + self.filename, 'wb') as f:
							self.media_data = self.media_conn_list[1].recv(2048)
							self.total_recv = len(self.media_data)
							f.write(self.media_data)

							while (self.total_recv < self.filesize):
								self.media_data = self.media_conn_list[1].recv(2048)
								self.total_recv += len(self.media_data)
								f.write(self.media_data)

								self.progress_bar_thread.start()
							print "Download Completed!"

						self.lbl_error.clear()
						f.close()


						if (self.isServer):
							self.filename = 'new_' + self.filename
							self.filepath = self.filename
							self.which = 1
							self.send_file()


					else:
						self.media_data = self.media_conn_list[1].recv(2048)
						self.total_recv = len(self.media_data)

						while (self.total_recv < self.filesize):
							self.media_data = self.media_conn_list[1].recv(2048)
							self.total_recv += len(self.media_data)

				else:
					self.media_data = self.media_conn_list[1].recv(2048)
					self.total_recv = len(self.media_data)

					while (self.total_recv < self.filesize):
						self.media_data = self.media_conn_list[1].recv(2048)
						self.total_recv += len(self.media_data)
						

			except ValueError:
				self.lbl_error.setText("Corrupted File!")
				rubbish = self.media_conn_list[1].recv(10000)

		s.close()




	# a thread that keeps polling any incoming data from a client/sender
	def threaded_client_1(self,client_conn):
		while True:
			# wait to receive data from client 1
			self.data[0] = self.conn_list[0].recv(2048)
			print 'data_1: ' + self.data[0]

			if not self.data[0]:
				break
			
			# extract the sender name and message content from the received packet
			# the name and the content are separated by '`'
			self.sender = self.data[0].partition('`')[0]
			self.data[0] = self.data[0][self.data[0].index('`') + 1:]

			if (self.sender != socket.getfqdn()):
				# el mafrood a-broadcast el typing signals dee brdo
				# if it is sending a 'is typing' signal
				if (self.data[0] == 'typn+'):
					self.lbl_typing.setText(self.sender + ' is typing...')
					#self.data[0] = ' '

				# if it is sending 'stopped typing' signal
				elif (self.data[0] == ('typn-' + self.sender +'`typn+')):
					self.lbl_typing.clear()
					#self.data[0] = ' '

				elif (self.data[0].startswith('typn')):
					self.lbl_typing.clear()
					#self.data[0] = ' '

				elif (self.data[0] == ('typn-')):
					self.lbl_typing.clear()
					#self.data[0] = ' '

				# if it is sending a message 3ady ya3ny
				else:
					try:
						if(platform.system() == 'Linux'):
							self.bubble.update(self.sender, self.data[0])
							self.bubble.show()

						# play the notification sound
						pygame.mixer.Sound('notification.wav').play()

						# add the received data to the chat room
						self.txt_chat.append(str(self.sender) +': ' + self.data[0])
						self.txt_chat.moveCursor(QtGui.QTextCursor.End)


					except AttributeError as e:
						self.txt_chat.append(str(self.host) +': ' + self.data[0])
						self.txt_chat.moveCursor(QtGui.QTextCursor.End)

				# if I'm the server --> broadcast to other clients
				if (self.isServer):
					print 'broadcaster_1'
					self.broadcast()


		# close the connection with that client
		self.conn_list[0].close()




	# the same commenting as above
	def threaded_client_2(self,client_conn):
		while True:
			self.data[1] = self.conn_list[1].recv(2048)
			print 'data_2: ' + self.data[1]

			if not self.data[1]:
				break
			
			self.sender = self.data[1].partition('`')[0]
			self.data[1] = self.data[1][self.data[1].index('`') + 1:]

			if (self.sender != socket.getfqdn()):
				if (self.data[1] == 'typn+'):
					self.lbl_typing.setText(self.sender + ' is typing...')
					self.data[1] = ' '

				elif (self.data[1] == ('typn-' + self.sender +'`typn+')):
					self.lbl_typing.clear()
					self.data[1] = ' '

				elif (self.data[1].startswith('typn')):
					self.lbl_typing.clear()
					self.data[1] = ' '

				elif (self.data[1] == ('typn-')):
					self.lbl_typing.clear()
					self.data[1] = ' '

				else:
					try:
						if(platform.system() == 'Linux'):
							self.bubble.update(self.sender, self.data[0])
							self.bubble.show()

						pygame.mixer.Sound('notification.wav').play()

						self.txt_chat.append(str(self.sender) +': ' + self.data[1])
						self.txt_chat.moveCursor(QtGui.QTextCursor.End)


					except AttributeError:
						self.txt_chat.append(str(self.host) +': ' + self.data[1])
						self.txt_chat.moveCursor(QtGui.QTextCursor.End)


				if (self.isServer):
					print 'broadcaster_2'
					self.broadcast()


		self.conn_list[1].close()



	# send the 'is typing' notification to the server
	# or broadcast it if you are the server
	def typing_notification(self):
		# if typing --> set chat box borders to grey in case it was red
		self.lndt_msg.setStyleSheet("border: 1px solid grey")

		# if you are the server --> send the notification to everyone
		if (self.isServer):
			for i in range(len(self.conn_list)):
				self.conn_list[i].send(socket.getfqdn() + '`' + 'typn+')

		# if a client --> just send to the server and the server will send to the others
		else:
			self.conn_list[0].send(socket.getfqdn() + '`' + 'typn+')


	# sends the data it received to all the client connected to it
	def broadcast(self):
		for i in range(len(self.conn_list)):
			for j in range(len(self.conn_list)):
				print 'broadcaster'
				if(self.data[j] != ' '):
					self.conn_list[i].send(self.sender + '`' + self.data[j])
		




	########################
	## sending media part ##
	########################
	# browse and get any file to send
	def attach_file(self):
		try:
			# get the file path of the file you want to send
			self.filepath = QtGui.QFileDialog.getOpenFileNames(self, 'Choose any file to send', "/home/omarcartera/Desktop", '*')
			self.filepath = str(self.filepath[0])

			# gets the filename from the path i.e. .../.../../../filename
			self.filename = str(os.path.basename(self.filepath))


			print self.filename

			# send file, the sender is client 0
			self.which = 8
			start_new_thread(self.send_file, ())

		except IndexError:
			pass



	# send media file 
	def send_file(self):
		# send to all connected devices
		for i in range(len(self.media_conn_list)):

			# send to every client other than me
			if (i != self.which):
				# if the file is available on the desk
				if os.path.isfile(self.filepath):
					print self.filename
					print str(os.path.getsize(self.filepath))

					# send --> sender_name`filename|file size
					self.media_conn_list[i].send(socket.getfqdn() + '`' + self.filename + '|' + str(os.path.getsize(self.filepath)))
					
					# leeh??
					time.sleep(1)

					# open the file and send its content to the receivers
					with open(self.filepath, 'rb') as f:
						bytesToSend = f.read(2048)
						self.media_conn_list[i].send(bytesToSend)
						while bytesToSend != "":
							bytesToSend = f.read(2048)
							self.media_conn_list[i].send(bytesToSend)

				else:
					print("ERR ")

				#self.media_conn_list[0].close()


	# change the progress bar value according to the changes to the variables below
	def update_progress_bar(self):
		self.bar_loading.setValue((self.total_recv/float(self.filesize))*100)




def main():
	App = QtGui.QApplication(sys.argv)
	form = mainApp()
	form.show()
	App.exec_()
	

if __name__ == '__main__':
	main()
