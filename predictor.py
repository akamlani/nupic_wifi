import time

from nupic.data.datasethelpers import findDataset
from nupic.frameworks.opf.metrics import MetricSpec
from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.frameworks.opf.predictionmetricsmanager import MetricsManager
from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.modelfactory import ModelFactory

import model_params



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

        # Store away current rssi information on the model
        if inference is not None:
            model.rssi_predicted =  int(inference)
            model.rssi_delta = abs(model.rssi_raw - model.rssi_predicted)
            model.zone_predicted.assign_rssi_zone(model.rssi_predicted) 
            #print "Prediction occured %s,%s,%s" % (model.essid, model.macaddress, model)


