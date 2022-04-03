import subprocess
import os
import sys

def check_status(status):
    if status != 0:
        sys.exit("Error detected while installing dependencies")
 
def install():
    os.system('echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list')
    os.system('curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -')

    args = ["sudo"] + ["apt"] + ["update"]
    check_status(subprocess.run(args))
    args = ["sudo"] + ["apt"] + ["-y"] + ["upgrade"]
    check_status(subprocess.run(args))
    args = ["sudo"] + ["apt"] + ["-y"] + ["install"] + ["hugin-tools"] + ["enblend"] + ["imagemagick"] + ["libopencv-dev"] + ["build-essential"] + ["python3-opencv"] + ["python3-tflite-runtime"]
    check_status(subprocess.run(args))
    args = ["pip3"] + ["install"] + ["xystitch"] + ["picamerax"] + ["Flask"] + ["flask-restful"]
    check_status(subprocess.run(args))

    args = ["sudo"] + ["cp"] + ["config.txt"] + ["/boot/config.txt"]
    check_status(subprocess.run(args))

    os.mkdir('./tmp')
    os.mkdir('./tmp/stitch')
    os.mkdir('./tmp/fs')

    args = ["git"] + ["clone"] + ["https://github.com/PetteriAimonen/focus-stack.git"]
    check_status(subprocess.run(args))
    args = ["make"] 
    check_status(subprocess.run(args, cwd='./focus-stack/'))
    args = ["sudo"] + ["make"] + ["install"]
    check_status(subprocess.run(args, cwd='./focus-stack/'))
    
if __name__ = "__main__":
    install()
    
