#!/usr/bin/env python2
# -*- coding: utf-8 -*-


try:
    from PySide import QtGui, QtCore
    Use_PyQt4_instead_of_PySide = False
except ImportError:
    from PyQt4 import QtGui, QtCore
    Use_PyQt4_instead_of_PySide = True

import sys
import tempfile
import numpy as np
import netCDF4
import shutil

class NetCDF_Editor(QtGui.QMainWindow):

    def __init__(self, sys_argv):
        super(NetCDF_Editor, self).__init__()

        self.input_filename = ""
        self.tmp_file       = ""
        self.file_is_saved  = True
        self.draw_filter    = ""
        self.Initialize_UI()

        if (len(sys_argv) == 2):
            self.input_filename = sys_argv[1]
            self.tmp_file = self.Generate_tmpfile()
            self.Refresh_View()

    def Initialize_UI(self):

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

        refresh = QtGui.QAction(QtGui.QIcon.fromTheme('view-refresh'), 'Refresh', self)
        refresh.setShortcut('F5')
        refresh.setStatusTip('Refresh')
        refresh.triggered.connect(self.Refresh_View)

        exitAction = QtGui.QAction(QtGui.QIcon.fromTheme('application-exit'), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        self.findWidget = QtGui.QLineEdit()
        self.findWidget.setStatusTip('Find a variable name or value')
        self.findWidget.textChanged.connect(self.Find)
        findLabel = QtGui.QLabel('&Find: ')
        findLabel.setBuddy(self.findWidget)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(saveFile)
        fileMenu.addAction(saveFileAs)
        fileMenu.addAction(openFile)
        fileMenu.addAction(refresh)
        fileMenu.addAction(exitAction)

        toolbar = self.addToolBar('Exit')
        toolbar.addAction(openFile)
        toolbar.addAction(saveFile)
        toolbar.addAction(saveFileAs)
        toolbar.addAction(refresh)
        toolbar.addAction(exitAction)
        toolbar.addWidget(findLabel)
        toolbar.addWidget(self.findWidget)

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

    def Refresh_View(self):
        if (not self.file_is_saved):
            answer = QtGui.QMessageBox.question(self, "Warning", "The file is not saved! Save it now?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
            if (answer == QtGui.QMessageBox.Yes):
                self.Save()
            else:
                answer = QtGui.QMessageBox.question(self, "Warning", "The file is not saved! Refresh anyway? You will loose any modifications...", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
                if (answer == QtGui.QMessageBox.No):
                    return
                else:
                    self.statusBar().showMessage("Refreshing, modifications lost!")
        try:
            self.rootgrp.close()
            del self.rootgrp
        except AttributeError:
            pass

        self.file_is_saved = True

        # Copy the file to /tmp
        self.Copy_file_to_tmp()

        # Re-open it
        self.Parse_NetCDF_File()

        # Re-draw the frame
        self.Draw()

    def Copy_file_to_tmp(self):
        print "Copying", self.input_filename, "to", self.tmp_file.name
        shutil.copy2(self.input_filename, self.tmp_file.name)

    def Generate_tmpfile(self):
        return tempfile.NamedTemporaryFile()

    def Parse_NetCDF_File(self):
        try:
            self.rootgrp.close()
            del self.rootgrp
        except AttributeError:
            pass
        print "Parsing", self.tmp_file.name
        self.rootgrp = netCDF4.Dataset(self.tmp_file.name,  'a')

    def OpenDialog(self):

        self.input_filename, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', filter = ("NetCDF files (*.cdf *.nc)"))

        del self.tmp_file
        self.tmp_file = self.Generate_tmpfile()

        self.Refresh_View()

    def Get_String_From_Variable_Content(self, variable, units):
        if (type(self.rootgrp.variables[variable][0]) == np.string_):
            # Collapse the list of characters into a real string
            variable_content = ""
            for i in range(len(self.rootgrp.variables[variable][:])):
                variable_content = variable_content + self.rootgrp.variables[variable][i]
        else:
            variable_content = str(self.rootgrp.variables[variable][0])
            if (units):
                try:
                    variable_content += " " + self.rootgrp.variables[variable].units
                except AttributeError:
                    pass
        return variable_content

    def Draw(self):
        scrollWidget = QtGui.QWidget()
        grid = QtGui.QGridLayout()
        line = 0
        for variable in self.rootgrp.variables:
            if (self.draw_filter == "" or variable.find(self.draw_filter) != -1):
                # Left column
                button = QtGui.QPushButton(variable, self)
                button.setToolTip("Click to edit \"" + variable + "\"'s value")
                button.clicked.connect(self.ButtonClick)
                grid.addWidget(button, line, 0)
                # Right column
                value_to_show = self.Get_String_From_Variable_Content(variable, units = True)
                grid.addWidget(QtGui.QLabel(value_to_show), line, 1)
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
            #QtGui.QMessageBox.warning(self, "Error", "Sorry, changing strings not yet implemented.")
            prev_string_length  = len(self.rootgrp.variables[variable])
            new_string_length   = len(new_variable_value)

            # Overwrite the old string one character at a time. NetCDF will expand the
            # string size automatically.
            for i in xrange(new_string_length):
                self.rootgrp.variables[variable][i] = new_variable_value[i]
            # If the new string is smaller, we need to set the last character to NULL
            # so that the C/C++ code will get the string size correctly. We could set
            # just the last character, but we clear the rest for cosmetic reasons.
            for i in xrange(new_string_length, prev_string_length):
                self.rootgrp.variables[variable][i] = ""

        else:
            self.rootgrp.variables[variable][0] = new_variable_value

        self.Draw()

    def ButtonClick(self):
        sender = self.sender()
        variable = sender.text()
        self.statusBar().showMessage("Changing " + variable + "'s value")

        old_value = self.Get_String_From_Variable_Content(variable, units = False)

        text, ok = QtGui.QInputDialog.getText(self, "Change variable's value", "Enter new value for \"" + variable + "\"", QtGui.QLineEdit.Normal, old_value)
        if ok:
            var_type = type(self.rootgrp.variables[variable][0])
            self.file_is_saved = False
            self.Change_NetCDF_Value(variable, text)
            self.statusBar().showMessage("Changed " + variable + "'s value to " + text)

    def Save(self):
        print "Saving", self.input_filename
        self.rootgrp.sync()
        shutil.copy2(self.tmp_file.name, self.input_filename)
        self.file_is_saved = True

    def SaveAs(self):
        self.rootgrp.sync()

        new_filename_and_other = QtGui.QFileDialog.getSaveFileName(self, "Save As", filter = ("NetCDF files (*.cdf *.nc)"))
        if (Use_PyQt4_instead_of_PySide):
            new_filename = new_filename_and_other
        else:
            new_filename = new_filename_and_other[0]
        print "Saving as", new_filename
        shutil.copy2(self.tmp_file.name, new_filename)
        self.filename = new_filename

    def Find(self):
        self.draw_filter = self.findWidget.text()
        self.Draw()


def main():

    app = QtGui.QApplication(sys.argv)
    ex = NetCDF_Editor(sys.argv)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

