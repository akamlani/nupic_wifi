# parse the wifi function

import os
import re
import sys
import argparse
import subprocess
import time

from collections import OrderedDict
from collections import deque
from datetime import datetime

import optparse
from optparse import OptionParser

from nupic.data.datasethelpers import findDataset
from nupic.frameworks.opf.metrics import MetricSpec
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.modelfactory import ModelFactory

import csv
import sys
import model_params

import matplotlib.pyplot as plt

DEFAULT_FILTER = "XXX"

import getpass
password = getpass.getpass()


class Zone:
    'Zone Identification model'
    zone1_count = 0 #Zone A (+36, -30)
    zone2_count = 0 #Zone B (-30, -40)
    zone3_count = 0 #Zone C (-40, -50)
    zone4_count = 0 #Zone D (-50, -60)
    zone5_count = 0 #Zone E (-60, -70)
    zone6_count = 0 #Zone F (-70, -80)
    zone7_count = 0 #Zone G (-80, -90)
    zone8_count = 0 #Zone H (-90,  x)
    current_zone = ""
        
    def __init__self(self):
        self.current_zone = ""
        self.rssi = 0

    def assign_rssi_zone(self, rssi_input):
        zone = ''
        self.current_rssi = rssi_input
        if rssi_input in range(36,-30, -1): 
            zone = 'A'
            self.zone1_count = self.zone1_count + 1
        elif rssi_input in range(-30,-40, -1):
            zone = 'B'
            self.zone2_count = self.zone2_count + 1
        elif rssi_input in range(-40,-50, -1):
            zone = 'C'
            self.zone3_count = self.zone3_count + 1
        elif rssi_input in range(-50,-60, -1):
            zone = 'D'
            self.zone4_count = self.zone4_count + 1
        elif rssi_input in range(-60,-70, -1):
            zone = 'E'
            self.zone5_count = self.zone5_count + 1
        elif rssi_input in range(-70,-80, -1):
            zone = 'F'
            self.zone6_count = self.zone6_count + 1
        elif rssi_input in range(-80,-90, -1):
            zone = 'G'
            self.zone7_count = self.zone7_count + 1
        elif rssi_input < -90:
            zone = 'H'
            self.zone8_count = self.zone8_count + 1
            
        self.current_zone = zone
        return zone
    
    
    def dump(self):
        print("Zone Name/Counters: %s,%d,%d,%d,%d,%d,%d,%d,%d" % (self.current_zone, self.zone1_count, self.zone2_count, 
        self.zone3_count, self.zone4_count, self.zone5_count, self.zone6_count, self.zone7_count, self.zone8_count) )
        
class Predictor:
    'Prediction model'
    cla_model = ""
    shifter = ""
    def __init__(self, timestep):
        self.cla_model = ""
        self.shifter = ""
        self.timestep = timestep

    def predict(self, model):
        # model input data is 
        cla_model_input=dict()
        cla_model_input["rssi"]    = float(model.rssi_raw)
        cla_model_input["quality"] = float(model.quality_raw)

        if not self.cla_model:
            # Create the model for predicting WiFi usage
            # The shifter will align prediction and actual values.
            s1 = int(round(time.time() * 1000))
            self.cla_model = ModelFactory.create(model_params.MODEL_PARAMS)
            self.cla_model.enableInference({'predictedField': 'rssi'})
            self.shifter = InferenceShifter()        
            s2 = int(round(time.time() * 1000))
            #print "Predictor construction %s,%d,%d,%d" % (self, s1, s2, abs(s2-s1))

        # Shift 'x' time periods into the future
        # Compare 'current' with 'predicted - pos(x)' - how do we compare
        # The point is to be able to Generalize on patterns that it hasn't seen yet
        result = self.shifter.shift(self.cla_model.run(cla_model_input))
        inference = result.inferences['multiStepBestPredictions'][self.timestep]
        return inference


class WifiModel:
    'Wifi model'
    def __init__(self, mac_data, timestep):
        #print "Wifimodel constructor %s" % self
        self.essid = ""
        self.macaddress = mac_data

        self.zone_raw = Zone()
        self.zone_predicted = Zone()

        self.rssi_raw = 0
        self.rssi_predicted = 0
        self.rssi_delta = 0
        self.quality_raw = 0
        self.quality_max = 0
        self.aged = 0
        self.history = list() 
        self.rssi_step_delta = 0
        self.step_idx = 0

        self.cla_model = Predictor(timestep)
        
    def __del__(self):
        #print "WifiModel destructor %s" % self
        del self.history


