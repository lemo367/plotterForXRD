import sys
from PyQt5.QtWidgets import(
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget, QDoubleSpinBox, QCheckBox, QVBoxLayout, QHBoxLayout, QMenu, QTextEdit)
from PyQt5.QtGui import QFont
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import csv

#Definition of Main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.statusBar() #definition of statusBar at bottom of window

        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        #menuBarの表示
        menubar = self.menuBar()

        #menuBarのaction定義
        XRD = QAction("XRD", self)
        XRD.setStatusTip("Plot XRD pattern, 2theta-omega, rocking curve, pole figure, etc.")
        XRD.triggered.connect(self.showPlotWindowXRD) #mainwindowからプロットを操作するより、MDIの子ウィンドウから操作した方が良いかもしれない。ここではMDIwinndwの表示に留めるべきか

        Menu_XRD = menubar.addMenu("&XRD")
        Menu_XRD.addAction(XRD)

        self.setGeometry(0, 0, 1280, 800) #Main Windowのサイズ, (x, y, width, height)
        self.setWindowTitle('multiplotter for XRD') #Main Windowのタイトル
        self.show() #Main Windowの表示

    def showPlotWindowXRD(self):
        self.plotWindowXRD = PlotWindowXRD()
        self.mdi.addSubWindow(self.plotWindowXRD.plotPanel)
        self.plotWindowXRD.plotPanel.show()
        self.mdi.addSubWindow(self.plotWindowXRD.controlPanel)
        self.plotWindowXRD.controlPanel.show()


class PlotWindowXRD(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        #プロットデータを制御するためのサブウィンドウ, ファイルダイアログやプロットの種別の選択を行う
        self.controlPanel = QMdiSubWindow()
        self.controlPanel.setWindowTitle("Control Panel")
        self.controlPanel.setFixedSize(300, 400)

        comboPlotType = QComboBox(self.controlPanel)
        plotType =['2theta-omega', 'Rocking Curve', 'Pole Figure']
        comboPlotType.addItems(i for i in plotType)

        btnLoad = QPushButton("Browse", self.controlPanel)
        btnLoad.clicked.connect(self.loadXRD)

        btnPlot = QPushButton("Plot", self.controlPanel)
        btnPlot.clicked.connect(self.plotXRD)

        btnLayout = QHBoxLayout()
        btnLayout.addWidget(btnLoad)
        btnLayout.addWidget(btnPlot)

        ctrlLayout = QVBoxLayout()
        ctrlLayout.addWidget(comboPlotType)
        ctrlLayout.addLayout(btnLayout)

        ctrWidget = QWidget()
        ctrWidget.setLayout(ctrlLayout)
        self.controlPanel.setWidget(ctrWidget)

        #プロットデータを表示するためのサブウィンドウ
        self.plotPanel = QMdiSubWindow()
        self.plotPanel.setWindowTitle("Graph")
        self.plotPanel.setGeometry(0, 0, 500, 500)

        # グラフの初期設定値
        config = {
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.width": 1.0,
            "ytick.major.width": 1.0,
            "xtick.minor.width": 1.0,
            "ytick.minor.width": 1.0,
            "xtick.major.size": 5.0,
            "ytick.major.size": 5.0,
            "xtick.minor.size": 3.0,
            "ytick.minor.size": 3.0,
            "font.family": "Arial",
            "font.size": 12
        }
        plt.rcParams.update(config)

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.set_xlabel(r'2$\theta$ (deg.)', fontsize=14)
        self.ax.set_ylabel('Intensity (a.u.)', fontsize=14)

        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self.plotPanel)

        self.plotLayout = QVBoxLayout()
        self.plotLayout.setContentsMargins(0, 0, 0, 0)
        self.plotLayout.addWidget(self.canvas)
        self.plotLayout.addWidget(self.toolbar)

        self.plotWidget = QWidget()
        self.plotWidget.setLayout(self.plotLayout)
        self.plotPanel.setWidget(self.plotWidget)

        self.canvas.draw()

    def plotXRD(self):
        action = self.sender()
        if action.text() == '2theta-omega':
            print(action.text())

        elif action.text() == 'Rocking Curve':
            print(action.text())

        elif action.text() == 'Pole Figure':
            print(action.text())

    def loadXRD(self):
        fPath = QFileDialog.getOpenFileName(self, 'Open file', '/home', 'CSV(*.csv)') #ファイルダイアログの表示
        dictData = {} #データを格納する辞書, データ型はdataframeとする。

        with open(fPath[0], newline='') as f:
            reader = csv.reader(f)
            csvData = list(reader)
            for i, row in enumerate(csvData):
                if '[Scan points]' in row:
                    data = pd.read_csv(fPath[0], skiprows = i+1, header = 0, names = ["Angle", "TimePerStep", "Intensity", "ESD"])
                    dictData['data'] = data

                    for j, row in enumerate(csvData):
                        if 'Scan axis' in row:
                            scanAxis = pd.read_csv(fPath[0], header = None, skiprows = lambda x : x not in [j], names = ['axis'])
                            dictData['scanAxis/type'] = scanAxis['axis']
                            break
                    
                    break

                elif i == len(csvData) and '[Scan points]' not in row:
                    for j, row in enumerate(csvData):
                        if 'Time per step' in row:
                            data = pd.read_csv(fPath[0], skiprows = j+1, header = None)
                            dictData['data'] = data
                            dictData['scanAxis/type'] = 'Pole Figure'
                            continue
                    
                        elif 'Psi range' in row:
                            rangePsiPhi = pd.read_csv(fPath[0], header = None, skiprows = lambda x : x not in [j, j+1], names = ['start', 'end', 'step'])
                            dictData['Psi and Phi'] = rangePsiPhi
                            continue
                        
                        elif dictData['scanAxis/type'] != '' and dictData['Psi and Phi'] != '':
                            break

                elif i < len(csvData) and '[Scan points]' not in row:
                    continue

        print(dictData)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())