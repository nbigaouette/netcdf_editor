#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import sys
from PySide import QtGui, QtCore

import tempfile
import numpy as np
import netCDF4
import shutil

class NetCDF_Editor(QtGui.QMainWindow):

    def __init__(self, sys_argv):
        super(NetCDF_Editor, self).__init__()

        self.input_filename = ""
        self.tmp_file       = ""
        self.grid           = ""

        self.initUI()

        if (len(sys_argv) == 2):
            self.input_filename = sys_argv[1]
            self.tmp_file = self.Copy_file_to_tmp(self.input_filename)
            self.Parse_NetCDF_File()

    def initUI(self):

        openFile = QtGui.QAction(QtGui.QIcon.fromTheme('system-file-manager'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        openFile.triggered.connect(self.OpenDialog)

        saveFile = QtGui.QAction(QtGui.QIcon.fromTheme('document-save'), 'Save', self)
        saveFile.setShortcut('Ctrl+S')
        saveFile.setStatusTip('Save File')
        saveFile.triggered.connect(self.Save)

        saveFileAs = QtGui.QAction(QtGui.QIcon.fromTheme('document-save-as'), 'Save As', self)
        saveFileAs.setShortcut('Ctrl+Shift+S')
        saveFileAs.setStatusTip('Save File As')
        saveFileAs.triggered.connect(self.SaveAs)

        exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(saveFile)
        fileMenu.addAction(saveFileAs)
        fileMenu.addAction(openFile)
        fileMenu.addAction(openFile)
        fileMenu.addAction(exitAction)

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(saveFile)
        toolbar.addAction(saveFileAs)
        toolbar.addAction(openFile)
        toolbar.addAction(exitAction)

        self.setGeometry(0, 0, 800, 600)
        self.setWindowTitle('Main window')
        self.setWindowIcon(QtGui.QIcon.fromTheme('esd'))

        # Center window
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.setCentralWidget(self.scrollArea)

        self.show()

    def OpenDialog(self):

        self.input_filename, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file')

        del self.tmp_file
        self.tmp_file = self.Copy_file_to_tmp(self.input_filename)

    def Copy_file_to_tmp(self, filename):
        tmp_file = tempfile.NamedTemporaryFile()

        print "tmp_filename.name =", tmp_file.name

        shutil.copy2(filename, tmp_file.name)

        return tmp_file

    def Parse_NetCDF_File(self):
        self.rootgrp = netCDF4.Dataset(self.tmp_file.name,  'a')

        self.Display_NetCDF_File()

    def Display_NetCDF_File(self):

        scrollWidget = QtGui.QWidget()
        grid = QtGui.QGridLayout()
        line = 0
        for variable in self.rootgrp.variables:
            # Left column
            button = QtGui.QPushButton(variable, self)
            button.setToolTip("Click to edit \"" + variable + "\"'s value")
            button.clicked.connect(self.ButtonClick)
            grid.addWidget(button, line, 0)
            # Right column
            grid.addWidget(QtGui.QLabel(str(self.rootgrp.variables[variable][0])), line, 1)
            line += 1
        scrollWidget.setLayout(grid)
        self.scrollArea.setWidget(scrollWidget)

    def Change_NetCDF_Value(self, variable, text):
        new_variable_value_string = text

        variable_type = type(self.rootgrp.variables[variable][0])
        # Detect file type
        if (variable_type == np.int32):
            new_variable_value = np.int32(new_variable_value_string)
        elif (variable_type == np.float32):
            new_variable_value = np.float32(new_variable_value_string)
        elif (variable_type == np.float64):
            new_variable_value = np.float64(new_variable_value_string)
        elif (variable_type == np.int8):
            if (new_variable_value_string.lower() == "true" or new_variable_value_string == "1"):
                new_variable_value = np.int8(True)
            else:
                new_variable_value = np.int8(False)
        elif (variable_type == np.string_):
            new_variable_value = new_variable_value_string
        else:
            print "ERROR: Supported types are:"
            print "    int, float, double, bool, string"
            print "Exiting."
            sys.exit(0)


        if (variable_type == np.string_):
            QtGui.QMessageBox.warning(self, "Error", "Sorry, changing strings not yet implemented.")
        else:
            self.rootgrp.variables[variable][0] = new_variable_value

        self.Display_NetCDF_File()

    def ButtonClick(self):
        sender = self.sender()
        variable = sender.text()
        self.statusBar().showMessage("Changing " + variable + "'s value")

        text, ok = QtGui.QInputDialog.getText(self, "Change variable's value", "Enter new value for \"" + variable + "\"")
        if ok:
            var_type = type(self.rootgrp.variables[variable][0])
            if (var_type == np.string_):
                QtGui.QMessageBox.warning(self, "Error", "Sorry, changing strings not yet implemented.")
            else:
                self.Change_NetCDF_Value(variable, text)
                self.statusBar().showMessage("Changed " + variable + "'s value to " + text)

    def Save(self):
        print "Saving..."
        self.rootgrp.sync()
        shutil.copy2(self.tmp_file.name, self.input_filename)

    def SaveAs(self):
        print "Saving as..."
        new_tmp_file = self.Copy_file_to_tmp(self.tmp_file.name)

        new_filename, _ = QtGui.QFileDialog.getSaveFileName(self, "Save As")
        # Make sure .cdf is the extension
        if (new_filename[-4:] != ".cdf"):
            new_filename = new_filename + ".cdf"
        print "Saving to", new_filename

        #new_filename = new_tmp_file.name + "_saveas"
        #print "new_tmp_file.name =", new_tmp_file.name
        #shutil.copy2(new_tmp_file.name, new_filename)


def main():

    app = QtGui.QApplication(sys.argv)
    ex = NetCDF_Editor(sys.argv)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