class Logger:

    def __init__(self, path=None):
        self.file_path = os.path.abspath(path)
        self.ofile  = open(self.file_path, "w+")
        self.writer = csv.writer(self.ofile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        self.write_headers()

    def __del__(self):
        self.ofile.close()

    def write_headers(self):
        self.labels = ["timestamp", 'essid', "mac address", "link quality", "raw rssi", "raw zone", "predicted rssi", 
        "predicted zone", "rssi delta", "rssi step delta"]
        self.writer.writerow(self.labels)

    def log(self, input_vector):
        self.writer.writerow(input_vector)



class Cells:
    def __init__(self, timestep):
        self.entries = dict()
        self.zonemap = dict()
        self.step_unit = timestep
        self.logger = Logger("./wlan.csv")


        # turn matplotlib interactive mode on (ion)
        plt.ion()
        plt.figure()
        # plot title, legend, etc
        plt.title('WiFi Prediction for Single Model')
        plt.xlabel('Unit Time Sample')
        plt.ylabel('RSSI (dBm)')
        plt.axis([0,50,-60,-10])   #xmin,xmax,ymin,ymax
        plt.show()
        plt.pause(1)

        self.plt_raw_history_x = list()
        self.plt_raw_history_y = list()
        self.plt_predicted_history_y = list()
        self.plt_predicted_step_history_y = list()


    def __del__(self):
        self.entries.clear()
        self.zonemap.clear()

    def scan(self, device, perm):
        # scan device for signal based on permission access (sudo)
        if not bool(perm):
            print "default scan"
            proc = subprocess.Popen(['/sbin/iwlist', str(device), 'scan'],stdout=subprocess.PIPE, close_fds=True)
            return proc.communicate()
        else:    
            print "supervised scan"
            proc = subprocess.Popen(['sudo', '/sbin/iwlist', str(device), 'scan'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
            proc.stdin.write(password+'\n')
            return proc.communicate()    
    
    def parse(self, scan_data, rssi_fluctuate, filter):
        mac = ""       
        
        # Clear models, zones, perform fresh parse
        self.zonemap.clear()
        lines = scan_data.split('\n')           
        for line in lines:
            if 'Address' in line:
                data = line.lstrip(' ').strip()
                cell, addr = data.split('-')
                mac = addr.lstrip(' ').split('Address: ')[1]
                if not self.entries.has_key(mac):
                    self.entries[mac] = WifiModel(mac, self.step_unit)
                    #print("MAC/MODEL:%s,%s" %(mac, self.entries[mac]))
            if 'ESSID' in line:
                data = line.lstrip(' ')
                essid_string, essid_data = data.split(':')
                wifi_model = self.entries[mac]
                wifi_model.essid = essid_data
                #print("ESSID/MAC/MODEL:%s,%s,%s,%s" %(essid_string, essid_data, mac, wifi_model))
                if filter not in DEFAULT_FILTER:                
                    if filter not in essid_data:
                        del self.entries[mac]
                    
            if 'Quality' in line: 
                #Quality, Signal level in single line (Quality=61/70  Signal level=-49 dBm)
                wifi_model = self.entries[mac]
                data = line.lstrip(' ')
                vector = data.split("=")
                quality_vector = vector[1].rstrip(" Signal level")
                wifi_model.quality_raw, wifi_model.quality_max = int(quality_vector.split("/")[0]), int(quality_vector.split("/")[1])
                rssi_raw = int(vector[2].rstrip(" dBm"))
                wifi_model.rssi_raw = rssi_raw + int(rssi_fluctuate)
                #print("QUALITY/RSSI/MODEL %d,%d,%d,%d,%s:" % (wifi_model.quality_raw, wifi_model.quality_max, rssi_raw, wifi_model.rssi_raw, wifi_model))

        
    def dump(self):
        # number of cells
        print("# of Cells:%d" % len(self.entries))
        for key, model in self.entries.iteritems():
            print("KEY/MAC/SSID:%s,%s,%s" % (key, model.macaddress, model.essid))
            print("QUALITY/RSSI/Zone:%d,%d,%d,%s" % (model.quality_raw, model.quality_max, model.rssi_raw, model.zone_raw.current_zone)) 

        # number of cells in each zone
        print("# of Zones:%d" % len(self.zonemap))
        for key, models in self.zonemap.iteritems():
            print("ZONE/KEY:%s, %d, %s" % (key, len(models), models ))
            for idx in models:
                print("MAC/SSID/RSSI/ZONE/AGED:%s,%s,%d,%s,%d" % (idx.macaddress, idx.essid, idx.rssi_raw, idx.zone_raw.current_zone, idx.aged))

        
    def filter_rssi(self, threshold):
        # Sort the cells by signal strength in order for each zone, strongest zone first
        # The first zone is the strongest proximity to us
        for key, models in self.zonemap.iteritems():
            self.zonemap[key] = sorted(models, key=lambda WifiModel: WifiModel.rssi_raw, reverse=True)
            for idx in models:
                # Threshold detection, Age cells by on RSSI and determine new Zone
                # Require at least 3 cells greater than this strength 
                if (threshold) > (idx.rssi_raw):
                    idx.aged = 1
                #print idx.zone_id.current_zone, idx.rssi_raw, threshold, idx.aged
                
    def map_zones(self):
        # Zone Map: -30 : -100 - > Map to labeled Zones "
        for key, model in self.entries.iteritems():
            zone = model.zone_raw.assign_rssi_zone(model.rssi_raw)
            self.zonemap.setdefault(zone, []).append(model)
            #print("Zonemap:%s, %d, %s %s" %(key, model.rssi_raw, model.zone_raw.current_zone, self.zonemap[zone]))

           
    def prediction(self, fluctuation, filter):
        for key, models in self.zonemap.iteritems():
            for idx in models:
                # attach to particular cell, now that we have determined to perform prediction
                # the nitial creation of a model factory is done during prediction for a single instance
                cla_model = idx.cla_model
                inference = cla_model.predict(idx)

                if inference is not None:
                    # Store away current rssi information on the model
                    idx.rssi_predicted =  int(inference)
                    idx.rssi_delta = abs(idx.rssi_raw - idx.rssi_predicted)
                    idx.zone_predicted.assign_rssi_zone(idx.rssi_predicted) 
                    #print "Prediction occured %s,%s,%s" % (idx.essid, idx.macaddress, idx)

                # Keep History of all rssi values
                history_data = {"rssi_raw": idx.rssi_raw, "fluctuation": fluctuation, "rssi_predicted": idx.rssi_predicted,
                "rssi_delta": idx.rssi_delta, "quality_raw": idx.quality_raw, "quality_max": idx.quality_max,
                "aged": idx.aged, "zone_raw": idx.zone_raw, "zone_predicted": idx.zone_predicted }
                idx.history.append(history_data)
                # Dump Inference and Raw Information
                #print("Inference Data -> %s, %s" % (idx.essid, idx.macaddress))
                #print("Inference Data -> Raw rssi:%d, Inference rssi%d:, RSSI Delta:%d" % (idx.rssi_raw, idx.rssi_predicted, idx.rssi_delta))
                #print("Inference Zone -> Raw Zone:%s, Predicted Zone:%s" % (idx.zone_raw.current_zone, idx.zone_predicted.current_zone))
                # rssi_step_delta calculation for current model
                # Compare Sample steps iterations (x) steps in future
                if ( len(idx.history) > (self.step_unit*2) ):
                    pos = len(idx.history) - 1
                    obj = idx.history[pos - self.step_unit]
                    idx.rssi_step_delta = idx.rssi_raw - obj["rssi_predicted"] 
                    #print "History Len=%d, Pos=%d, Raw Rssi=%d, Unit=%d, Step Delta =%d" %  (
                    #len(idx.history), pos, idx.rssi_raw, self.step_unit, idx.rssi_step_delta) 

                # if this particular model is aged, do not dump and log the information
                if not idx.aged:
                    timestamp = int(round(time.time() * 1000))
                    input_vector = [timestamp, idx.essid, idx.macaddress, str(idx.quality_raw)+"/"+str(idx.quality_max), idx.rssi_raw, 
                    idx.zone_raw.current_zone, idx.rssi_predicted, idx.zone_predicted.current_zone, idx.rssi_delta, idx.rssi_step_delta]             
                    self.logger.log(input_vector)
                    idx.zone_raw.dump()
                    idx.zone_predicted.dump()
                     
                if filter in idx.essid:
                    self.plt_raw_history_x.append(len(idx.history)-1)
                    self.plt_raw_history_y.append(idx.rssi_raw)
                    self.plt_predicted_history_y.append(idx.rssi_predicted)
                    self.plt_predicted_step_history_y.append(idx.rssi_step_delta)
                    plt.plot(self.plt_raw_history_x, self.plt_raw_history_y)
                    plt.plot(self.plt_raw_history_x, self.plt_predicted_history_y)
                    plt.plot(self.plt_raw_history_x, self.plt_predicted_step_history_y)
                    plt.legend( ('actual','predicted', 'step') )
                    plt.draw()
                    plt.pause(1)
                    #print self.plt_raw_history_x, self.plt_raw_history_y, self.plt_predicted_history_y, self.plt_predicted_step_history_y
                    
        
        
if __name__ == '__main__':
    #print 'Number of arguments:', len(sys.argv), 'arguments.'
    #print 'Arguement List', str(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    

    parser = OptionParser()
    desc="Wireless Localization using NuPIC Open Source CLA"
    parser = optparse.OptionParser(description=desc, usage="usage: %prog [options] filename", version="%prog version 1.0")  
    parser.add_option('-u', '--uncached', help='uncached scan', action="store_true", dest="uncached", default=False)    
    parser.add_option('-d', '--device', help='wireless device,default=wlan0', action='store', dest="device", default="wlan0", metavar='<DEVICE_NAME>')
    parser.add_option('-r', '--rescan', help='rescan period (sec), default=2', action="store", dest="scan_period", type='int', default=2, metavar='<PERIOD>')
    parser.add_option('-e', '--emulate', help='fluctuation emulation RSSI, default=-5', action="store", dest="emulate", type='int', default=5, metavar='<STRENGTH>')
    parser.add_option('-a', '--age', help='aging RSSI threshold, default=-70', action="store", dest="aging", type='int', default=-70, metavar='<THRESHOLD>')
    parser.add_option('-f', '--filter', help='filter ESSID string', default=DEFAULT_FILTER, action="store", dest="filter", metavar='<ESSID_NAME>')   
    parser.add_option('-t', '--timestep', help='set unit time step, default=5', action="store", dest="timestep", default=5, metavar='<TIME_STEP>')

    (args, opts) = parser.parse_args()
    #print args, opts
    
    scan_type      = args.uncached    #cached or uncached scan
    device_name    = args.device      #device name (wlan0, mlan0)
    rescan_period  = args.scan_period #period of re-scan (seconds)
    rssi_fluctuate = args.emulate     #stationary, so we fluctuate by 'x' every AP on every scan
    aging_strength = args.aging       #signal strength at which we age out older APs based on active signal strength
    essid_filter   = args.filter      #essid to filter on
    time_step      = args.timestep    #timestep


    
    cells = Cells(int(time_step))
    while(True):
        # scan for new nearby access points and parse info into table
        stdout, stderr = cells.scan(device_name, scan_type)
        cells.parse(stdout, rssi_fluctuate, essid_filter)
        # based on signal strength, map each access point into a labeled zone
        cells.map_zones()
        # sort the table based on strongest rssi, this is the zone you are currently in
        # set signal strength whereby we have aged out the current access point
        # the strongest signal defines our current area in location
        cells.filter_rssi(aging_strength)
        cells.dump()
    
        # EMULATION MODEL PURPOSES
        # Fluctuation Model - Fluctuate till 'ceiling' hit, then decrement till 'floor' hit, continue [range: 20]    
        # Pattern, We want to see a pattern of which access points we trend towards
        
        
        # PREDICTION
        # Prediction based on RSSI, (Inputs: RSSI, Link Quality) for each AP Model
        # move 'x' steps into the future, after 'x' steps we should started getting prediction sample
        cells.prediction(rssi_fluctuate, essid_filter)
        # Perform rescan in 'x' time period, and repeat until killed
        time.sleep(rescan_period)   
        
        # output data to spreadsheet for mapping (MAC, ESSID, RAW RSSI, RSSI PREDICTED, RSSI DELTA)
        # access Point Predictions, number of times appear in each zone
    
    
    
    

