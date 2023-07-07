#!/usr/bin/python3
'''
voltage monitoring and controlling software 
functions:  turn on all channels
            turn off all channels
            turn on/off single or multiple channels
            read voltages of all channels
            monitoring voltage and status changes

To Do :     add temperature readout 
            add logger
            
Autor Otari Javakhishvili  
o.javakhishvili@fz-juelich.de
03/2019
(AUG - IKP2)
'''
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from voltage_ui_full import Ui_MainWindow
import sys
import time
import epics
import array

#pv names declaration not all pv-s used at this time 
pv_names = {
"getHVnames":"EXP:JEDI:JEPo:getHVnames",
"getHVchannels":"EXP:JEDI:JEPo:getHVchannels",
"getHVvalues":"EXP:JEDI:JEPo:getHVvalues",
"getHVtimestamps":"EXP:JEDI:JEPo:getHVtimestamps",
"getHVstatus":"EXP:JEDI:JEPo:getHVstatus",
"getHVnChannels":"EXP:JEDI:JEPo:getHVnChannels",
"setHVstatus":"EXP:JEDI:JEPo:setHVstatus",
"setHVall":"EXP:JEDI:JEPo:setHVall",
"setHVtoggle":"EXP:JEDI:JEPo:setHVtoggle",
"getHVtemperature":"EXP:JEDI:JEPo:getHVtemperature"
}

epics_variables = dict()    #contains epics PV objects and its names to be easily accessible 
HVnames = list()            #contains module names
HVvalues = list()           #contains voltage values
HVstatuses = list()         #contains statuses of channels 0-off, 1-on
HVupdatelist = list()       #xontains updated statuses that should be written into the pv setHVstatus

class mywindow(QtWidgets.QMainWindow):
    '''user interface class which handles whole software'''
    def __init__(self):
        ''' initialises user interface and some button press events '''
        super(mywindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.on_load()
        self.ui.all_on.clicked.connect(self.all_on_clicked)
        self.ui.all_off.clicked.connect(self.all_off_clicked)
        self.ui.update_button.clicked.connect(self.update_all)

    def all_on_clicked(self):
        print (setValue("setHVall", 1)) #turns all channels on
      
    def all_off_clicked(self):
        print (setValue("setHVall", 0)) #turns all channels off
       
    def update_all(self):
        setValue("setHVstatus", HVupdatelist)   #sends updated status list to PV to set channel on/off states
       
    def on_load(self):
        '''initialises variables and some events at startup'''
        self.makePVdict()      #makes PV dictionary 
        self.getHVnames()      #gets naems of channels
        self.getHVvalues()     #gets voltage values 
        self.getHVstatuses()   #gets statuses of channels
        
        #constructs events for each button, every button name is same as channel name "for" loop searches
        # in channel names then finds button whos name is equal to channel name and asigns button_State_changed event 
        for n,i in enumerate(HVnames):
            var = self.findChild(QObject, i)
            if var:
                var.clicked.connect(self.button_state_changed)
                var.setToolTip(" Channel name is \n " + "{:^22}".format(i))

    def button_state_changed(self):
        '''this method is event handler it handels every button change on the user interface '''
        global HVupdatelist
        global HVstatuses
        HVupdatelist = HVstatuses   #copies statuses to new status list 
        index = HVnames.index(self.sender().objectName()) #gets index of caller button to change apropriate index in status list
        #print(HVstatuses[index])
        # if new index is different than in previouse status list  change it in new list
        if HVstatuses[index] == 0:
            HVupdatelist[index] = 1
            self.sender().setStyleSheet("background-color: grey")
        else:
            HVupdatelist[index] = 0
            self.sender().setStyleSheet("background-color: grey")
        
       # print(index)

    def makePVdict(self):
        '''for each pv name in pv_names dictionary creates epics PV object and writes it to epics variables dictionary'''
        pv_list = list()
        keys = list(pv_names.keys())
        values = pv_names.values()
        for n in values:
            pv_list.append(epics.PV(str(n)))
        epics_variables.update(dict(zip(keys,pv_list)))
        #creates callback for some pvs which will be used to update values in user interface
        epics_variables["getHVvalues"].add_callback(self.voltageUpdated)
        epics_variables["getHVstatus"].add_callback(self.HVstatusesUpdated)

    def HVstatusesUpdated(self, pvname, value, timestamp, cb_info, **kwargs):
        '''executed whan getHVstatus PV is changed'''
        self.getHVstatuses()
        print("status update")

    def voltageUpdated(self, pvname, value, timestamp, cb_info, **kwargs):
        '''executed whan getHVvalues PV is changed'''
        self.getHVvalues()
        print("voltage update")

    def getHVnames(self):
        '''gets hardvare names of channels from PV'''
        global HVnames
        HVnames = getValue("getHVnames")
        #we dont have channel after C1_04_04 PV variable contains 0-s and we dont need tham at this time so we delete tham
        while True :  
            del HVnames[-1]
            if HVnames[-1] == 'C1_04_04' :
                break

    def getHVvalues(self):
        '''gets voltage values from PV'''
        values = getValue("getHVvalues")
        global HVvalues
        HVvalues = array.array("d", values).tolist()
        stop = HVnames.index("C1_04_04") + 1
        while True :  
            del HVvalues[-1]
            if len(HVvalues) == stop :
                break
        #gets apropriate button to write voltage value on it
        for n,i in enumerate(HVnames):
            var = self.findChild(QObject, i)
            if var:
                var.setText(str(round(HVvalues[n],3)))     
        #print(HVvalues)

    def getHVstatuses(self):
        '''gets statuses from PV'''
        print("hvstatuses interupt")
        values = getValue("getHVstatus")
        global HVstatuses
        HVstatuses = array.array("i", values).tolist()
        print(HVstatuses)
        #updates button background color depending on statuses green -> channel is on; red -> channel is off
        for n,i in enumerate(HVnames):
            var = self.findChild(QObject, i)
            if var:
                if HVstatuses[n] == 1:
                    var.setStyleSheet("background-color: green")
                else:
                    var.setStyleSheet("background-color: red")

def getValue(PV_Name):
    '''reads the value from epics PV variable'''
    value = epics_variables[str(PV_Name)].value
    return value

def setValue(PV_Name, Value):
    '''sends data to epics PV variable'''
    epics_variables[PV_Name].value = Value
    time.sleep(0.1)
    return epics_variables[PV_Name].value


if __name__ == "__main__":
    '''constructs whole application'''
    app = QtWidgets.QApplication([])
    application = mywindow()
    application.show()
    sys.exit(app.exec())
