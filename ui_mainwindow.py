# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        icon = QtGui.QIcon.fromTheme("preferences")
        MainWindow.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(MainWindow)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setObjectName("splitter")
        self.layoutWidget_2 = QtWidgets.QWidget(self.splitter)
        self.layoutWidget_2.setObjectName("layoutWidget_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.layoutWidget_2)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.altLogo = QtWidgets.QLabel(self.layoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.altLogo.sizePolicy().hasHeightForWidth())
        self.altLogo.setSizePolicy(sizePolicy)
        self.altLogo.setMinimumSize(QtCore.QSize(64, 64))
        self.altLogo.setText("")
        self.altLogo.setPixmap(QtGui.QPixmap("basealt.png"))
        self.altLogo.setScaledContents(False)
        self.altLogo.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.altLogo.setObjectName("altLogo")
        self.gridLayout_2.addWidget(self.altLogo, 0, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem, 0, 0, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_2.addItem(spacerItem1, 0, 2, 1, 1)
        self.moduleList = QtWidgets.QListView(self.layoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.moduleList.sizePolicy().hasHeightForWidth())
        self.moduleList.setSizePolicy(sizePolicy)
        self.moduleList.setMinimumSize(QtCore.QSize(200, 200))
        self.moduleList.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.moduleList.setObjectName("moduleList")
        self.gridLayout_2.addWidget(self.moduleList, 1, 0, 1, 3)
        self.stack = QtWidgets.QStackedWidget(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.stack.sizePolicy().hasHeightForWidth())
        self.stack.setSizePolicy(sizePolicy)
        self.stack.setMinimumSize(QtCore.QSize(550, 500))
        self.stack.setObjectName("stack")
        self.emptyPage = QtWidgets.QWidget()
        self.emptyPage.setMinimumSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setPointSize(9)
        self.emptyPage.setFont(font)
        self.emptyPage.setObjectName("emptyPage")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.emptyPage)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.stack.addWidget(self.emptyPage)
        self.verticalLayout.addWidget(self.splitter)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.runOnSessionStart = QtWidgets.QCheckBox(MainWindow)
        self.runOnSessionStart.setObjectName("runOnSessionStart")
        self.gridLayout.addWidget(self.runOnSessionStart, 1, 0, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 1, 1, 1, 1)
        self.closeButton = QtWidgets.QPushButton(MainWindow)
        self.closeButton.setObjectName("closeButton")
        self.gridLayout.addWidget(self.closeButton, 1, 2, 1, 1)
        self.line = QtWidgets.QFrame(MainWindow)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 0, 0, 1, 3)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(MainWindow)
        self.closeButton.pressed.connect(MainWindow.close)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "ALT Center"))
        self.runOnSessionStart.setText(_translate("MainWindow", "Do not run on next sesion start"))
        self.closeButton.setText(_translate("MainWindow", "&Close"))
