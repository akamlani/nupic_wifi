'''
Created on Oct 27, 2013

@author: akamlani
'''

"""A simple client to read WiFi strength and predict it in real time."""
import time
from collections import deque

import csv
import datetime
import logging
import sys
import os

import subprocess
import re
import argparse

from nupic.data.datasethelpers import findDataset
from nupic.frameworks.opf.metrics import MetricSpec
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager

from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.modelfactory import ModelFactory

import model_params


def create():
   parser = argparse.ArgumentParser(description='Display WLAN signal strength.')
   parser.add_argument(dest='interface', nargs='?', default='wlan0', help='wlan interface (default: wlan0)')
   args = parser.parse_args()




def parseWiFi():
    # Retrieve current wifi strength
    quality = []
    quality_sig = []
    quality_max = []
    signal = []
    essid  = []
    proc = subprocess.Popen(['sudo', '/sbin/iwlist', 'wlan0', 'scan'],stdout=subprocess.PIPE)
    #proc = subprocess.Popen(['/sbin/iwlist', 'wlan0', 'scan'],stdout=subprocess.PIPE)

    stdout, stderr = proc.communicate()
    lines = stdout.split('\n')
    for line in lines:
        if 'ESSID' in line:
           data = line.lstrip(' ')
           essid = data.split(':')[1]
           #print essid
        if 'Quality' in line:
           data = line.lstrip(' ').split()
           quality = data[0].split('=')
           quality_sig = quality[1].split('/')[0]
           quality_max = quality[1].split('/')[0]
           signal  = data[2].split('=')
           signal  = signal[1]
           #print quality_sig, quality_max, signal
    return essid, quality_sig, quality_max, signal

           

def runWiFi():
    # Create the model for predicting CPU usage.
    model = ModelFactory.create(model_params.MODEL_PARAMS)
    model.enableInference({'predictedField': 'rssi'})
    # The shifter will align prediction and actual values.
    shifter = InferenceShifter()
    modelHistory = dict()
    cells = dict()
    mymodel = list()


    while True:
	    # get current timestamp
	    s = time.time()
	    # parse the WiFi
	    essid, quality_sig, quality_max, rssi = parseWiFi()
            if not rssi:
              continue
	    print ("SSID:%s, RSSI:%s, Quality:%s, Max Quality:%s" % (str(essid), rssi, quality_sig, quality_max ))
	    # Run the input through the model and shift the resulting prediction.
            modelInput=dict()
	    modelInput["rssi"] = float(rssi)
            modelInput["quality"] = float(quality_sig)
	    result = shifter.shift(model.run(modelInput))
	    inference = result.inferences['multiStepBestPredictions'][5]
            # Inference rssi and quality, but predict rssi
	    if inference is not None:
              delta = abs(result.rawInput['rssi'] - inference)
              print("Inference Data -> Raw rssi:%d, Raw Quality:%d, Inference rssi%d:, Delta:%d" % 
              (result.rawInput['rssi'], result.rawInput['quality'], inference, delta))
              #store data 
              modelHistory['ssid'] = essid
              modelHistory['rawrssi'] = result.rawInput['rssi']
              modelHistory['predictedrssi'] = inference
              modelHistory['rssidelta'] = delta
              if 'Tagged-Meetup' in essid:     
                mymodel.append(modelHistory)
                cells[essid] = mymodel
                print cells[essid]
               

            # sample every 2 seconds and fluctuate power
            time.sleep(3)
   

if __name__ == '__main__':
    create()
    runWiFi()
    
