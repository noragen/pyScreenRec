# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets # pip install pyqt5
from PyQt5.QtWidgets import QFileDialog
import os 
import pyautogui # pip install pyautogui
import cv2 
import numpy as np 
import pygetwindow as gw
import _thread
import imutils			
import time
import signal
from threading import Thread 
import shlex
import psutil
import subprocess
from subprocess import Popen
from dateutil.relativedelta import relativedelta  # Install it via: pip install python-dateutil
from win32api import GetMonitorInfo, MonitorFromPoint
from PIL import ImageFont, ImageDraw, Image
try: 
	os.remove("output_video.mp4")
except:
	pass

drawing = False
global x1, y1, x2,y2,num,h,w,windowRegion
x1,y1,x2,y2,h,w = 0,0,0,0,0,0
windowRegion=0
num = 0

def signal_handler(sig, frame):
	pass

signal.signal(signal.SIGINT, signal_handler)


class Ui_MainWindow(object):
	def setupUi(self, MainWindow):
		self.threadpool = QtCore.QThreadPool()
		#MainWindow.setObjectName("MainWindow")
		sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)

		H = (sizeObject.height())
		W = (sizeObject.width())
		self.W = W
		self.H = H
		
		monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
		work_area = monitor_info.get("Work")
		DW, DH = work_area[2], work_area[3]

		width, height=DW//4, DH//7
		MainWindow.resize(width, height)
		MainWindow.setMinimumSize(QtCore.QSize(width, height))
		MainWindow.setGeometry(DW-width, DH-height, MainWindow.width(), MainWindow.height());
		MainWindow.setAcceptDrops(True)
		self.centralwidget = QtWidgets.QWidget(MainWindow)
		#self.centralwidget.setObjectName("centralwidget")
		self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
		#self.gridLayout.setObjectName("gridLayout")
		#self.comboBox = QtWidgets.QComboBox(self.centralwidget)
		#self.comboBox.setObjectName("comboBox")
		#self.comboBox.addItem('')
		self.cmd = ""
		""" AUDIO and VIDIO DEVICES """
		from PyQt5.QtMultimedia import QAudioDeviceInfo,QAudio,QCameraInfo
		# List of Audio Input Devices
		self.input_audio_deviceInfos = {dev.deviceName() for dev in QAudioDeviceInfo.availableDevices(QAudio.AudioInput)}
		#self.comboBox.addItems(input_audio_deviceInfos)
		""" ----------------------  """
		#self.comboBox.setCurrentIndex(1)
		
		#self.gridLayout.addWidget(self.comboBox, 1, 0, 1, 1)
		#self.checkBoxesInputDevices, self.checkStates = [*zip(*input_audio_deviceInfos.items())]
		self.checkBoxesInputDevices = \
			[QtWidgets.QCheckBox(deviceName, self.centralwidget) 
			for deviceName in self.input_audio_deviceInfos]   #)
		#]
		
		#print("checkBoxesInputDevices", self.checkBoxesInputDevices)
		
		for i, chkInputDevice in enumerate(self.checkBoxesInputDevices):
			self.gridLayout.addWidget(chkInputDevice, 2, 2, i+1, 1)
			chkInputDevice.toggled.connect(self.toggleAudioDevice)
			chkInputDevice.setChecked(True)
				
		self.Mic = [*self.input_audio_deviceInfos]	
		self.checkBox = QtWidgets.QCheckBox(self.centralwidget)
		#self.checkBox.setObjectName("checkBox")
		self.gridLayout.addWidget(self.checkBox, 2, 0, 1, 1)
		self.pushButton = QtWidgets.QPushButton(self.centralwidget)
		self.pushButton.setMinimumSize(QtCore.QSize(0, 23))
		self.pushButton.setIconSize(QtCore.QSize(16, 25))
		#self.pushButton.setObjectName("pushButton")
		self.gridLayout.addWidget(self.pushButton, 3, 0, 1, 1)
		MainWindow.setCentralWidget(self.centralwidget)
		self.statusbar = QtWidgets.QStatusBar(MainWindow)
		self.statusbar.setObjectName("statusbar")
		MainWindow.setStatusBar(self.statusbar)
		#self.actionNew = QtWidgets.QAction(MainWindow)
		#self.actionNew.setObjectName("actionNew")
		self.retranslateUi(MainWindow)
		QtCore.QMetaObject.connectSlotsByName(MainWindow)
		self.clicked = False
		self.pushButton.clicked.connect(self.takeSnapNow)
		self.checkBox.setChecked(True)
		self.useCam = self.checkBox.isChecked()
		self.checkBox.toggled.connect(self.toggleStatus)
		#self.comboBox.currentIndexChanged[str].connect(self.setAudioDevice)
		self.th={}
		self.cap = ""
		self.st = 0
		self.arguments = ''
		self.process = None
	
	#@QtCore.pyqtSlot()
	def toggleAudioDevice(self):
		self.setAudioDevice(
			list(filter(lambda inputDevName: inputDevName, map(lambda inputDev: ('', inputDev.text())[inputDev.isChecked()], self.checkBoxesInputDevices)))
		)
	
	def setAudioDevice(self,audioD):
		self.Mic = audioD
		
	def toggleStatus(self):
		self.useCam = not self.useCam
		
	def draw_rect(self,event, x, y, flags, param):
		global x1, y1, drawing,  num, img, img2,x2,y2
		if event == cv2.EVENT_LBUTTONDOWN:
			drawing = True
			x1, y1 = x, y
		elif event == cv2.EVENT_MOUSEMOVE:
			if drawing == True:
				a, b = x, y
				if a != x & b != y:
					img = img2.copy()
				   
					cv2.rectangle(img, (x1,y1),(x,y), (0, 255, 0), 2)
		elif event == cv2.EVENT_LBUTTONUP:
			drawing = False
			num += 1
			font = cv2.FONT_HERSHEY_SIMPLEX
			x2 = x
			y2= y

	def takeSnap(self):
		global x1, y1, drawing,  num, img, img2,x2,y2,h,w
		global windowRegion
		if self.useCam==False:
			key=ord('a')

			im1 = pyautogui.screenshot()
			im1.save(r"monitor-1.png")
			
			img= cv2.imread('monitor-1.png') # reading image
			try:
				os.remove('monitor-1.png')
			except:
				pass
				
			img_pil = Image.fromarray(img)
			draw = ImageDraw.Draw(img_pil)
			font_text = ImageFont.truetype(font='arial.ttf', size = 48, encoding = 'utf-8')
			draw.text((self.W//8,self.H//2),  "Klicken und Bereich auswählen,\nw-Taste drücken um die Auswahl zu bestätigen", font=font_text, fill = (20,255,0))
			img = np.array(img_pil)
			cv2.putText(img,"",(self.W//8,self.H//2),cv2.FONT_HERSHEY_TRIPLEX, 1.3, (20,255,0), 2, cv2.LINE_AA) 
			
			img2=img.copy()
			cv2.namedWindow("main", cv2.WINDOW_NORMAL)	
			cv2.setMouseCallback("main", self.draw_rect)
			cv2.setWindowProperty("main", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);

			while key!=ord('w'):
				cv2.imshow("main",img)
				key = cv2.waitKey(1)&0xFF 
			(h, w) = ((y2-y1),(x2-x1))
			if key==ord('w'):
				cv2.destroyAllWindows()
				
		else:
			x1,y1,w,h = ( 0, 0, self.W, self.H )
		if w%2 ==0:
			pass
		else:
			w=w+1
		if h%2 ==0:
			pass
		else:
			h=h+1
		windowRegion = ( x1, y1, w, h )
		return x1,y1,w,h
	

	def run(self,inp,out):
		global windowRegion
		self.st = time.time()
		cnt = 0
		from time import sleep
		while self.running:
			if self.useCam:
				windowRegion = ( 0, 0, self.W, self.H )
			frame = np.array(pyautogui.screenshot(region=windowRegion),dtype="uint8")
			frame = imutils.resize(frame, width=480)
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			#cv2.imshow("Preview",frame)
			rt = relativedelta(seconds=time.time()-self.st)
			st = ('{:02d}:{:02d}:{:02d}'.format(int(rt.hours), int(rt.minutes), int(rt.seconds)))
			self.pushButton.setText('Stop Recording: '+st)
			sleep(1)
			#if cv2.waitKey(1) == 27:
				#w = gw.getWindowsWithTitle('Windows PowerShell')[0]
				#w.close()
				#cv2.destroyAllWindows()
			#	break
		#print("Exited Thread!")
	
	def takeSnapNow(self):
		self.running = True
		if not self.clicked:
			
			#filename = QtWidgets.QFileDialog.getSaveFileName( self.centralwidget,"Save video to file", os.sep.join((os.path.expanduser('~'), 'Desktop')), "MP4(*.mp4);;AVI(*.avi);;MKV(*.mkv);;MOV(*.mov)") 
			#print(filename)
			from datetime import datetime
			
			filename = os.sep.join((os.path.expanduser('~'), "Videos", str(datetime.now()).replace(":", "-").partition(".")[0]+".mp4")) 
			
			while not filename: 
				pyautogui.alert(text='Please write a video name', title='File name required', button='OK')	
				filename = QtWidgets.QFileDialog.getSaveFileName( self.centralwidget,"Save video to file", os.sep.join((os.path.expanduser('~'), 'Desktop')), "MP4(*.mp4);;AVI(*.avi);;MKV(*.mkv);;MOV(*.mov)")[0] 
			try: 
				os.remove(filename)
			except:
				pass
			
			x1,y1,w,h = self.takeSnap()
			
			# self.cmd = r'"ffmpeg -rtbufsize 100M -f dshow -i audio="{}" -f -y -rtbufsize 100M -f gdigrab -framerate 30 -offset_x {} -offset_y {} -video_size {}x{} -draw_mouse 1 -i desktop -c:v libx264 -r 30 -preset ultrafast -tune zerolatency -crf 25 -pix_fmt yuv420p "{}"'.format(self.Mic,x1,y1,w,h,filename[0])
			
			self.cmd = """ffmpeg """ + \
			" ".join('-rtbufsize 1500M -f dshow -thread_queue_size 1024 -i audio="{}"'.format(audioDevice) for audioDevice in self.Mic) \
			+ """ -f -y -rtbufsize 1500M -f gdigrab -framerate ntsc -offset_x {} -offset_y {} -video_size {}x{} -draw_mouse 1 -thread_queue_size 1024 -i desktop -c:v libx264 -r 30 -preset ultrafast -tune zerolatency -crf 1 -pix_fmt yuv420p""".format(x1,y1,w,h) \
			+ ("", " -filter_complex [0:a][1:a]amix=inputs=2:duration=shortest ")[len(self.Mic)==2] \
			+ ' "{}" '.format(filename)
			
			#self.cmd = """ffmpeg -rtbufsize 1500M -f dshow -thread_queue_size 1024 -i audio="{}" -rtbufsize 1500M -f dshow -thread_queue_size 1024 -i audio="{}" -f -y -rtbufsize 1500M -f gdigrab -framerate ntsc -offset_x {} -offset_y {} -video_size {}x{} -draw_mouse 1 -thread_queue_size 1024 -i desktop -c:v libx264 -r 30 -preset ultrafast -tune zerolatency -crf 1 -pix_fmt yuv420p -filter_complex [0:a][1:a]amix=inputs=2:duration=shortest "{}" """.format(self.Mic[0],self.Mic[1],x1,y1,w,h,filename)
			
			self.arguments = shlex.split(self.cmd)			
			
			self.clicked = True			
			self.th[0] = Thread(target = self.run,args = (1,1))
			self.th[1] = Thread(target = self.makeVideo,args = (1,))
			self.th[0].start()
			self.th[1].start()
			
			
			self.pushButton.setShortcut("Ctrl+r")
			self.checkBox.setEnabled(False)
		else:
			self.pushButton.setEnabled(False)
			
			self.pushButton.setText('Fertig stellen...')

			os.kill(self.process.pid, signal.CTRL_C_EVENT)
			#self.closePreview()
			#os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)  ##Linux?	

			#w = gw.getWindowsWithTitle('Windows PowerShell')[0]
			#w.close()

			self.clicked = False
			_translate = QtCore.QCoreApplication.translate
			self.pushButton.setText(_translate("MainWindow", "Starte Aufnahme"))
			self.pushButton.setEnabled(True)
			self.checkBox.setEnabled(True)
			self.running = False
	
	def closePreview(self):
		cv2.destroyAllWindows()
		
	def makeVideo(self,inp):
		
		#self.process = subprocess.Popen(self.arguments, shell=True) 
		FNULL = open(os.devnull, 'w')
		#retcode = subprocess.call(self.arguments, stdout=FNULL, stderr=subprocess.STDOUT)
		self.process = subprocess.Popen(self.arguments, stdout=FNULL,
                       shell=True)

		
	def retranslateUi(self, MainWindow):
		_translate = QtCore.QCoreApplication.translate
		MainWindow.setWindowTitle(_translate("MainWindow", "PyShine Video Recorder"))
		#self.comboBox.setItemText(0, _translate("MainWindow", "Audio Gerät auswählen"))
		self.checkBox.setText(_translate("MainWindow", "Full Screen"))
		self.pushButton.setText(_translate("MainWindow", "Starte Aufnahme"))
		self.pushButton.setShortcut(_translate("MainWindow", "Ctrl+r"))
		#self.actionNew.setText(_translate("MainWindow", "New"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
