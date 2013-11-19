import os
import csv

class Logger:
    'Logger, CSV, Dump'
    def __init__(self, path=None):
        self.file_path = os.path.abspath(path)
        self.ofile  = open(self.file_path, "w+")
        self.writer = csv.writer(self.ofile, delimiter='\t', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        self.write_headers()

    def __del__(self):
        self.ofile.close()

    def write_headers(self):
        self.labels = ["timestamp", 'essid', "mac address", "link quality", "raw rssi", "raw zone", "predicted rssi", 
        "predicted zone", "rssi delta", "rssi step delta", "timestamp step delta"]
        self.writer.writerow(self.labels)

    def log(self, input_vector):
        self.writer.writerow(input_vector)


    def dump(self, entries, zones):
        # number of cells
        print("# of Cells:%d" % len(entries))
        for key, model in entries.iteritems():
            print("KEY/MAC/SSID:%s,%s,%s" % (key, model.macaddress, model.essid))
            print("RAW QUALITY/RSSI/Zone:%d,%d,%d,%s" % (model.quality_raw, model.quality_max, model.rssi_raw, model.zone_raw.current_zone)) 
            print("PREDICTED RSSI/Zone:%d,%s" % (model.rssi_predicted, model.zone_predicted.current_zone)) 


        # number of cells in each zone
        print("# of Zones:%d" % len(zones))
        for key, models in zones.iteritems():
            print("ZONE/KEY:%s, %d, %s" % (key, len(models), models))
            for idx in models:
                print("RAW MAC/SSID/RSSI/ZONE/AGED:%s,%s,%d,%s,%d" % (idx.macaddress, idx.essid, idx.rssi_raw, idx.zone_raw.current_zone, idx.aged))
                print("PREDICTED MAC/SSID/RSSI/ZONE/AGED:%s,%s,%d,%s,%d" % (idx.macaddress, idx.essid, idx.rssi_predicted, idx.zone_predicted.current_zone, idx.aged))

