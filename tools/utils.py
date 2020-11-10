# 该模块用于创建临时文件和目录，它可以跨平台使用。
import tempfile
import time
import os
import shutil
import _thread as thread

def check_and_delete(fp, wait=0):
    """ 
    检查并删除文件/文件夹

    :param fp: 文件路径
    """
    def run():
        if wait > 0:
            time.sleep(wait)
        if isinstance(fp, str) and os.path.exists(fp):
            if os.path.isfile(fp):
                os.remove(fp)
            else:
                shutil.rmtree(fp)
    
    thread.start_new_thread(run, ())

def write_temp_file(data, suffix, dirs,mode='w+b'):
    """ 
    写入临时文件

    :param data: 数据
    :param suffix: 后缀名
    :param mode: 写入模式，默认为 w+b
    :returns: 文件保存后的路径
    """
    if not os.path.exists(dirs):
            os.mkdir(dirs)
    with tempfile.NamedTemporaryFile(mode=mode, suffix=suffix, dir=dirs,delete=False) as f:
        f.write(data)
        tmpfile = f.name
    return tmpfile