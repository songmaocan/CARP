"""
2020-3-11
功能：求解ARC
版本：1.0
"""
from model import ADMM
import time
def main():
    start_time=time.time()
    mod=ADMM()
    mod.g_Alternating_Direction_Method_of_Multipliers()
    end_time=time.time()
    spend_time=end_time-start_time
    mod.output_to_file(spend_time)
    print("程序用时{}分钟".format(spend_time/60))

if __name__=="__main__":
    main()