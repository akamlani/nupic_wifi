from zone import Zone
from predictor import Predictor

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
        self.rssi_step_delta = 0
        self.rssi_step_predicted = 0

        self.timestamp = 0
        self.timestamp_step_delta = 0

        self.quality_raw = 0
        self.quality_max = 0
        self.aged = 0
        self.history = list() 

        self.cla_model = Predictor(timestep)
        
    def __del__(self):
        #print "WifiModel destructor %s" % self
        del self.history

