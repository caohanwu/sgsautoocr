#每次运行前需要清除浏览器图片缓存
import subprocess
from multiprocessing import Process, Queue,Event

class MitmCommandRunner:
    def __init__(self):
        self.command = ['mitmdump', '-s', r'G:\cao\sanguosha\autoSanGuoSha\linshi4\mitmproxy_py.py', '-q']

    def run_command(self,queue,event):
        event.set()
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in iter(process.stdout.readline, b''):
            queue.put(line.decode('utf-8').strip())

    def read_queue(self,queue):
        """ 读取队列中的内容，直到队列为空"""
        content = []
        while True:
            try:
                item = queue.get(timeout=1)
                content.append(item)
            except Exception as e:
                break
        return content

if __name__ == '__main__':
    run = MitmCommandRunner()
    q = Queue()
    cmd_process = Process(target=run.run_command, args=(q,))
    cmd_process.start()
    print(run.read_queue(q))
    input("Press Enter to continue...")
    print(run.read_queue(q))

