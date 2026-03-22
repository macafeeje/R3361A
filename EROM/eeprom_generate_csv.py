#generates a CSV file to be modified for calibration
#generates a binary file from a CSV of modified calibration data

print ("1 - binary -> .csv file")
print ("2 - .csv file -> binary")
mode = input("")

if mode == "1":
    filename = input("enter filename: ")
    if filename == "":
        filename = "eeprom.bin"                                 #default

    try:
        with open (filename, mode='rb') as file:
            data = file.read()
            if len(data) != 0x4000:
                print ("binary file not 4k")
                quit()

            if not (data[0x3fd0] == 0x11 and data[0x3fd1] == 0x11):
                print ("unrecognised compensation type")
                print (hex(data[0x3fd0]))
                print (hex(data[0x3fd1]))
                quit()
            
            savefilename = input("enter save file name: ")
            if savefilename == "":
                savefilename = "eeprom.csv"                     #default

            try:
                with open (savefilename, mode='w') as savefile:
                    freq_addr = 0                               #start of freq data
                    freq_bin_size = 41                          #number of freq
                    att_addr = 0x148                            #start addr of comp data
                    att_size = 164                              #size of one comp data set
                    att_bin_size = 6                            #number of comp data sets
                    
                    savefile.write("FREQ (Hz), ATT0, ATT1, ATT2, ATT3, ATT4, ATT5, \n")         ### comp data may not be in this order... ###

                    for l in range(0,freq_bin_size,1):
                        #calc freq
                        freq = (data[freq_addr] << 24) + (data[freq_addr+1] << 16) + (data[freq_addr+2] << 8) + data[freq_addr+3]
                        freq = freq * 1000000
                        freq_addr = freq_addr + 4
                        freq = freq + ((data[freq_addr] << 24) + (data[freq_addr+1] << 16) + (data[freq_addr+2] << 8) + data[freq_addr+3])
                        freq_addr = freq_addr + 4
                        
                        savefile.write(str(freq) + ", ")

                        #calc comp
                        for i in range(0,att_bin_size,1):
                            tmp_addr = att_addr + i * att_size
                            att = (data[tmp_addr] << 24) + (data[tmp_addr+1] << 16) + (data[tmp_addr+2] << 8) + data[tmp_addr+3]
                            if att & 0x80000000:
                                att = att - 0x100000000
                                
                            if i < att_bin_size - 1:
                                savefile.write(str(att) + ", ")
                            else:
                                savefile.write(str(att) + "\n")
                        att_addr = att_addr + 4

                    savefile.close()
                    
            except FileNotFoundError:
                print ("unable to save file: " + savefilename)
                quit()
                
            file.close()
            print ("done")

    except FileNotFoundError:
        print  ("unable to open file: " + filename)
        quit()
    quit()

if mode == "2":
    print ("not implemented")
    quit()

print ("no selection")
