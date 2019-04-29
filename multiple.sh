#!/bin/sh

flag=0
flag2=0
var=1

for i in $(ls Run_$1*); do 
    
    #Exec the model with or without dependencies
    if [ $flag -eq 0 ]
    then
        hid=$(qsub -terse $i)
        echo "ejecuta: "$hid
    else
        hidd=$(qsub -hold_jid $hid -terse $i)
        echo $hidd" depende de "$hid
    fi
    
    #Increas the counter and check for change of flag
    ((++var))
    if [ $var -eq 5 ]
    then 
        if [ $flag -eq 1 ]
        then
            hid=$hidd
        fi
        flag=1    
        var=1
    fi
    
done


