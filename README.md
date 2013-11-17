[Project]
* NuPIC Wifi Localization based on signal strength and link quality
* NuPIC does best in samples that vary in time and can generalize from slight changes 
* Prediction of signal strength based on time steps (NuPIC platform)
* Inputs to Prediction: Signal Strength, Link Quality

* Help Menu (python wifi.py -h)
  *   --version                                show program's version number and exit
  *  -h, --help                                show this help message and exit
  *  -u, --uncached                            uncached scan
  *  -d <DEVICE_NAME>, --device=<DEVICE_NAME>  wireless device,default=wlan0
  *  -r <PERIOD>, --rescan=<PERIOD>            rescan period (sec), default=2
  *  -e <STRENGTH>, --emulate=<STRENGTH>       fluctuation emulation RSSI, default=-5
  *  -a <THRESHOLD>, --age=<THRESHOLD>         aging RSSI threshold, default=-70
  *  -f <ESSID_NAME>, --filter=<ESSID_NAME>    filter ESSID string
  *  -t <TIME_STEP>, --timestep=<TIME_STEP>    set unit time step, default=5

  Example usage:
  python wifi.py -u -dwlan0 -r2 -a-80 -fDIRECT -t5

* Zones based on RSSI to determine proximity

  *  Zone A (+36, -30)
  *  Zone B (-30, -40)
  *  Zone C (-40, -50)
  *  Zone D (-50, -60)
  *  Zone E (-60, -70)
  *  Zone F (-70, -80)
  *  Zone G (-80, -90)
  *  Zone H (-90,  x)

* output 
  * wlan.csv
  * graph (matplotlib requirement) 
  * Compare raw rssi, predicted rssi based on samples in time 

* Note: 
  * due to memory constraints, it is best to use filter to perform wifi model localization of
  * uncached options requires root access for full scan
  
* ESSID Station is best with WIFI-DIRECT for Testing (DIRECT-*) and move to fluctuate signal
