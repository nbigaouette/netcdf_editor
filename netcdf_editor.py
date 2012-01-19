#!/usr/bin/env python2
# -*- coding: utf-8 -*-



import sys
from PySide import QtGui

import tempfile
import numpy as np
import netCDF4
import shutil

class NetCDF_Editor(QtGui.QMainWindow):

    def __init__(self, sys_argv):
        super(NetCDF_Editor, self).__init__()

        self.input_filename = ""
        self.tmp_file       = ""

        if (len(sys_argv) == 2):
            self.input_filename = sys_argv[1]
            self.Copy_file_to_tmp()

        self.initUI()

    def initUI(self):

        textEdit = QtGui.QTextEdit()
        self.setCentralWidget(textEdit)

        openFile = QtGui.QAction(QtGui.QIcon.fromTheme('system-file-manager'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.OpenDialog)


        exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(exitAction)

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(openFile)
        toolbar.addAction(exitAction)

        self.setGeometry(300, 300, 800, 600)
        self.setWindowTitle('Main window')
        self.setWindowIcon(QtGui.QIcon.fromTheme('esd'))

        self.show()

    def OpenDialog(self):

        self.input_filename, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file')

        self.Copy_file_to_tmp()

    def Copy_file_to_tmp(self):
        # Call self.tmp_file's destructor only when re-opening a new file.
        del self.tmp_file
        self.tmp_file = tempfile.NamedTemporaryFile()

        print "tmp_filename.name =", self.tmp_file.name

        shutil.copy2(self.input_filename, self.tmp_file.name)


def main():

    app = QtGui.QApplication(sys.argv)
    ex = NetCDF_Editor(sys.argv)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

