import sys
sys.path.insert(0,r"c:\users\administrator\appdata\local\programs\python\python38\lib\site-packages")

from threading import Thread
from time import sleep
import os

class MyThread(Thread):
    def __init__(self, func, args, name):
        super().__init__()
        self.func = func
        self.args = args
        self.name = name 

    def run(self):
        print(f"Thread-{self.name} is starting")
        self.func(self.args)
    
    def stop(self):
        super()._stop()
    
    def delete(self):
        super()._delete()

def work(delta):
    print("Thread is working")
    sleep(delta)
    print("Thread is ending")

# 子线程与主线程的关系，如果想让子线程在主线程结束之后马上结束，那么要在子线程的start方法前设置守护线程为True
# 如果想让主线程等待子线程执行完成之后主线程在退出，那么需要设置子线程的join()



import inspect
import ctypes
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)




if __name__ == "__main__":
    print("Main Thread is Start PID-%s"%(os.getpid()))
    t = MyThread(work, 5, "test_thread1")   
    t.start()
    #stop_thread(t)
    print(t.is_alive())

    


