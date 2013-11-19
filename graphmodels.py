import matplotlib.pyplot as plt

class GraphModels:
    def __init__(self):
        self.plt_raw_history_x = list()
        self.plt_raw_history_y = list()
        self.plt_predicted_history_y = list()
        self.plt_predicted_step_history_y = list()

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

    def plot(self, model):
        self.plt_raw_history_x.append(len(model.history)-1)
        self.plt_raw_history_y.append(model.rssi_raw)
        self.plt_predicted_history_y.append(model.rssi_predicted)
        self.plt_predicted_step_history_y.append(model.rssi_step_delta)
        plt.plot(self.plt_raw_history_x, self.plt_raw_history_y)
        plt.plot(self.plt_raw_history_x, self.plt_predicted_history_y)
        #plt.plot(self.plt_raw_history_x, self.plt_predicted_step_history_y)
        #plt.legend( ('actual','predicted', 'step') )
        plt.legend( ('actual','predicted') )                
        plt.draw()
        plt.pause(1)
        #print self.plt_raw_history_x, self.plt_raw_history_y, self.plt_predicted_history_y, self.plt_predicted_step_history_y

