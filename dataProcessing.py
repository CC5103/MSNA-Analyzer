from scipy import signal
from scipy.signal import find_peaks
import numpy as np
import math

class data_set:
    def __init__(self, ECG: list, BP: list, iMSNA: list, fs: int):
        """読み込んだデータにファイルタをかけることやピークを検出することができる
        
        Args:
            ECG (list): ECGのデータ
            BP (list): BPのデータ
            iMSNA (list): rMSNAのデータ
            fs (int): サンプリング周波数
        """
        self.ECG = ECG
        self.BP = BP
        self.iMSNA = iMSNA
        self.fs = fs
    def zerofilter_sci(self, n: int, fc: int, Type: str, data: list) -> list:
        """バターワースフィルタをかける
        
        Args:
            n (int): フィルタ次数
            fc (int): カットオフ周波数
            Type (str): フィルタの種類
            data (list): フィルタをかけるデータ
        
        Returns:
            list: フィルタをかけたデータ
        """
        if Type == "band":
            b, a = signal.butter(n, [fc[0]/(self.fs/2), fc[1]/(self.fs/2)], Type, analog=False)
        else:
            b, a = signal.butter(n, fc/(self.fs/2), Type, analog=False)
        y = signal.filtfilt(b, a, data)
        return y

    def read_data(self) -> list:
        """データを読み込んで，フィルタをかけるやピークを検出する
        
        Returns:
            list: フィルタをかけたECGデータ
            list: フィルタをかけたBPデータ
            list: フィルタをかけたMSNAデータ
            list: ECGのピーク
            list: BPのsystolicピーク
            list: BPのdiastolicピーク
        """
        F_ECG = self.zerofilter_sci(2, [0.3, 28], "band", self.ECG)
        F_BP = self.zerofilter_sci(2, 10, "low", self.BP)

        # Find peaks
        peaks_ECG, _ = find_peaks(F_ECG, np.mean(F_ECG[F_ECG>0])*2.9)
        peaks_ECG_diff = np.diff(peaks_ECG)
        peaks_ECG_diff_mean = np.mean(peaks_ECG_diff)

        # Delete error peaks
        del_list = []
        for i in range(len(peaks_ECG_diff)):
            if peaks_ECG_diff[i] < 0.5 * peaks_ECG_diff_mean:
                del_list.append(i+1)
        peaks_ECG = np.delete(peaks_ECG, del_list)

        F_ECG = F_ECG[peaks_ECG[0]:peaks_ECG[-1]+1]
        F_BP = F_BP[peaks_ECG[0]:peaks_ECG[-1]+1]
        F_iMSNA = self.iMSNA[peaks_ECG[0]:peaks_ECG[-1]+1]
        
        peaks_ECG = peaks_ECG - peaks_ECG[0]
        
        sbp_arg = []
        dbp_arg = []
        for i in range(1, len(peaks_ECG)):
            sbp_arg.append(np.argmax(F_BP[peaks_ECG[i-1]:(peaks_ECG[i-1]+(peaks_ECG[i]-peaks_ECG[i-1])//2)]) + peaks_ECG[i-1])
            dbp_arg.append(np.argmin(F_BP[peaks_ECG[i-1]:(peaks_ECG[i-1]+(peaks_ECG[i]-peaks_ECG[i-1])//2)]) + peaks_ECG[i-1])

        return F_ECG, F_BP, F_iMSNA, peaks_ECG, sbp_arg, dbp_arg
    
if __name__ == "__main__":
    pass