# bizlink-Vajra_FpgaProj

## xpga_launch.sh notes

```
BASH:  xpga_launch.sh 10
ERROR: " application-specific initialization failed: couldn't load file "librdi_commontasks.so": libtinfo.so.5: cannot open shared object file: No such file or directory"

Solution: https://support.xilinx.com/s/article/76585?language=en_US

sudo apt install libtinfo-dev
sudo ln -s /lib/x86_64-linux-gnu/libtinfo.so.6 /lib/x86_64-linux-gnu/libtinfo.so.5
sudo apt-get install libtinfo5
