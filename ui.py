#!/usr/bin/env python3
import sys
import time
from multiprocessing import Process, Queue, Event, freeze_support
import threading
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtCore
from PyQt5.QtGui import *
import getpreview
import launchbot
import launchcart
import validateIP
import apicall
import hcbexport
import hcbimport

# load qt ui
qtCreatorFile = "C:/Users/Patrick/PycharmProjects/holycopbot/holycopbot.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QMainWindow):
    def __init__(self):
        super(MyApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.closeEvent = self.closeEvent
        self.ui.setupUi(self)

        self.botinstances = []
        self.cookies = []
        self.newrow = []
        self.killevents = []
        self.count = 0
        self.ui.addRow.clicked.connect(self.AddRow)
        self.ui.verify.clicked.connect(self.verification)
        self.ui.runAll.hide()
        self.ui.runAll.clicked.connect(self.runall)
        self.ui.actionOpen.setShortcut("Ctrl+R")
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionOpen.setShortcut("Ctrl+O")
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSave.setShortcut("Ctrl+S")

        # Start cookie listening
        self.qcookies = Queue()
        self.endcookies = Event()
        self.cookieplacer = threading.Thread(target=self.CookieListener)
        self.cookieplacer.start()

    def save(self):
        Qname = QFileDialog.getSaveFileName(self, 'Save file', '', "HolyCopBot Files (*.hcb)")
        if Qname:
            name = Qname[0]
            linklist = []
            proxylist = []
            sizelist = []
            for i in range(self.count):
                linklist.append(self.newrow[i].urlInput.text())
                proxylist.append(self.newrow[i].proxy.text() + ":" + self.newrow[i].proxyport.text())
                sizelist.append(str(self.newrow[i].sizeBox.currentText()))
            hcbexport.all(name, linklist, proxylist, sizelist)

    def open(self):
        Qname = QFileDialog.getOpenFileName(self, 'Open file', '', "HolyCopBot Files (*.hcb)")[0]
        if Qname:
            name = Qname
            filecontents = hcbimport.all(name)
            linklist = filecontents[0]
            proxylist = filecontents[1]
            proxyportlist = filecontents[2]
            sizelist = filecontents[3]
            for i in range(len(linklist)):
                newest = self.count
                self.AddRow()
                self.newrow[newest].urlInput.setText(linklist[i])
                self.newrow[newest].proxy.setText(proxylist[i])
                self.newrow[newest].proxyport.setText(proxyportlist[i])
                index = self.newrow[newest].sizeBox.findText(sizelist[i], QtCore.Qt.MatchFixedString)
                if index >= 0:
                    self.newrow[newest].sizeBox.setCurrentIndex(index)

    def verification(self):
        # api verification check
        key = self.ui.verifyKey.text()

        verified = apicall.verify(key)
        if verified:
            self.ui.verify.hide()
            self.ui.verifyKey.hide()
            self.ui.verifyLabel.hide()
            self.ui.runAll.show()
            self.ui.addRow.setEnabled(True)
            self.ui.actionOpen.setEnabled(True)
            self.ui.actionSave.setEnabled(True)
        else:
            reply = QMessageBox.question(self, 'Not Registered', "Your verification key was incorrect", QMessageBox.Ok)
            if reply == QMessageBox.Ok:
                self.close()

    def runall(self):
        if self.count == 0:
            return
        else:
            self.ui.runAll.setEnabled(False)
            for i in range(self.count):
                self.RunBot(i)

    def AddRow(self):
        #limit of concurrent bots
        if self.count > 20:
            return

        self.newrow.append(RowWidget(self.ui, self.count))
        somenum = int(self.newrow[self.count].countLabel.text())
        self.ui.verticalLayout_2.addWidget(self.newrow[self.count].widget)
        self.newrow[self.count].run.clicked.connect(lambda: self.RunBot(somenum))
        self.newrow[self.count].openCart.clicked.connect(lambda: self.OpenCart(somenum))
        self.newrow[self.count].stop.clicked.connect(lambda: self.StopProcess(somenum))
        self.count += 1

    def RunBot(self, somenum):
        link = self.newrow[somenum].urlInput.text()
        if link == "":
            self.newrow[somenum].invalidUrl.setText("Invalid Url!")
        else:
            self.newrow[somenum].invalidUrl.setText("")
            # get and validate proxy if exists
            self.proxy = self.newrow[somenum].proxy.text() + ":" + self.newrow[somenum].proxyport.text()
            ipcheck = validateIP.check(self.proxy)
            if ipcheck == False or self.proxy == '':
                self.proxy = 0

            rawsize = str(self.newrow[somenum].sizeBox.currentText())
            if rawsize == "Size":
                self.newrow[somenum].invalidUrl.setText("Invalid Size!")
            if not rawsize == "Size":
                size = rawsize.replace(".", "")
                self.newrow[somenum].run.setText("Running")
                self.newrow[somenum].stop.setEnabled(True)
                self.newrow[somenum].run.setEnabled(False)
                self.newrow[somenum].sizeBox.setEnabled(False)

                imagepreview = threading.Thread(target=self.GetPreviewImage, args=(link,somenum))
                imagepreview.start()

                self.BotInstance(link,size,somenum)

    def BotInstance(self, link, size, row):
        kill = Event()
        self.killevents.insert(row, kill)
        botprocess = Process(target=launchbot.runbot, args=(link, size, self.proxy, self.qcookies, row, self.killevents[row]))
        botprocess.start()
        self.botinstances.insert(row, botprocess)

    def CookieListener(self):
        while not self.endcookies.is_set():
            if self.qcookies.qsize() != 0:
                self.ui.runAll.setEnabled(True)
                result = self.qcookies.get()
                placeinrow = result[0]
                # error handling
                if result[1] == "oos":
                    error = "Size Out of Stock!"
                    self.newrow[placeinrow].invalidUrl.setText(error)
                if result[1] == 'forbidden':
                    error = "IP Ban! (temporary)"
                    self.newrow[placeinrow].invalidUrl.setText(error)
                else:
                    newcookies = result[1]
                    self.cookies.insert(placeinrow, newcookies)
                    self.newrow[placeinrow].run.setText("Copped!")
                self.newrow[placeinrow].openCart.setEnabled(True)
                self.newrow[placeinrow].stop.setEnabled(False)

    def OpenCart(self,somenum):
        self.newrow[somenum].run.setText("Run")
        self.newrow[somenum].run.setEnabled(True)
        self.newrow[somenum].sizeBox.setEnabled(True)

        link = self.newrow[somenum].urlInput.text()
        global site
        if "footlocker" in link:
            site = "https://www.footlocker.com/"
        if "footaction" in link:
            site = "https://www.footaction.com/"
        if "eastbay" in link:
            site = "https://www.eastbay.com/"
        if "champssports" in link:
            site = "https://www.champssports.com/"
        cartbrowser = Process(target=launchcart.opencart, args=(site, self.cookies[somenum], self.proxy))
        cartbrowser.start()

    def GetPreviewImage(self, link, rownum):
        img = getpreview.req(link)
        # set pixmap qt object to image returned
        pixmap = QPixmap()
        pixmap.loadFromData(img)
        self.newrow[rownum].previewImage.setPixmap(pixmap)

    def StopProcess(self, rownum):
        # set event for botinstance to kill, then wait for event to be unset, reset gui
        killevent = self.killevents[rownum]
        killevent.set()
        while killevent.is_set():
            time.sleep(.1)
        self.botinstances[rownum].terminate()
        self.newrow[rownum].run.setText("Run")
        self.newrow[rownum].stop.setEnabled(False)
        self.newrow[rownum].run.setEnabled(True)
        self.newrow[rownum].sizeBox.setEnabled(True)

    def closeEvent(self, event):
        if self.count == 0:
            self.endcookies.set()
            sys.exit()
        reply = QMessageBox.question(self, 'Confirm Exit',
            "Are you sure you want to quit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.endcookies.set()
            time.sleep(0.15)
            event.accept()
        else:
            event.ignore()


class RowWidget(QWidget):
    def __init__(self, ui, count):
        QWidget.__init__(self)
        MainWindow = ui
        self.setupUi(MainWindow, count)
        self.test123 = "test"

    def setupUi(self, MainWindow, count):
        self.widget = QtWidgets.QWidget(MainWindow.scrollContent)
        self.widget.setObjectName("widget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.sizeBox = QtWidgets.QComboBox(self.widget)
        self.sizeBox.setCurrentText("")
        self.sizeBox.setMaxCount(50)
        self.sizeBox.setObjectName("sizeBox")
        self.gridLayout_2.addWidget(self.sizeBox, 0, 2, 1, 1)
        self.previewImage = QtWidgets.QLabel(self.widget)
        self.previewImage.setMaximumSize(QtCore.QSize(150, 100))
        self.previewImage.setObjectName("previewImage")
        self.gridLayout_2.addWidget(self.previewImage, 0, 0, 1, 1)
        self.runstopbox = QtWidgets.QWidget(self.widget)
        self.runstopbox.setMinimumSize(QtCore.QSize(100, 50))
        self.runstopbox.setObjectName("runstopbox")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.runstopbox)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.run = QtWidgets.QPushButton(self.runstopbox)
        self.run.setObjectName("run")
        self.verticalLayout_3.addWidget(self.run)
        self.stop = QtWidgets.QPushButton(self.runstopbox)
        self.stop.setEnabled(False)
        self.stop.setObjectName("stop")
        self.verticalLayout_3.addWidget(self.stop)
        self.gridLayout_2.addWidget(self.runstopbox, 0, 3, 1, 1)
        self.openCart = QtWidgets.QPushButton(self.widget)
        self.openCart.setEnabled(False)
        self.openCart.setObjectName("openCart")
        self.gridLayout_2.addWidget(self.openCart, 0, 5, 1, 1)
        self.inputbox = QtWidgets.QWidget(self.widget)
        self.inputbox.setMinimumSize(QtCore.QSize(500, 0))
        self.inputbox.setMaximumSize(QtCore.QSize(16777215, 120))
        self.inputbox.setObjectName("inputbox")
        self.gridLayout = QtWidgets.QGridLayout(self.inputbox)
        self.gridLayout.setObjectName("gridLayout")
        self.portLabel = QtWidgets.QLabel(self.inputbox)
        self.portLabel.setObjectName("portLabel")
        self.gridLayout.addWidget(self.portLabel, 4, 2, 1, 1)
        self.urlInput = QtWidgets.QLineEdit(self.inputbox)
        self.urlInput.setObjectName("urlInput")
        self.gridLayout.addWidget(self.urlInput, 2, 1, 1, 1)
        self.linkLabel = QtWidgets.QLabel(self.inputbox)
        self.linkLabel.setObjectName("linkLabel")
        self.gridLayout.addWidget(self.linkLabel, 2, 0, 1, 1)
        self.proxy = QtWidgets.QLineEdit(self.inputbox)
        self.proxy.setObjectName("proxy")
        self.gridLayout.addWidget(self.proxy, 4, 1, 1, 1)
        self.proxyLabel = QtWidgets.QLabel(self.inputbox)
        self.proxyLabel.setObjectName("proxyLabel")
        self.gridLayout.addWidget(self.proxyLabel, 4, 0, 1, 1)
        self.proxyport = QtWidgets.QLineEdit(self.inputbox)
        self.proxyport.setMaximumSize(QtCore.QSize(60, 40))
        self.proxyport.setObjectName("proxyport")
        self.gridLayout.addWidget(self.proxyport, 4, 3, 1, 1)
        self.invalidUrl = QtWidgets.QLabel(self.inputbox)
        self.invalidUrl.setText("")
        self.invalidUrl.setObjectName("invalidUrl")
        self.gridLayout.addWidget(self.invalidUrl, 0, 1, 1, 1, QtCore.Qt.AlignHCenter)
        self.countLabel = QtWidgets.QLabel(self.inputbox)
        self.countLabel.setText("")
        self.countLabel.setObjectName("countLabel")
        self.gridLayout.addWidget(self.countLabel, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.inputbox, 0, 1, 1, 1)

        self.retranslateUi()
        # QtCore.QMetaObject.connectSlotsByName(self.widget)

        self.countLabel.setText(str(count))
        sizevals = ["Size", "07.5", "08.0", "08.5", "09.0", "09.5", "10.0", "10.5", "11.0", "11.5", "12.0", "12.5",
                    "13.0", "14.0", "15.0"]
        for sizeval in sizevals:
            self.sizeBox.addItem(sizeval)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.openCart.setText(_translate("MainWindow", "Open Cart"))
        self.portLabel.setText(_translate("MainWindow", "Port:"))
        self.linkLabel.setText(_translate("MainWindow", "Link URL:"))
        self.proxyLabel.setText(_translate("MainWindow", "Proxy IP:"))
        self.run.setText(_translate("MainWindow", "Run"))
        self.stop.setText(_translate("MainWindow", "Stop"))
        self.previewImage.setText(_translate("MainWindow", "preview"))

if __name__ == "__main__":
    # allow single window in compiled exe for multiprocesses
    freeze_support()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('./icon.png'))
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
