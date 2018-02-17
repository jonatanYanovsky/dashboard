import time
import csv


with open('radical.entk.task_manager.0000-proc.prof') as csvfile:

	for row in csvfile.readlines(): # read every line in the file
		array = row.split(',') # split row into elements
        	first_item = array[0] # get first element in row
		if first_item != '#time' and first_item != "": # cleanup
			date_item = time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(float(first_item)))   #epoch to date format 
			print(date_item)
