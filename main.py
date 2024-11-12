"""
MSNAApp
作成者: 周 贇豪
作成日: 2024年11月9日
連絡先: z510389750@gmail.com
ライセンス: GPL-3.0
バージョン: 1.0.2

概要:
このアプリケーションは、ECG、BP、MSNAのデータを表示し、解析するためのツールです。

更新履歴:
バージョン1.0.0: 初版
バージョン1.0.1: Downボタン表示の修正; 出力デフォルトファイル名の異常出力の修正
バージョン1.0.2: 「Start」ボタン押した後の「Auto」ボタンの無効化

exe化:
pyinstaller --onefile --windowed --icon=image/icon.ico --add-data "main.ui;." --add-data "image/icon.ico;image" --hidden-import openpyxl.cell._writer --name MSNAAnalyzer main.py

"""

from PyQt5 import QtWidgets, uic, QtGui
import pyqtgraph as pg
import dataProcessing
import autoCheck
import numpy as np
import pandas as pd
from pathlib import Path
import os
import sys

class MSNAApp:
    def __init__(self, ui_file="main.ui"):
        # アプリケーションの初期化
        self.app = pg.mkQApp("MSNAAnalyzer")

        # 実行環境に応じたファイルパスの取得
        if getattr(sys, 'frozen', False):
            # PyInstallerで打包された場合
            base_path = sys._MEIPASS
        else:
            # 通常のスクリプト実行の場合
            base_path = os.path.dirname(os.path.abspath(__file__))
        ui_file = os.path.join(base_path, "main.ui")
        icon_file = os.path.join(base_path, "image", "icon.ico")

        self.win = uic.loadUi(ui_file)
        self.win.setWindowTitle("MSNAAnalyzer v1.0.2")
        self.win.setWindowIcon(QtGui.QIcon(icon_file))

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
        self.HR_output = []
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
        self.initialize_plots()

        # UIの各要素とメソッドを接続
        self.win.toolButton.clicked.connect(self.open_file_dialog)
        self.win.pushButton_4.clicked.connect(self.autoBurst_check)
        self.win.pushButton.clicked.connect(self.button_clicked)
        self.win.pushButton_2.clicked.connect(self.button2_clicked)
        self.win.pushButton_3.clicked.connect(self.config)
        self.win.pushButton_5.clicked.connect(self.button5_clicked)
        self.win.progressBar.setMinimum(0)
        self.win.progressBar.setMaximum(100)

        # キーイベントのハンドラを接続
        self.win.keyPressEvent = self.handle_key_press
        
        # プロットの範囲変更イベントを接続
        self.ECG_plot.sigXRangeChanged.connect(self.on_xrange_changed)
        
    def on_xrange_changed(self, viewbox):
        """X軸の範囲が変更されたときの処理
        Args:
            viewbox (pg.ViewBox): ビューボックス
        """
        min_range, max_range = viewbox.viewRange()[0]
        self.min_range = min_range
        self.max_range = max_range

    def handle_key_press(self, event):
        """キーボードイベントに基づいて処理を開始する
        Args:
            event (QKeyEvent): キーボードイベント
        """
        if event.key() == 16777234 and self.count > 0: # 左矢印キー（バーストあり）
            self.start(1)
        elif event.key() == 16777237 and self.count > 0 and self.count < len(self.peaks_ECG_arg) - 1: # 下矢印キー（バーストなし）
            self.button2_clicked()
        elif event.key() == 16777236 and self.count > 0 and self.count < len(self.peaks_ECG_arg) - 1: # 右矢印キー（エラー）
            self.button5_clicked()

    def initialize_plots(self):
        """プロットの初期化"""

        # それぞれのプロットビューを作成
        self.ECG_plot = self.win.graphicsView.addPlot()
        self.BP_plot = self.win.graphicsView_2.addPlot()
        self.MSNA_plot = self.win.graphicsView_3.addPlot()
        
        self.ECG_plot.setRange(xRange=[0, 30000], padding=0)
        self.BP_plot.setRange(xRange=[0, 30000], padding=0)
        self.MSNA_plot.setRange(xRange=[0, 30000], padding=0)
        
        # プロットの同期（範囲変更時）
        self.ECG_plot.setXLink(self.BP_plot)
        self.BP_plot.setXLink(self.MSNA_plot)

        # 各データ用のカーブを作成
        self.curve_ECG = self.ECG_plot.plot(pen='y')
        self.curve_BP = self.BP_plot.plot(pen='g')
        self.curve_MSNA = self.MSNA_plot.plot(pen='r')

        self.is_updating = False

    def update_region(self):
        """選択された範囲を更新"""
        self.min_val, self.max_val = self.region.getRegion()
        self.min_val = round(self.min_val)
        self.max_val = round(self.max_val)
        self.win.lineEdit_9.setText(str(self.min_val))
        self.win.lineEdit_10.setText(str(self.max_val))

    def drawCalculation(self, select):
        """グラフのデータを計算して描画
        Args:
            select (int): 0: ファイルを選択する前, 1: ファイルを選択した後
        """
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
        dataSet = dataProcessing.data_set(self.ECG, self.BP, self.MSNA_, self.fs)
        self.F_ECG, self.F_BP, self.F_MSNA_, self.peaks_ECG_arg, self.sbp_arg, self.dbp_arg = dataSet.read_data()
        self.F_MSNA = [x / self.MSNA_cal for x in self.F_MSNA_]
        self.peaks_ECG_arg_diff = np.diff(self.peaks_ECG_arg)

        # データをプロット
        self.curve_ECG.setData(self.F_ECG)
        self.curve_ECGpeaks = pg.PlotDataItem(
            x=self.peaks_ECG_arg, y=self.F_ECG[self.peaks_ECG_arg],
            pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=(255, 0, 0)
        )
        self.ECG_plot.addItem(self.curve_ECGpeaks)
        self.ECG_plot.setRange(xRange=[0, (self.max_range-self.min_range)], yRange=[min(self.F_ECG), max(self.F_ECG)], padding=0)

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
        self.BP_plot.setRange(yRange=[min(self.F_BP), max(self.F_BP)], padding=0)

        self.curve_MSNA.setData(self.F_MSNA)
        self.MSNA_plot.setRange(yRange=[min(self.F_MSNA), max(self.F_MSNA)], padding=0)

    def config(self):
        """設定ボタンが押されたときの処理"""
        self.win.spinBox.setEnabled(False)
        self.win.doubleSpinBox_2.setEnabled(False)
        self.win.doubleSpinBox_3.setEnabled(False)
        self.win.doubleSpinBox_4.setEnabled(False)
        self.win.pushButton_3.setEnabled(False)
        self.win.pushButton_4.setEnabled(True)
        self.win.pushButton.setEnabled(True)
        self.win.pushButton_2.setEnabled(True)
        self.win.pushButton_5.setEnabled(True)
        self.drawCalculation(1)

    def restart(self):
        """ファイル選択ときの処理"""
        self.count = 0
        self.drawCalculation(0)
        self.region = pg.LinearRegionItem([0.5 * self.fs, 1.5 * self.fs])
        self.region.sigRegionChanged.connect(self.update_region) # regionnの選択範囲の変更を監視
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
        self.win.lineEdit.setText(str(0))
        self.win.lineEdit_2.setText(str(0))
        self.win.lineEdit_3.setText(str(0))
        self.win.lineEdit_4.setText(str(0))
        self.win.lineEdit_6.setText(str(0))
        self.win.lineEdit_7.setText(str(0))
        self.win.lineEdit_8.setText(str(0))
        self.win.pushButton_4.setEnabled(False)
        self.win.pushButton.setEnabled(False)
        self.win.pushButton_2.setEnabled(False)
        self.win.pushButton_5.setEnabled(False)
        self.win.pushButton.setText("Start")
        self.win.pushButton_2.setText("Back")
        self.win.pushButton_5.setText("Close")

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
                self.MSNA_ = MSNA
                self.restart()
                self.update_region()
            except ValueError as e:
                msg_box = QtWidgets.QMessageBox(self.win)
                msg_box.setWindowTitle("Error")
                msg_box.setText(f"File format error: {e}")
                msg_box.exec_()

    def Burst_check(self, select):
        """バーストのチェック
        Args:
            select (int): 0: バーストなし, 1: バーストあり, 2: エラー
        """
        self.win.lineEdit.setText(str(self.count))
        self.region = pg.LinearRegionItem([self.r_lift, self.r_right])
        if select == 0:
            self.region.setBrush(pg.mkBrush(color=(255, 0, 0, 70)))
            self.Burst_output.append(0)
        elif select == 1:
            self.times+=1
            self.win.lineEdit_2.setText(str(self.times))
            self.region.setBrush(pg.mkBrush(color=(0, 161, 71, 70)))
            self.Burst_output.append(1)
        elif select == 2:
            self.region.setBrush(pg.mkBrush(color=(255, 255, 255, 70)))
        self.MSNA_plot.addItem(self.region)
        self.region.setMovable(False)
        self.win.progressBar.setValue(round(self.count/(len(self.peaks_ECG_arg)-2)*100))
        QtWidgets.QApplication.processEvents()

    def start(self, select):
        """スタートボタンが押されたときの処理
        Args:
            select (int): 0: バーストなし, 1: バーストあり, 2: エラー
        """
        self.win.setFocus()
        if self.start_check:
            return
        self.start_check = True
        if self.count >= len(self.peaks_ECG_arg)- 1:
            pass
        else:
            if self.count == 0:
                self.win.pushButton.setText("Burst(Left Key)")
                self.win.pushButton_2.setText("No Burst(Down Key)")
                self.win.pushButton_5.setText("Error(Right Key)")
                self.win.pushButton_4.setEnabled(False)
                self.update_region()
                self.region.setMovable(False)
                self.times = 0
            else:
                self.r_lift = self.min_val + self.peaks_ECG_arg[self.count - 1]
                self.r_right = self.max_val + self.peaks_ECG_arg[self.count - 1]
                xRange = [self.peaks_ECG_arg[self.count - 1], (self.max_range-self.min_range) + self.peaks_ECG_arg[self.count - 1]]

                if select != 2:
                    self.Rtime_output.append(self.peaks_ECG_arg[self.count - 1]/self.fs)
                    self.RRI_output.append(self.peaks_ECG_arg_diff[self.count - 1]/self.fs)
                    self.HR_output.append(60 / (self.peaks_ECG_arg_diff[self.count - 1] / self.fs))
                    self.DBPtime_output.append(self.dbp_arg[self.count - 1]/self.fs)
                    self.DBP_output.append(self.F_BP[self.dbp_arg[self.count - 1]])
                    self.SBPtime_output.append(self.sbp_arg[self.count - 1]/self.fs)
                    self.SBP_output.append(self.F_BP[self.sbp_arg[self.count - 1]])
                    self.MSNAtime_output.append(self.r_lift)
                    self.MSNAheight_output.append(max(self.F_MSNA[self.r_lift:self.r_right + 1]))
                    self.MSNAAera_output.append(sum(self.F_MSNA[self.r_lift:self.r_right + 1]))
                
                    self.win.lineEdit_6.setText(str(round(self.HR_output[-1], 2)))
                    self.win.lineEdit_7.setText(str(round(self.DBP_output[-1], 2)))
                    self.win.lineEdit_8.setText(str(round(self.SBP_output[-1], 2)))
                    self.win.lineEdit_3.setText(str(round(self.MSNAheight_output[-1], 2)))
                    self.win.lineEdit_4.setText(str(round(self.MSNAAera_output[-1], 2)))

                self.Burst_check(select)
                if self.count < len(self.peaks_ECG_arg) - 2:
                    self.ECG_plot.setRange(xRange=xRange, yRange=[min(self.F_ECG), max(self.F_ECG)], padding=0)
                    self.BP_plot.setRange(yRange=[min(self.F_BP), max(self.F_BP)], padding=0)
                    self.MSNA_plot.setRange(yRange=[min(self.F_MSNA), max(self.F_MSNA)], padding=0)
                    self.region = pg.LinearRegionItem([self.min_val + self.peaks_ECG_arg[self.count], self.max_val + self.peaks_ECG_arg[self.count]])
                    self.region.setBrush(pg.mkBrush(color=(0, 0, 0, 0)))
                    self.MSNA_plot.addItem(self.region)
                    self.region.setMovable(False)
                else:
                    self.win.lineEdit_5.setText("Save the file as .xlsx or .txt (if no extension is entered, .xlsx will be added automatically).")
                    self.win.pushButton.setText("Save or not")
                    self.win.pushButton_2.setText("Restart(Save to enable)")
                    self.win.pushButton_5.setText("Close(Save to enable)")
                    self.win.pushButton_2.setEnabled(False)
                    self.win.pushButton_5.setEnabled(False)
            self.count += 1
        self.start_check = False

    def autoBurst_check(self):
        """自動バーストチェック"""
        self.win.toolButton.setEnabled(False)
        self.win.pushButton_4.setEnabled(False)
        self.win.pushButton.setEnabled(False)
        self.win.pushButton_2.setEnabled(False)
        self.win.pushButton_5.setEnabled(False)
        self.win.lineEdit_5.setText("Auto Burst Check")
        self.update_region()
        self.region.setMovable(False)
        self.times = 0
        self.count = 1
        autoCheck_ = autoCheck.auto_check(self.F_MSNA, self.fs, self.Baseline)
        for i in range(len(self.peaks_ECG_arg) - 1):
            # プロットの範囲を設定
            xRange = [self.peaks_ECG_arg[i], (self.max_range-self.min_range) + self.peaks_ECG_arg[i]]
            self.ECG_plot.setRange(xRange=xRange, yRange=[min(self.F_ECG), max(self.F_ECG)], padding=0)
            self.BP_plot.setRange(yRange=[min(self.F_BP), max(self.F_BP)], padding=0)
            self.MSNA_plot.setRange(yRange=[min(self.F_MSNA), max(self.F_MSNA)], padding=0)
            # バーストのチェック
            self.r_lift = self.peaks_ECG_arg[i]
            self.r_right = self.peaks_ECG_arg[i + 1]
            Burst_result = autoCheck_.burst_SNR(self.min_val + self.r_lift, self.max_val + self.r_lift + 1)
            self.start(Burst_result)
        self.win.toolButton.setEnabled(True)
        self.win.pushButton.setEnabled(True)

    def back(self):
        """戻るボタンが押されたときの処理"""
        self.win.spinBox.setEnabled(True)
        self.win.doubleSpinBox_2.setEnabled(True)
        self.win.doubleSpinBox_3.setEnabled(True)
        self.win.doubleSpinBox_4.setEnabled(True)
        self.win.pushButton_3.setEnabled(True)
        self.win.pushButton_4.setEnabled(False)
        self.win.pushButton.setEnabled(False)
        self.win.pushButton_2.setEnabled(False)
        self.win.pushButton_5.setEnabled(False)
        
    def saveExcel(self):
        """Excelに保存"""
        file_path = Path(self.file)
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self.win, "Save File",  f"{file_path.stem}_result", "All Files (*)")
        
        if file_name:
            # 拡張子がない場合は.xlsxを追加
            if not any(file_name.endswith(ext) for ext in [".xlsx", ".txt"]):
                # 拡張子が指定されていないか、不正な場合
                if '.' not in file_name:
                    file_name += ".xlsx"  # 拡張子が無ければ.xlsxを追加
                else:
                    # 拡張子が不正な場合
                    self.win.lineEdit_5.setText("Invalid file extension. Please use .xlsx or .txt.")
                    self.win.lineEdit_5.setStyleSheet("color: red;")
                    return

            # 拡張子が.xlsxまたは.txtの場合のみ保存
            df = pd.DataFrame({
                "R time": self.Rtime_output,
                "RRI": self.RRI_output,
                "HR": self.HR_output,
                "DBP time": self.DBPtime_output,
                "DBP": self.DBP_output,
                "SBP time": self.SBPtime_output,
                "SBP": self.SBP_output,
                "MSNA time": self.MSNAtime_output,
                "MSNA height": self.MSNAheight_output,
                "MSNA area": self.MSNAAera_output,
                "Burst": self.Burst_output,
            })
            
            if file_name.endswith(".xlsx"):
                df.to_excel(file_name, index=False)
            elif file_name.endswith(".txt"):
                df.to_csv(file_name, sep='\t', index=False)

            self.win.lineEdit_5.setText(f"Saved to {file_name}")
        else:
            self.win.lineEdit_5.setText("Save canceled")

        self.win.pushButton_2.setEnabled(True)
        self.win.pushButton_5.setEnabled(True)

    def button_clicked(self):
        """左下ボタン「Start」が押されたときの処理"""
        if self.count >= len(self.peaks_ECG_arg) - 1:
            # Excelに保存
            self.saveExcel()
        else:
            self.start(1)

    def button2_clicked(self):
        """下中間ボタン「Back」が押されたときの処理"""
        if self.count == 0:
            self.back()
        elif self.count >= len(self.peaks_ECG_arg) - 1:
            self.restart()
        else:
            self.start(0)
            
    def button5_clicked(self):
        """右下ボタン「Close」が押されたときの処理"""
        if self.count == 0:
            self.win.close()
        elif self.count >= len(self.peaks_ECG_arg) - 1:
            self.win.close()
        else:
            self.start(2)

    def run(self):
        """アプリケーションを実行"""
        self.win.show()
        self.app.exec_()

if __name__ == "__main__":
    msna_app = MSNAApp()
    msna_app.run()
