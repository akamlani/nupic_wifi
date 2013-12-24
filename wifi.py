# WiFi Model for Predictions

import os
import re
import sys
import subprocess
import time
# argument parsing
import optparse
from optparse import OptionParser
# user based wifi function
from zone import Zone
from logger import Logger
from wifimodel import WifiModel
from predictor import Predictor
from graphmodels import GraphModels


DEFAULT_FILTER = "XXX"
import getpass
password = getpass.getpass()



class Cells:
    def __init__(self, timestep):
        self.entries = dict()
        self.zonemap = dict()
        self.step_unit = timestep
        self.logger = Logger("./wlan.csv")
        self.graph  = GraphModels(timestep)

    def __del__(self):
        self.entries.clear()
        self.zonemap.clear()

    def log(self):
        self.logger.dump(self.entries, self.zonemap)

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
                wifi_model.timestamp = float(time.time()) 
                #print("QUALITY/RSSI/MODEL %d,%d,%d,%d,%s:" % (wifi_model.quality_raw, wifi_model.quality_max, rssi_raw, wifi_model.rssi_raw, wifi_model))

        
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
                cla_model.predict(idx)

                # Keep History of all rssi values
                history_data = {"timestamp": idx.timestamp,"rssi_raw": idx.rssi_raw, "fluctuation": fluctuation, "rssi_predicted": idx.rssi_predicted,
                "rssi_delta": idx.rssi_delta, "quality_raw": idx.quality_raw, "quality_max": idx.quality_max,
                "aged": idx.aged, "zone_raw": idx.zone_raw, "zone_predicted": idx.zone_predicted }
                idx.history.append(history_data)
                #print("Inference Data -> %s, %s" % (idx.essid, idx.macaddress))
                #print("Inference Data -> Raw rssi:%d, Inference rssi%d:, RSSI Delta:%d" % (idx.rssi_raw, idx.rssi_predicted, idx.rssi_delta))
                #print("Inference Zone -> Raw Zone:%s, Predicted Zone:%s" % (idx.zone_raw.current_zone, idx.zone_predicted.current_zone))

                # rssi_step_delta calculation for current model
                # Compare Sample steps iterations (x) steps in future
                if ( len(idx.history) > (self.step_unit*2) ):
                    pos = len(idx.history) - 1
                    obj = idx.history[pos - self.step_unit]
                    idx.rssi_step_predicted = obj["rssi_predicted"]
                    idx.rssi_step_delta = idx.rssi_raw - obj["rssi_predicted"] 
                    idx.timestamp_step_delta = idx.timestamp - obj["timestamp"]
                    print "Sample Delta Prediction: Len=%d,Pos=%d,Raw Rssi=%d,Predicted Rssi=%d,Rssi Step Delta=%d,Rssi Step Prediction=%d, Timestamp Delta=%d" % (
                    len(idx.history), pos, idx.rssi_raw, idx.rssi_predicted, idx.rssi_step_delta, idx.rssi_step_predicted,  idx.timestamp_step_delta) 

                # if this particular model is aged, do not write to csv file
                if not idx.aged:
                    input_vector = [idx.timestamp, idx.essid, idx.macaddress, str(idx.quality_raw)+"/"+str(idx.quality_max), idx.rssi_raw, 
                    idx.zone_raw.current_zone, idx.rssi_predicted, idx.zone_predicted.current_zone, idx.rssi_delta, idx.rssi_step_delta, 
                    idx.rssi_step_predicted, idx.timestamp_step_delta]             
                    self.logger.log(input_vector)
                    idx.zone_raw.dump()
                    idx.zone_predicted.dump()

                # plot only for a filtered essid      
                if filter in idx.essid:
                    self.graph.plot(idx)

        
        
if __name__ == '__main__':
    #print 'Number of arguments:', len(sys.argv), 'arguments.'
   
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
        cells.log()

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
    
    
    
    

