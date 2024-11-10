import numpy as np

class auto_check():
    def __init__(self, MSNA: list, fs: int, baseline: float):
        """バーストのSN比を求め, MSNAのバーストを検出する

        Args:
            MSNA (list): iMSNAのデータ
            fs (int): サンプリング周波数
            baseline (float): ベースライン(設定値)
        """
        super().__init__()
        self.MSNA = MSNA
        self.fs = fs
        self.baseline = baseline

    def burst_SNR(self, R0: int, R1: int) -> 0 | 1:
        '''バーストのSN比を求め, MSNAのバーストを検出する
        
        Args:
            MSNA_window (np.array): MSNAのデータ
            R0 (int): 区間の始点
            R1 (int): 区間の終点
        
        Returns:
            0 | 1: バーストの有無
        '''
        F_MSNA_window = self.MSNA[R0:R1]
        F_MSNA_max_arg = np.argmax(F_MSNA_window)
        F_MSNA_max = np.max(F_MSNA_window)
        if F_MSNA_max_arg == 0:
            F_MSNA_min = F_MSNA_max
        else:
            F_MSNA_min = np.min(F_MSNA_window[:F_MSNA_max_arg])
        SNR = F_MSNA_max / F_MSNA_min

        if SNR > (1 + self.baseline * 0.01):
            Burst = 1
        else:
            Burst = 0
        return Burst

if  __name__ == "__main__":
    pass