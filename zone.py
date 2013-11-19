


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

