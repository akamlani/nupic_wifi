import matplotlib.pyplot as plt

class GraphModels:
    def __init__(self, timestep):
        self.plt_raw_history_x = list()
        self.plt_raw_history_y = list()
        self.plt_predicted_history_y = list()
        self.plt_predicted_step_history_y = list()

        # turn matplotlib interactive mode on (ion)
        plt.ion()
        plt.figure()
        # plot title, legend, etc
        plt.title('WiFi Prediction for Single Model, Step=%d' %timestep)
        plt.xlabel('Unit Time Sample')
        plt.ylabel('RSSI (dBm)')
        plt.axis([0,100,-90,-10])   #xmin,xmax,ymin,ymax
        plt.show()
        plt.pause(1)

    def plot(self, model):
        self.plt_raw_history_x.append(len(model.history)-1)
        self.plt_raw_history_y.append(model.rssi_raw)
        self.plt_predicted_history_y.append(model.rssi_predicted)
        self.plt_predicted_step_history_y.append(model.rssi_step_predicted)
        plt.plot(self.plt_raw_history_x, self.plt_raw_history_y, color="blue")
        #plt.plot(self.plt_raw_history_x, self.plt_predicted_history_y, color="red")
        plt.plot(self.plt_raw_history_x, self.plt_predicted_step_history_y, color="green" )
        #plt.legend( ('actual','predicted', 'step') )
        plt.legend( ('actual','predicted') )                
        plt.draw()
        plt.pause(1)
        #print self.plt_raw_history_x, self.plt_raw_history_y, self.plt_predicted_history_y, self.plt_predicted_step_history_y

