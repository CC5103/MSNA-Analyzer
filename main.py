"""
MSNAApp
作成者: 周 贇豪
作成日: 2024年11月9日
連絡先: z510389750@gmail.com
ライセンス: MIT
バージョン: 1.0.0

概要:
このアプリケーションは、ECG、BP、MSNAのデータを表示し、解析するためのツールです。
"""

from PyQt5 import QtWidgets, uic
import pyqtgraph as pg
import dataImport
import numpy as np

class MSNAApp:
    def __init__(self, ui_file="main.ui"):
        # アプリケーションの初期化
        self.app = pg.mkQApp("MSNAAnalyzer")
        self.win = uic.loadUi(ui_file)
        self.win.setWindowTitle("MSNAAnalyzer")

        # 初期化するグローバル変数
        self.count = 0 # カウント変数（処理の進行状況を追跡）
        self.file = None  # ファイル名（後で選択される）
        self.curve_ECGpeaks = None  # ECGピークのデータ
        self.curve_dbp = None  # DBP（拡張期血圧）のデータ
        self.is_updating = False  # 更新中フラグ
        self.start_check = False  # スタート状態をチェックするフラグ
        
        # 出力データを格納するリスト
        self.Rtime_output = []
        self.RRI_output = []
        self.HR_optput = []
        self.DBP_output = []
        self.DBPtime_output = []
        self.SBP_output = []
        self.SBPtime_output = []
        self.MSNAtime_output = []
        self.MSNAheight_output = []
        self.MSNAAera_output = []
        self.Burst_output = []

        # プロットの初期化
        pg.setConfigOptions(antialias=True) # アンチエイリアスを有効にする
        self.region = pg.LinearRegionItem() # 選択範囲を示す線形領域アイテム
        self.initialize_plots()

        # UIの各要素とメソッドを接続
        self.win.toolButton.clicked.connect(self.open_file_dialog)
        self.win.pushButton.clicked.connect(lambda: self.start(1))
        self.win.pushButton_2.clicked.connect(self.button2_clicked)
        self.win.pushButton_3.clicked.connect(self.config)
        self.region.sigRegionChanged.connect(self.update_region)
        self.win.progressBar.setMinimum(0)
        self.win.progressBar.setMaximum(100)
        self.win.progressBar.setValue(0)

        # キーイベントのハンドラを接続
        self.win.keyPressEvent = self.handle_key_press

    def handle_key_press(self, event):
        """キーボードイベントに基づいて処理を開始する"""
        if event.key() == 16777234 and self.count > 0: # 左矢印キー（前進）
            self.start(1)
        elif event.key() == 16777236 and self.count > 0: # 右矢印キー（後退）
            self.button2_clicked()

    def initialize_plots(self):
        """プロットの初期化"""

        # それぞれのプロットビューを作成
        self.ECG_plot = self.win.graphicsView.addPlot()
        self.BP_plot = self.win.graphicsView_2.addPlot()
        self.MSNA_plot = self.win.graphicsView_3.addPlot()

        # プロットの同期（範囲変更時）
        self.ECG_plot.sigRangeChanged.connect(lambda: self.sync_plots(self.ECG_plot))
        self.BP_plot.sigRangeChanged.connect(lambda: self.sync_plots(self.BP_plot))
        self.MSNA_plot.sigRangeChanged.connect(lambda: self.sync_plots(self.MSNA_plot))

        # 各データ用のカーブを作成
        self.curve_ECG = self.ECG_plot.plot(pen='y')
        self.curve_BP = self.BP_plot.plot(pen='g')
        self.curve_MSNA = self.MSNA_plot.plot(pen='r')

    def sync_plots(self, source_plot):
        """プロットの同期: 1つのプロットを変更すると他のプロットの範囲も変更する"""
        if self.is_updating:
            return

        current_x_range = source_plot.viewRange()[0]
        
        self.is_updating = True

        if source_plot != self.ECG_plot:
            self.ECG_plot.setRange(xRange=current_x_range)
        if source_plot != self.BP_plot:
            self.BP_plot.setRange(xRange=current_x_range)
        if source_plot != self.MSNA_plot:
            self.MSNA_plot.setRange(xRange=current_x_range)

        self.is_updating = False

    def update_region(self):
        """選択された範囲を更新"""
        self.min_val, self.max_val = self.region.getRegion()
        self.min_val = round(self.min_val)
        self.max_val = round(self.max_val)
        print(self.min_val, self.max_val)

    def drawCalculation(self, select):
        """グラフのデータを計算して描画"""
        if self.curve_ECGpeaks:
            if select == 0:
                self.ECG_plot.deleteLater()
                self.BP_plot.deleteLater()
                self.MSNA_plot.deleteLater()
                self.initialize_plots()
            else:
                self.curve_ECG.clear()
                self.curve_BP.clear()
                self.curve_MSNA.clear()
                self.ECG_plot.removeItem(self.curve_ECGpeaks)
                self.BP_plot.removeItem(self.curve_dbp)

        # UIから値を取得
        self.fs = self.win.spinBox.value()
        self.ECGTrig = self.win.doubleSpinBox_2.value()
        self.Baseline = self.win.doubleSpinBox_3.value()
        self.MSNA_cal = self.win.doubleSpinBox_4.value()

        # MSNAの補正
        self.MSNA = [x / self.MSNA_cal for x in self.MSNA]
        dataSet = dataImport.data_set(self.ECG, self.BP, self.MSNA, self.fs)
        self.F_ECG, self.F_BP, self.F_MSNA, self.peaks_ECG_arg, self.sbp_arg, self.dbp_arg = dataSet.read_data()
        self.peaks_ECG_arg_diff = np.diff(self.peaks_ECG_arg)

        # データをプロット
        self.curve_ECG.setData(self.F_ECG)
        self.curve_ECGpeaks = pg.PlotDataItem(
            x=self.peaks_ECG_arg, y=self.F_ECG[self.peaks_ECG_arg],
            pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=(255, 0, 0)
        )
        self.ECG_plot.addItem(self.curve_ECGpeaks)
        self.ECG_plot.setRange(xRange=[0, 20000], yRange=[min(self.F_ECG), max(self.F_ECG)])

        self.curve_BP.setData(self.F_BP)
        self.curve_sbp = pg.PlotDataItem(
            x=self.sbp_arg, y=self.F_BP[self.sbp_arg],
            pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=(255, 0, 0)
        )
        self.BP_plot.addItem(self.curve_sbp)
        self.curve_dbp = pg.PlotDataItem(
            x=self.dbp_arg, y=self.F_BP[self.dbp_arg],
            pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=(255, 0, 0)
        )
        self.BP_plot.addItem(self.curve_dbp)
        self.BP_plot.setRange(xRange=[0, 20000], yRange=[min(self.F_BP), max(self.F_BP)])

        self.curve_MSNA.setData(self.F_MSNA)
        self.MSNA_plot.setRange(xRange=[0, 20000], yRange=[min(self.F_MSNA), max(self.F_MSNA)])

    def config(self):
        """設定ボタンが押されたときの処理"""
        self.win.spinBox.setEnabled(False)
        self.win.doubleSpinBox_2.setEnabled(False)
        self.win.doubleSpinBox_3.setEnabled(False)
        self.win.doubleSpinBox_4.setEnabled(False)
        self.win.pushButton_3.setEnabled(False)
        self.win.pushButton.setEnabled(True)
        self.win.pushButton_2.setEnabled(True)
        self.drawCalculation(1)

    def restart(self):
        """ファイル選択ときの処理"""
        self.count = 0
        self.drawCalculation(0)
        self.region = pg.LinearRegionItem([0.5 * self.fs, 1.5 * self.fs])
        self.region.setBrush(pg.mkBrush(color=(0, 0, 0, 0)))
        self.MSNA_plot.addItem(self.region)
        self.win.lineEdit_5.setText(self.file)
        self.region.setMovable(True)
        self.win.spinBox.setEnabled(True)
        self.win.doubleSpinBox_2.setEnabled(True)
        self.win.doubleSpinBox_3.setEnabled(True)
        self.win.doubleSpinBox_4.setEnabled(True)
        self.win.pushButton_3.setEnabled(True)
        self.win.progressBar.setValue(0)
        self.win.pushButton.setEnabled(False)
        self.win.pushButton_2.setEnabled(False)
        self.win.pushButton.setText("Start")
        self.win.pushButton_2.setText("Back")

    def open_file_dialog(self):
        """ファイル選択ダイアログ"""
        self.file, _ = QtWidgets.QFileDialog.getOpenFileName(self.win, "Select a file", "", "Text Files (*.txt)")
        if self.file:
            ECG, BP, MSNA = [], [], []
            try:
                with open(self.file, "r") as f:
                    for line in f:
                        data = line.split()
                        if len(data) != 3:
                            raise ValueError("Invalid file format")
                        ECG.append(float(data[0]))
                        BP.append(float(data[1]))
                        MSNA.append(float(data[2]))
                self.ECG = ECG
                self.BP = BP
                self.MSNA = MSNA
                self.restart()
            except ValueError as e:
                msg_box = QtWidgets.QMessageBox(self.win)
                msg_box.setWindowTitle("Error")
                msg_box.setText(f"File format error: {e}")
                msg_box.exec_()

    def Burst_check(self, select):
        """バーストのチェック"""
        self.win.lineEdit.setText(str(self.count))
        self.region = pg.LinearRegionItem([self.r_lift, self.r_right])
        if select == 0:
            self.region.setBrush(pg.mkBrush(color=(255, 0, 0, 70)))
            self.Burst_output.append(0)
        else:
            self.times+=1
            self.win.lineEdit_2.setText(str(self.times))
            self.region.setBrush(pg.mkBrush(color=(0, 161, 71, 70)))
            self.Burst_output.append(1)
        self.MSNA_plot.addItem(self.region)
        self.region.setMovable(False)
        self.win.progressBar.setValue(round(self.count/len(self.peaks_ECG_arg)*100))
        print(round(self.count/len(self.peaks_ECG_arg)*100))
        QtWidgets.QApplication.processEvents()

    def start(self, select):
        """スタートボタンが押されたときの処理"""
        self.win.setFocus()
        if self.start_check:
            return
        self.start_check = True
        if self.count == len(self.peaks_ECG_arg)- 1:
            # self.win.pushButton.setText("OK")
            # self.win.pushButton_2.setText("OK")
            pass
        else:
            if self.count == 0:
                self.win.pushButton.setText("Burst(Left Key)")
                self.win.pushButton_2.setText("No Burst(Right Key)")
                self.update_region()
                self.region.setMovable(False)
                self.times = 0
            else:
                self.r_lift = self.min_val + self.peaks_ECG_arg[self.count - 1]
                self.r_right = self.max_val + self.peaks_ECG_arg[self.count - 1]
                xRange = [0 + self.peaks_ECG_arg[self.count - 1], 20000 + self.peaks_ECG_arg[self.count - 1]]

                self.Rtime_output.append(self.peaks_ECG_arg[self.count - 1])
                self.RRI_output.append(self.peaks_ECG_arg_diff[self.count - 1])
                self.HR_optput.append(60 / (self.peaks_ECG_arg_diff[self.count - 1] / self.fs))
                self.DBP_output.append(self.F_BP[self.dbp_arg[self.count - 1]])
                self.DBPtime_output.append(self.dbp_arg[self.count - 1])
                self.SBP_output.append(self.F_BP[self.sbp_arg[self.count - 1]])
                self.SBPtime_output.append(self.sbp_arg[self.count - 1])
                self.MSNAtime_output.append(self.r_lift)
                self.MSNAheight_output.append(max(self.F_MSNA[self.r_lift:self.r_right + 1]))
                self.MSNAAera_output.append(sum(self.F_MSNA[self.r_lift:self.r_right + 1]))
                
                self.win.lineEdit_3.setText(str(self.MSNAheight_output[-1]))
                self.win.lineEdit_4.setText(str(self.MSNAAera_output[-1]))

                self.Burst_check(select)
                if self.count < len(self.peaks_ECG_arg) - 2:
                    self.ECG_plot.setRange(xRange=xRange, yRange=[min(self.F_ECG), max(self.F_ECG)])
                    self.BP_plot.setRange(xRange=xRange, yRange=[min(self.F_BP), max(self.F_BP)])
                    self.MSNA_plot.setRange(xRange=xRange, yRange=[min(self.F_MSNA), max(self.F_MSNA)])
                    self.region = pg.LinearRegionItem([self.min_val + self.peaks_ECG_arg[self.count], self.max_val + self.peaks_ECG_arg[self.count]])
                    self.region.setBrush(pg.mkBrush(color=(0, 0, 0, 0)))
                    self.MSNA_plot.addItem(self.region)
                    self.region.setMovable(False)
                # else:
                #     self.win.pushButton.setText("Finish")
                #     self.win.pushButton_2.setText("Back")
            self.count += 1
        self.start_check = False

    def back(self):
        """戻るボタンが押されたときの処理"""
        self.win.spinBox.setEnabled(True)
        self.win.doubleSpinBox_2.setEnabled(True)
        self.win.doubleSpinBox_3.setEnabled(True)
        self.win.doubleSpinBox_4.setEnabled(True)
        self.win.pushButton_3.setEnabled(True)
        self.win.pushButton.setEnabled(False)
        self.win.pushButton_2.setEnabled(False)

    def button2_clicked(self):
        """後退ボタンが押されたときの処理"""
        if self.count == 0:
            self.back()
        else:
            self.start(0)

    def run(self):
        """アプリケーションを実行"""
        self.win.show()
        self.app.exec_()


if __name__ == "__main__":
    msna_app = MSNAApp()
    msna_app.run()
