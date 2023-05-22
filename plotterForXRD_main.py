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
import scipy.special
import scipy.optimize
import scipy.signal
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

        labelPlotType = QLabel("Plot Type", self.controlPanel)

        self.comboPlotType = QComboBox(self.controlPanel)
        self.plotType =['2theta-omega', 'Rocking Curve', 'Pole Figure']
        self.comboPlotType.addItems(i for i in self.plotType)

        self.comboSaveExt = QComboBox(self.controlPanel)
        self.saveExt =['PNG(*.png)', 'PDF(*.pdf)', 'SVG(*.svg)']
        self.comboSaveExt.addItems(i for i in self.saveExt)

        btnLoad = QPushButton("Browse", self.controlPanel)
        btnLoad.clicked.connect(self.loadXRD)

        btnPlot = QPushButton("Plot", self.controlPanel)
        btnPlot.clicked.connect(self.plotXRD)

        btnSave = QPushButton("Save", self.controlPanel)
        btnSave.clicked.connect(self.saveFigure)

        typeLayout = QHBoxLayout()
        typeLayout.addWidget(labelPlotType)
        typeLayout.addWidget(self.comboPlotType)

        btnLayout = QHBoxLayout()
        btnLayout.addWidget(btnLoad)
        btnLayout.addWidget(btnPlot)

        saveLayout = QHBoxLayout()
        saveLayout.addWidget(self.comboSaveExt)
        saveLayout.addWidget(btnSave)

        ctrlLayout = QVBoxLayout()
        ctrlLayout.addLayout(typeLayout)
        ctrlLayout.addLayout(btnLayout)
        ctrlLayout.addLayout(saveLayout)

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
            plotRockingCurve = self.ax.plot(df['Angle'], df['Intensity']/np.max(df['Intensity']), c = "red", lw = 0.8)
            fit = self.getFWHMofRCbyFitting(df['Angle'], df['Intensity']/np.max(df['Intensity']))
            FWHM = self.getFWHMofRCbyFitting(df['Angle'], df['Intensity']/np.max(df['Intensity']))['FWHM']

            print(fit)
            print(f'FWHM of rocking curve is {FWHM} deg.')

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

    #プロットしたグラフの保存を行う
    def saveFigure(self):
        fileType = self.comboSaveExt.currentText()

        fPath = QFileDialog.getSaveFileName(self, 'Save file', '/home', fileType) #ファイルダイアログの表示
        if fPath[0]:
            self.fig.savefig(fPath[0], dpi = 300, bbox_inches = 'tight', pad_inches = 0.1, transparent = True)

    def getFWHMofRCbyFitting(self, x, y):#rocking curveのピークのFWHMをフィッティングで求める
        dataNo = len(x)-1
        x_start, x_end = x[0], x[dataNo]
        y_start, y_end = y[0], y[dataNo]
        matrix_coef = np.array([[x_start, 1], [x_end, 1]]) #matrix_coef: matrix coefficient, 2x2の行列
        matrix_y = np.array([y_start, y_end]) #matrix_y: matrix y, 2x1の行列
        Slope_Intercept = np.linalg.solve(matrix_coef, matrix_y) #Slope_Intercept: Slope and Intercept, 2x1の行列
        a, b = Slope_Intercept[0], Slope_Intercept[1] #a, b: Slope and Intercept, 1次関数の傾きと切片
        B_x = a*x+b #B_x: B(x), 1次関数の式

        def voigt(x, *params): #Voigt関数を定義
            voigtFunction = np.zeros_like(x)

            intensity = params[0]
            center = params[1]
            gaussianWidth = params[2]
            naturalWidthCu = 2.5 #Cuの自然幅, 単位はeV
            #delLambda = 1239*naturalWidthCu/(4*(8047.8**2) - naturalWidthCu**2) #delLambda: delta lambda, 単位はnm
            lorentzianWidth = 1.44640182e-04 #単位はdeg

            z = (x - center + 1j*lorentzianWidth)/(gaussianWidth * np.sqrt(2.0))
            w = scipy.special.wofz(z)
            voigtFunction = intensity * np.real(w) / (gaussianWidth * np.sqrt(2.0 * np.pi))

            return voigtFunction
        
        y_sub = y-B_x #y_sub: y subtracted B_x, 線形バックグラウンドを除いたデータ
        guess_init = (np.max(y), (x_end-x_start)/2, 0.5) #フィッティングの初期値を設定, [ピークの高さ, ピークの中心, ガウシアン幅], ローレンチアン幅は2.5(Cu Ka1の自然幅)として固定する
        constraint = ([0, x_start, 0], [np.inf, x_end, np.inf]) #フィッティングの制約条件を設定, [ピークの高さ, ピークの中心, ガウシアン幅]
        popt, pcov = scipy.optimize.curve_fit(voigt, x, y_sub, p0 = guess_init, bounds = constraint, maxfev = 10000) #フィッティングを行う
        
        paramName = ['intensity', 'peak position', 'Wid_g']
        dictOptParams = {paramName[i] : popt[i] for i in range(len(paramName))} #フィッティングの結果を格納
        dictOptParams['FWHM'] = 2.0*np.sqrt(2.0*np.log(2.0))*dictOptParams['Wid_g'] #FWHM = 2.3548*Wid_g, FWHM: Full Width at Half Maximum, ピークの半分の高さになる幅

        return dictOptParams

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())