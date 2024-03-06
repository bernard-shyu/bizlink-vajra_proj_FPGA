#!/bin/bash
#----------------------------------------------------------------------------
export TFTPBOOT=/srv/tftp

#source /fpga_share/Xilinx_tools/PetaLinux/2023.2/components/yocto/buildtools_extended/environment-setup-x86_64-petalinux-linux
source /fpga_share/Xilinx_tools/PetaLinux/2023.2/settings.sh > /dev/null 2>&1
# cd /fpga_share/Xilinx_tools/PetaLinux/2023.2/; source settings.sh > /dev/null 2>&1; cd - > /dev/null

cat <<-END
	#---------------------------------------------------------------------------------------------------------------------------------------------
	BSP=xilinx-vck190-v2023.2-10140544.bsp
	PRJ=vck190
	SD_CARD_FAT32=XXX    # SD card 1st partition, in FAT32 format
	SD_CARD_EXT4=YYY

	#---------------------------------------------------------------------------------------------------------------------------------------------
	ln -s /srv/common_fpga/xilinx.development-kit/2023.2/\$BSP
	petalinux-create -t project -n \$PRJ -s ./\$BSP

	cd \$PRJ; ln -s ln -s ../../top.xsa system.xsa
	petalinux-config --get-hw-description=. --silentconfig

	cd build/; mv downloads downloads.BXU_`date +%F`; ln -s /fpga_share/Xilinx_tools/PetaLinux/sstate-cache.downloads_2023.2 downloads; cd -
	petalinux-build

	petalinux-package --boot --u-boot --force

	# Analysing the device tree
	#---------------------------------------------------------------------------------------------------------------------------------------------
	cd images/linux/
	dtc --out-format dts --out BXU_devicetree.dts system.dtb

	# boot PetaLinux image from SD Card
	#---------------------------------------------------------------------------------------------------------------------------------------------
	cp -v BOOT.BIN image.ub boot.scr \$SD_CARD_FAT32
	tar xzf rootfs.tar.gz -C \$SD_CARD_EXT4;  ls \$SD_CARD_EXT4/*

END
