#!/bin/bash
#------------------------------------------------------------------------------------
do_combine_CSV() {

	pushd $1
	TID=$(basename `pwd`);

	for HWID in 111A 112A; do
		COMBINE_ALL="../Combine_ALL.${TID}-${HWID}.csv"
		for RATE in 10G 25G 26G 28G 51G 53G 56G 106G 112G; do
			echo -e "To do combine_CSV on $TID::Sn${HWID}_${RATE}"
			# check FILE exists or not
			if ls Sn${HWID}_${RATE}.*-[0-9]*.csv > /dev/null 2>&1; then
				COMBINE_ONE="../Combine_Sn${HWID}_${RATE}.$TID.csv"
				echo "TID, HWID, RATE, YK-QUAD, `head -1 Sn${HWID}_${RATE}.YK-Quad_204_CH0-*.csv`"  >  $COMBINE_ONE;
				for QUAD in 202 203 204 205; do
					for CH in 0 1 2 3; do
						# check FILE exists or not
						if ls Sn${HWID}_${RATE}.YK-Quad_${QUAD}_CH${CH}-[0-9]*.csv > /dev/null 2>&1; then
							# f="Sn111A_53G.YK-Quad_204_CH2-1615.csv"   =>  q="Sn111A_53G.YK-Quad_204_CH2"
							f=$(ls -1 Sn${HWID}_${RATE}.YK-Quad_${QUAD}_CH${CH}-[0-9]*.csv | tail -1)    # pick the last one if many
							q=`echo $f | sed "s/Sn${HWID}_${RATE}.YK-//;  s/-[0-9]*.csv//"`;
							echo "$TID, $HWID, $RATE, $q, `tail -1 $f`" >> $COMBINE_ONE;
						fi
					done
				done
				cat $COMBINE_ONE >> $COMBINE_ALL
			fi
		done
	done

	popd
	echo -e "\n\n"
}

do_combine_CSV $1

exit
#------------------------------------------------------------------------------------
Usage: combine_YK_CSV.sh $TID_PATH

for d in `find -type d -name TID_\*`; do ./combine_YK_CSV.sh $d; done

#------------------------------------------------------------------------------------
RATE=51G; ls YK_CSV_Files/*/*${RATE}*  YK_SlicerData_Files/*/*${RATE}*

#------------------------------------------------------------------------------------
tree -L 1 YK_CSV_Files/
YK_CSV_Files/
├── TID_B2.sn111_B1.sn112.2024-0708
└── TID_B5.sn111_B3.sn112.2024-0708


tree -L 1 YK_CSV_Files/TID_B5.sn111_B3.sn112.2024-0708
YK_CSV_Files/TID_B5.sn111_B3.sn112.2024-0708
├── Sn111A_10G.YK-Quad_202_CH0-1444.csv
├── Sn111A_10G.YK-Quad_202_CH1-1444.csv
├── Sn111A_10G.YK-Quad_202_CH2-1444.csv
...
├── Sn112A_56G.YK-Quad_205_CH0-1534.csv
├── Sn112A_56G.YK-Quad_205_CH1-1534.csv
├── Sn112A_56G.YK-Quad_205_CH2-1534.csv
└── Sn112A_56G.YK-Quad_205_CH3-1534.csv

#------------------------------------------------------------------------------------