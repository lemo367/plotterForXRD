import sys
from PyQt5.QtWidgets import(
    QMainWindow, QAction, QFileDialog, QApplication, QMdiArea, QMdiSubWindow, QLabel,
    QComboBox, QPushButton, QWidget, QDoubleSpinBox, QCheckBox, QVBoxLayout, QHBoxLayout, QMenu, QTextEdit)
from PyQt5.QtGui import QFont
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
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
        XRD.setStatusTip("Plot XRD pattern, such as 2theta-omega, rocking curve, and pole figure, etc.")
        XRD.triggered.connect(self.showPlotWindowXRD)

        Menu_XRD = menubar.addMenu("&XRD")
        Menu_XRD.addAction(XRD)

        self.setGeometry(0, 0, 1280, 960) #Main Windowのサイズ, (x, y, width, height)
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

        self.comboPlotType = QComboBox(self.controlPanel)
        self.plotType =['2theta-omega', 'Rocking Curve', 'Pole Figure']
        self.comboPlotType.addItems(i for i in self.plotType)

        btnLoad = QPushButton("Browse", self.controlPanel)
        btnLoad.clicked.connect(self.loadXRD)

        btnPlot = QPushButton("Plot", self.controlPanel)
        btnPlot.clicked.connect(self.plotXRD)

        btnSave = QPushButton("Save", self.controlPanel)
        btnSave.clicked.connect(self.saveFigure)

        btnLayout = QHBoxLayout()
        btnLayout.addWidget(btnLoad)
        btnLayout.addWidget(btnPlot)
        btnLayout.addWidget(btnSave)

        ctrlLayout = QVBoxLayout()
        ctrlLayout.addWidget(self.comboPlotType)
        ctrlLayout.addLayout(btnLayout)

        ctrWidget = QWidget()
        ctrWidget.setLayout(ctrlLayout)
        self.controlPanel.setWidget(ctrWidget)

        #プロットデータを表示するためのサブウィンドウ
        self.plotPanel = QMdiSubWindow()
        self.plotPanel.setWindowTitle("Graph")
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
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
        plType = self.comboPlotType.currentText()
        self.fig.clf()

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

        if self.ax in self.fig.axes:
            self.ax.remove()

        if plType == '2theta-omega':
            self.plotPanel.setGeometry(0, 0, 800, 600)

            self.ax = self.fig.add_subplot(111)
            self.ax.spines['top'].set_visible(False) #プロット外周部の黒枠削除
            self.ax.spines['right'].set_visible(False) #プロット外周部の黒枠削除
            self.ax.set_xlabel(r'2$\theta$ (deg.)', fontsize=14)
            self.ax.set_ylabel('Log-intensity (a.u.)', fontsize=14)
            self.ax.set_yscale("log", nonpositive = 'mask')
            self.ax.minorticks_on()

            df = self.dictData['data']
            plotXRDpattern = self.ax.plot(df['Angle'], df['Intensity'], c = "red", lw = 0.8)

        elif plType == 'Rocking Curve':
            self.plotPanel.setGeometry(0, 0, 600, 800)

            self.ax = self.fig.add_subplot(111)
            self.ax.spines["top"].set_visible(False) #プロット外周部の黒枠削除
            self.ax.spines["right"].set_visible(False) #プロット外周部の黒枠削除
            self.ax.spines["left"].set_visible(False) #プロット外周部の黒枠削除
            self.ax.set_xlabel(xlabel = r'$\omega$ (deg.)', fontsize = 14)
            self.ax.get_yaxis().set_visible(False) #y軸のラベルを非表示, ロッキングカーブにおいてはy軸は不要
            self.ax.minorticks_on()

            df = self.dictData['data']
            plotRockingCurve = self.ax.plot(df['Angle'], df['Intensity'], c = "red", lw = 0.8)

        elif plType == 'Pole Figure':
            self.plotPanel.setGeometry(0, 0, 800, 800)

            df = self.dictData['data'] #型はDataframe
            #以下PsiはXRDでは一般的にChi軸と呼ばれる軸である
            startPsiPhi = self.dictData['Psi and Phi']['start'] #0番目はPsi, 1番目はPhi
            endPsiPhi = self.dictData['Psi and Phi']['end'] #0番目はPsi, 1番目はPhi
            stepPsiPhi = self.dictData['Psi and Phi']['step'] #0番目はPsi, 1番目はPhi

            #Psiの最小値, 測定のスタートは必ずしも0度から始まらない. 後述の測定点数によるメッシュの分割数と一致させるためにstepで割る
            minPsi = int(startPsiPhi[0]/stepPsiPhi[0])
            #同上
            maxPsi = int(endPsiPhi[0]/stepPsiPhi[0])

            N_samplePhi = len(df.index) #Phi軸まわりの測定点数
            N_samplePsi = int(90/stepPsiPhi[0]) #Psi軸まわりの測定点数, 実際には90度まで測定することは稀である。 測定していない範囲は0埋めすることで対応。

            phi = np.linspace(0, 2*np.pi, N_samplePhi) #Phi軸の描画範囲を0から2πに設定, かつ測定点数で分割, これにより測定点数とメッシュの分割数が一致する
            psi = np.linspace(0, 90, N_samplePsi) #Psi軸の描画範囲を0から90度に設定, かつ測定点数で分割, これにより測定点数とメッシュの分割数が一致する

            x, y = np.meshgrid(phi, psi) #x, yはメッシュグリッドの座標値, 測定角度と実数値で一致しないことに注意（一致するのは測定点数)

            self.ax = self.fig.add_subplot(111, projection = 'polar')
            self.ax.spines['polar'].set_visible(False)
            self.ax.set_xticklabels(labels=[] , fontname="Arial", fontsize=10)
            self.ax.set_yticklabels([])
            self.ax.grid(c="black", lw=0.4)

            dummy1 = self.ax.contour(x[0 : minPsi], y[0 : minPsi], np.zeros((len(x[0 : minPsi]), N_samplePhi))) #測定していない範囲の0埋め
            polefigure = self.ax.contourf(x[minPsi : maxPsi+1], y[minPsi : maxPsi+1], df.T, 100, cmap = cm.jet) #測定している範囲のプロット
            dummy2 = self.ax.contour(x[maxPsi+1 : N_samplePsi], y[maxPsi+1 : N_samplePsi], np.zeros((len(x[maxPsi+1 : N_samplePsi]), N_samplePhi))) #測定していない範囲の0埋め

            colb = self.fig.colorbar(polefigure, pad = 0.1, orientation = 'vertical') #カラーバーの表示
            colb.set_label('', fontsize = 14)

        self.canvas.draw()

    def loadXRD(self):
        fPath = QFileDialog.getOpenFileName(self, 'Open file', '/home', 'CSV(*.csv)') #ファイルダイアログの表示
        self.dictData = {} #データを格納する辞書, データ型はdataframeとする。

        if fPath[0]: #ファイルが選択された場合, QFileDialog.getOpenFileName()の0番目の要素にファイルパスが格納されている
            with open(fPath[0], newline='') as f:
                reader = csv.reader(f) #csvファイルを読み込む, readerはイテレータ
                csvData = list(reader) #csvファイルの内容をリストに格納
                
                for i, row in enumerate(csvData): #csvファイルの内容を1行ずつ読み込む
                    if '[Scan points]' in row: #測定データの開始行を検出, 想定しているデータでは[Scan points]の直後に測定データが格納されている(2theta-omegaスキャン及びrocking curveの場合)
                        data = pd.read_csv(fPath[0], skiprows = i+1, header = 0, names = ["Angle", "TimePerStep", "Intensity", "ESD"])
                        self.dictData['data'] = data

                        for j, row in enumerate(csvData): #測定軸の種類を検出
                            if 'Scan axis' in row:
                                scanAxis = row[1] #測定軸の種類を格納, 2Theta-OmegaかOmegaが返ってくる
                                self.dictData['scanAxis/type'] = scanAxis
                                break #測定軸の種類を検出したらループを抜ける
                    
                        break #測定データの開始行を検出したらループを抜ける

                    elif i == len(csvData)-1 and '[Scan points]' not in row: #[Scan points]が最後の行まで見つからなかった場合, 極点測定では[Scan points]が存在しない
                        for j, row in enumerate(csvData):
                            if 'Time per step' in row: #測定データの開始行を検出, 極点測定の場合ではTime per stepの直後に測定データが格納されている
                                data = pd.read_csv(fPath[0], skiprows = j+1, header = None)
                                self.dictData['data'] = data
                                self.dictData['scanAxis/type'] = 'Pole Figure' #極点測定の場合はscanAxis/typeにPole Figureを格納
                                continue #測定データの開始行を検出したら次のループに移る(Psi rangeは必ず別の行にある)
                    
                            elif 'Psi range' in row: #Psi rangeの存在する行にPsiの測定範囲が格納されている, 次の行にはPhiの測定範囲が格納されている
                                #Psi rangeの存在する行とその次の行のみを読み込む
                                rangePsiPhi = pd.read_csv(fPath[0], header = None, skiprows = lambda x : x not in [j, j+1], names = ['start', 'end', 'step'])
                                self.dictData['Psi and Phi'] = rangePsiPhi
                                continue
                        
                            elif 'scanAxis/type' in self.dictData.keys() and 'Psi and Phi' in self.dictData.keys():
                                break #測定データの開始行, Psi range, Phi rangeの3つの情報を取得したらループを抜ける
                    
                    #[Scan points]が見つからなかった場合は次の行に移る
                    elif i < len(csvData)-1 and '[Scan points]' not in row:
                        continue
        
            if self.dictData['scanAxis/type'] == '2Theta-Omega':
                self.comboPlotType.setCurrentText(self.plotType[0])

            elif self.dictData['scanAxis/type'] == 'Omega':
                self.comboPlotType.setCurrentText(self.plotType[1])

            elif self.dictData['scanAxis/type'] == 'Pole Figure':
                self.comboPlotType.setCurrentText(self.plotType[2])
        
            print(self.dictData['data'], self.dictData['scanAxis/type'])
            if 'Psi and Phi' in self.dictData.keys():
                print(self.dictData['Psi and Phi'])

    #プロットしたグラフの保存を行うメソッド(実装予定)
    def saveFigure(self):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())