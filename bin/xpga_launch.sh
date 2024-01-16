#!/bin/bash
#-------------------------------------------------------------------------------
# [Handle files with space in filename and output file names](https://stackoverflow.com/questions/52772654/handle-files-with-space-in-filename-and-output-file-names)
# [BASH Shell: For Loop File Names With Spaces](https://www.cyberciti.biz/tips/handling-filenames-with-spaces-in-bash.html)
#-------------------------------------------------------------------------------

cd ~/.local/share/applications
#------------------------------------------------
# Find the desktop files that match the patterns
#	 files=($(find -type f -print0 -name "Vitis*.desktop" -o -name "Vivado*.desktop" -o -name "Xilinx*.desktop" | xargs -0 ls -1 -t))
# TO Debug: for file in "${files[@]}"; do echo "$file"; done
#------------------------------------------------
IFS=$'\n' files=($(ls -1 Vitis*.desktop Vivado*.desktop Xilinx*.desktop Documentation\ Navigator*.desktop Add\ Design\ Tools*.desktop Manage\ Licenses*.desktop))

#------------------------------------------------
# Display the menu and get the user input
#------------------------------------------------
if [ -n "$1" ]; then
	REPLY=$1
	file=${files[$(($1 - 1))]}
else
	prompt="Please select a desktop file to launch:"
	PS3="$prompt "
	select file in "${files[@]}" "Quit"; do
		break
	done
fi

#------------------------------------------------
# Launch the desktop file or quit the script
#------------------------------------------------
if [[ $REPLY -ge 1 && $REPLY -le ${#files[@]} ]]; then
	echo -e "\n>>> You selected '$file' which is option $REPLY\n"
	cd $HOME 
	gtk-launch $file
elif [[ $REPLY == $(( ${#files[@]}+1 )) ]]; then
	echo "Goodbye!"
	exit
else
	echo "Invalid option. Try another one."
fi
