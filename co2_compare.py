#import mraa
import time
import string
import os
import subprocess


from datetime import datetime

import co2_compare_config as Conf

fields = Conf.fields
values = Conf.values

def upload_data():
	CSV_items = ['device_id','date','time','s_t0','s_h0','s_g8','s_gh']
	pairs = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S").split(" ")
	values["device_id"] = Conf.DEVICE_ID
	values["ver_app"] = Conf.Version
	values["date"] = pairs[0]
	values["time"] = pairs[1]
	
	values["tick"] = 0
	try:
		with open('/proc/uptime', 'r') as f:
			values["tick"] = float(f.readline().split()[0])
	except:
		print "Error: reading /proc/uptime"
		
	msg = ""
	for item in values:
		if Conf.num_re_pattern.match(str(values[item])):
			msg = msg + "|" + item + "=" + str(values[item]) + ""
		else:
			tq = values[item]
			tq = tq.replace('"','')
			msg = msg + "|" + item + "=" + tq 

	restful_str = "wget -O /tmp/last_upload.log \"" + Conf.Restful_URL + "topic=" + Conf.APP_ID + "&device_id=" + Conf.DEVICE_ID + "&key=" + Conf.SecureKey + "&msg=" + msg + "\""
	os.system(restful_str)

	msg = ""
	for item in CSV_items:
		if item in values:
			msg = msg + str(values[item]) + '\t'
		else:
			msg = msg + "N/A" + '\t'
	
	try:
		with open(Conf.FS_SD + "/" + values["date"] + ".txt", "a") as f:
			f.write(msg + "\n")
	except:
		print "Error: writing to SD"

def display_data(disp):
	global connection_flag
	pairs = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S").split(" ")
	disp.setCursor(0,0)
	disp.write('{:16}'.format("ID: " + Conf.DEVICE_ID))
        disp.setCursor(1,0)                                                                
        disp.write('{:16}'.format("Date: " + pairs[0]))
	disp.setCursor(2,0)                                                                
        disp.write('{:16}'.format("Time: " + pairs[1]))
	disp.setCursor(3,0)                                                                                                                              
        disp.write('{:16}'.format('Temp: %.2fC' % values["s_t0"]))
	disp.setCursor(4,0)                                                                
        disp.write('{:16}'.format('  RH: %.2f%%' % values["s_h0"]))
	disp.setCursor(5,0)                                                                                                            
        disp.write('{:16}'.format('CO2_S8: %dppm' % values["s_g8"]))
	disp.setCursor(6,0)                                                                                                            
        disp.write('{:16}'.format('CO2_hw: %dppm' % values["s_gh"]))

    	disp.setCursor(7,0)
	temp = '{:16}'.format(Conf.DEVICE_IP)
	disp.write(temp)

	disp.setCursor(7,15)
    	temp = connection_flag
    	disp.write(temp)
	
def reboot_system():
	process = subprocess.Popen(['uptime'], stdout = subprocess.PIPE)
	k = process.communicate()[0]

	items = k.split(",")
	k = items[-3]
	items = k.split(" ")
	k = float(items[-1])

	if k>1.5:
		os.system("echo b > /proc/sysrq-trigger")

def check_connection():
	global connection_flag
	if(os.system('ping www.google.com -q -c 1  > /dev/null')):
		connection_flag = "X"
	else:
		connection_flag = "@"

if __name__ == '__main__':
	if Conf.Sense_Tmp==1:
		tmp_data = '1'
		tmp = Conf.tmp_sensor.sensor(Conf.tmp_q)
		tmp.start()
		tmp_data = {'Tmp':0.0, 'RH':0}
	if Conf.Sense_S8==1:
                gas_s8_data = '2'
                gas_S8 = Conf.gas_S8_sensor.sensor(Conf.S8_q)
                gas_S8.start()
        if Conf.Sense_hw==1:
		gas_hw_data = '3'
		gas_hw = Conf.gas_hw_sensor.sensor(Conf.hw_q)
		gas_hw.start()

	disp = Conf.upmLCD.SSD1306(0, 0x3C)
	disp.clear()

	count = 0

	values["s_t0"] = 0
	values["s_h0"] = 0
	values["s_g8"] = 0
        values["s_gh"] = 0

	while True:
		reboot_system()
		check_connection()

		if Conf.Sense_Tmp==1 and not Conf.tmp_q.empty():
			while not Conf.tmp_q.empty():
				tmp_data = Conf.tmp_q.get()
                        for item in tmp_data:                                                                 
                                if item in fields:                                                                
                                        values[fields[item]] = tmp_data[item]                                     
					if Conf.float_re_pattern.match(str(values[fields[item]])):
						values[fields[item]] = round(float(values[fields[item]]),2)
                                else:                                                                             
                                        values[item] = tmp_data[item]
		if Conf.Sense_S8==1 and not Conf.S8_q.empty():
			while not Conf.S8_q.empty():
				gas_S8_data = Conf.S8_q.get()
                        for item in gas_S8_data:                                                                 
                                if item in fields:                                                                
                                        values[fields[item]] = gas_S8_data[item]                                     
					if Conf.float_re_pattern.match(str(values[fields[item]])):
						values[fields[item]] = round(float(values[fields[item]]),2)
                                else:                                                                             
                                        values[item] = gas_S8_data[item]                                             
		if Conf.Sense_hw==1 and not Conf.hw_q.empty():
                        while not Conf.hw_q.empty():
                                gas_hw_data = Conf.hw_q.get()
                        for item in gas_hw_data:
                                if item in fields:
                                        values[fields[item]] = gas_hw_data[item]
                                        if Conf.float_re_pattern.match(str(values[fields[item]])):
                                                values[fields[item]] = round(float(values[fields[item]]),2)
                                else:
                                        values[item] = gas_hw_data[item]

                display_data(disp)
		if count == 0:
			upload_data()
			
		count = count + 1
		count = count % (Conf.Restful_interval / Conf.Interval_LCD)
		time.sleep(Conf.Interval_LCD)
		

					
