from scipy import signal
from scipy.signal import find_peaks
import numpy as np
import math

class data_set:
    def __init__(self, ECG, BP, MSNA, fs):
        self.ECG = ECG
        self.BP = BP
        self.MSNA = MSNA
        self.fs = fs
    def zerofilter_sci(self, n, fc, Type, data):
        if Type == "band":
            b, a = signal.butter(n, [fc[0]/(self.fs/2), fc[1]/(self.fs/2)], Type, analog=False)
        else:
            b, a = signal.butter(n, fc/(self.fs/2), Type, analog=False)
        y = signal.filtfilt(b, a, data)
        return y

    def read_data(self):
        F_ECG = self.zerofilter_sci(2, [0.3, 28], "band", self.ECG)
        F_BP = self.zerofilter_sci(2, [0.3, 10], "band", self.BP)
        timeConstant = 0.1
        fc = 1/(2*math.pi*timeConstant)
        alpha = 2 * np.pi *  fc * (1/self.fs) / (2 * np.pi *  fc * (1/self.fs) + 1)
        MSNA_abs = np.abs(self.MSNA)
        phase = np.angle(MSNA_abs)
        F_MSNA = np.zeros_like(MSNA_abs)
        for n in range(1, len(MSNA_abs)):
            F_MSNA[n] = alpha * MSNA_abs[n] + (1 - alpha) * F_MSNA[n - 1]
        F_MSNA = F_MSNA * np.exp(1j * phase)
        F_MSNA = np.real(F_MSNA)
        
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
        F_MSNA = F_MSNA[peaks_ECG[0]:peaks_ECG[-1]+1]
        
        peaks_ECG = peaks_ECG - peaks_ECG[0]
        
        sbp_arg = []
        dbp_arg = []
        for i in range(1, len(peaks_ECG)):
            sbp_arg.append(np.argmax(F_BP[peaks_ECG[i-1]:(peaks_ECG[i-1]+(peaks_ECG[i]-peaks_ECG[i-1])//2)]) + peaks_ECG[i-1])
            dbp_arg.append(np.argmin(F_BP[peaks_ECG[i-1]:(peaks_ECG[i-1]+(peaks_ECG[i]-peaks_ECG[i-1])//2)]) + peaks_ECG[i-1])

        return F_ECG, F_BP, F_MSNA, peaks_ECG, sbp_arg, dbp_arg