#macafeeje APR/2026
#version 0.1

import pyvisa
import csv
from time import sleep

def pbq():
    input ("press ENTER to quit")
    quit()

def word_as_char(word):
    if word == 1:
        return "B"
    if word == 2:
        return "W"
    if word == 4:
        return "L"
    print ("word size not recognised")
    pbq()


def bin_to_str(binary, pos, word):
    if word == 1:
        return format(binary[pos], "02X")
    if word == 2:
        return format(binary[pos], "02X") + format(binary[pos+1], "02X")
    if word == 4:
        return format(binary[pos], "02X") + format(binary[pos+1], "02X") + format(binary[pos+2], "02X") + format(binary[pos+3], "02X")
    print ("word size not recognised")
    pbq()


def gpib_addr_check(addr, size, word):
    end_addr = addr + size

    if end_addr > 0x00200000:
        print ("address out of bounds")
        pbq()

    if addr % word != 0:
        print ("address not word aligned")
        pbq()

    if end_addr % word != 0:
        print ("size not word aligned")
        pbq()

    if addr == end_addr:
        print ("size is null")
        pbq()
        
    return end_addr


def gpib_read(instr, addr, size, word):
    #takes device_id, start address, size to read (in bytes), word type
    #returns the binary

    if instr == None:
        print ("instrument not setup")
        pbq()

    end_addr = gpib_addr_check(addr, size, word)
    bwl = word_as_char(word)
    binary = bytearray()
    
    while True:
        tmp = instr.query("$RM" + bwl + "H" + format(addr, 'X'))
        binary.extend(bytes.fromhex(tmp))

        addr += word
        if addr >= end_addr:
            break;

    return binary
    

def gpib_write(instr, addr, binary, word):
    #takes device_id, start address, binary file, and word type
    #writes binary to instrument

    if instr == None:
        print ("instrument not setup")
        pbq()
    
    end_addr = gpib_addr_check(addr, len(binary), word)
    bwl = word_as_char(word)
    l = 0
    print ("working...")
    
    while True:
        instr.write("$WM" + bwl + "H" + format(addr,"X") + "," + bin_to_str(binary, l, word))
        #print("$WM" + bwl + "H" + format(addr,"X") + "," + bin_to_str(binary, l, word))

        if addr >= 0x1a0000 and addr < 0x1a4000:
            sleep(0.01)     #Twc AT28C64 is max 1ms - delay required for EEPROM write
        
        addr += word
        l += word
        if addr >= end_addr:
            break;


def csv_to_binary(filename):
    try:
        with open (filename, newline='') as file:
            parser = csv.DictReader(file)
            binary = bytearray()

            try:
                for row in parser:
                    tmp = int(row["FREQ (Hz)"])
                    hw = 0
                    lw = 0
                    if tmp < 10000000:
                        lw = tmp
                    else:
                        hw = tmp // 1000000
                        lw = tmp - int(hw) * 1000000

                    binary.extend(hw.to_bytes(4, byteorder="big"))
                    binary.extend(lw.to_bytes(4, byteorder="big"))

                n_str = "ATT"
                for l in range(0, 6, 1):
                    file.seek(0)
                    parser = csv.DictReader(file, skipinitialspace=True)
                    for row in parser:
                        tmp = int(row[n_str + str(l)])
                        binary.extend(tmp.to_bytes(4, byteorder="big", signed=True))

                chksm = 0
                print ("len: " + str(len(binary)))
                for l in range(0, len(binary), 2):
                    chksm += (binary[l] << 8) + binary[l+1]
                    if chksm >= 0x10000:
                        chksm -= 0x10000

                print ("checksum: " + hex(chksm))
                binary.extend(chksm.to_bytes(2, byteorder="big", signed=False))

                if not (len(binary) == 0x522 or len(binary) == 0x502):
                    print ("output binary wrong length: " + hex(len(binary)))
                    pbq()
                    
            except:
                print ("unable to parse .csv file")
                pbq()

            file.close()
            return binary
    except FileNotFoundError:
        print ("unable to open file")
        pbq()


print ("R3x61 toolkit v0.1")
print ("******************")
print ("options:")
print ("1 - read eeprom to binary file")
print ("2 - read %custom% to binary file")
print ("3 - write binary file to eeprom")
print ("4 - write binary file to %custom%")
print ("5 - binary -> .csv comp data")
print ("6 - comp data .csv -> binary (merge)")
print ("7 - write comp data .csv -> eeprom")
print ("8 - code injection over GPIB")
print ("9 - read loop")

menu = input()
instr = None
rm = None

if menu == "1" or menu == "2" or menu == "3" or menu == "4" or menu == "7" or menu ==  "8" or menu == "9":
    print ("getting device list...")
    rm = None
    res = None
    try:
        rm = pyvisa.ResourceManager()
        res = rm.list_resources()
    except:
        print ("no devices found, or missing drivers")
        pbq()

    for r in res:
        print (" -", r)

    dev_id = input("enter device id: ")

    if dev_id == "":
        dev_id = "GPIB0::8::INSTR"      #(or press 'enter' for default id)

    for r in res:
        if dev_id == r:
            instr = rm.open_resource(dev_id, read_termination='\r')
            break

    if instr == None:
        print ("no such device listed")
        pbq()

#read
if menu == "1" or menu == "2":
    filename = input ("enter save file name: ")
    if filename == "":
        if menu == "1":
            filename = "eeprom.bin"
        else:
            filename = "binary.bin"
        print ("using default: \"" + filename + "\"")

    try:
        with open (filename, mode="wb") as file:
            addr = 0x1a0000
            size = 0x4000
            word = 4
            
            if menu == "2":
                s_addr = input("enter start address: 0x")
                s_size = input("enter size: 0x")
                s_word = input("enter word size (1 - byte, 2 - word, 4 - long): ")
                addr = int(s_addr, 16)
                size = int(s_size, 16)
                word = int(s_word, 10)

            print ("reading: 0x" + format(addr, "08X") + " to 0x" + format(addr + size - word, "08X") + "...")
            binary = gpib_read(instr, addr, size, word)
            file.write(binary)
            file.close()
            print ("done")
            
    except FileNotFoundError:
        print ("unable to save file")
        pbq()
        
#write
#print ("3 - write binary file to eeprom")
#print ("4 - write binary file to %custom%")
#print ("7 - write comp data .csv -> eeprom")
#print ("8 - code injection over GPIB")
if menu == "3" or menu == "4" or menu == "7" or menu == "8":
    filename = ""
    if menu == "7":
        filename = input ("enter .csv file name: ")
    else:
        filename = input ("enter .bin file name: ")
        
    if filename == "":
        if menu == "7":
            filename = "eeprom.csv"             #default
        elif menu == "8":
            filename = "C14-minesweeper.bin"    #default
        else:
            filename = "eeprom.bin"             #default
        print ("using default: \"" + filename + "\"")

    binary = bytearray()
    addr = 0x1a0000
    word = 2
    deq_ptr = 0
    
    if menu == "7":
        binary = csv_to_binary(filename)
        tmp = gpib_read(instr, 0x1a3fd0, 2, 2)
        if not(tmp[0] == 0x11 and tmp[1] == 0x11):
            print ("unsupported checksum type in use")
            pbq()
    else:
        try:
            with open (filename, mode="rb") as file:
                binary = file.read()
                file.close()
        except FileNotFoundError:
            print ("unable to open file")
            pbq()

    if menu == "4":
        s_addr = input ("enter start address: 0x")
        s_word = input ("enter word size (1 - byte, 2 - word, 4 - long): ")
        addr = int(s_addr, 16)
        word = int(s_word, 10)

    if menu == "8":
        #first two longs of binary are the program start address (hence (-8) for real start addr to write program)
        #and a pointer to the dynamic execution pointer DEQ_PTR (depends on firmware version) for auto run
        addr = int.from_bytes(binary[0:4], byteorder="big", signed=False) - 8
        word = 2
        deq_ptr = int.from_bytes(binary[4:8], byteorder="big", signed=False)
    
    size = len(binary)
    if menu == "3":
        if size != 0x4000:
            print ("binary file not 4k")
            pbq()

    print ("write: 0x" + format(addr, "08X") + " to 0x" + format(addr + size - word, "08X") + ", word=" + word_as_char(word))
    cont = input ("memory will be overwritten, continue? y/n: ")
    if cont != "y":
        pbq()

    gpib_write(instr, addr, binary, word)
    print ("done")
    
    if menu == "8":
        run = input ("run? y/n: ")
        if run == "y":
            binary = addr.to_bytes(4, byteorder="big", signed=False)
            gpib_write(instr, 0x102768, binary, 4)
            print ("done")
        
#binary -> .csv
if menu == "5":
    filename = input ("enter .bin filename: ")
    if filename == "":
        filename = "eeprom.bin"                                 #default
        print ("using default: \"" + filename + "\"")

    try:
        with open (filename, mode='rb') as file:
            data = file.read()
            if len(data) != 0x4000:
                print ("binary file not 4k")
                pbq()

            if not (data[0x3fd0] == 0x11 and data[0x3fd1] == 0x11):
                print ("unrecognised compensation type")
                print (hex(data[0x3fd0]))
                print (hex(data[0x3fd1]))
                pbq()
            
            savefilename = input ("enter .csv savefile name: ")
            if savefilename == "":
                savefilename = "eeprom.csv"                     #default
                print ("using default: \"" + savefilename + "\"")

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
                pbq()
                
            file.close()
            print ("done")

    except FileNotFoundError:
        print ("unable to open file: " + filename)
        pbq()
    pbq()

#.csv -> binary (merge)
if menu == "6":
    filename = input("enter original binary filename: ")
    if filename == "":
        filename = "eeprom.bin"                                 #default
        print ("using default: \"" + filename + "\"")

    binary_in = None
    try:
        with open (filename, mode="rb") as file:
            binary_in = file.read()
            file.close()

            if len(binary_in) != 0x4000:
                print ("binary file not 4k")
                pbq()

            if not (binary_in[0x3fd0] == 0x11 and binary_in[0x3fd1] == 0x11):
                print ("unrecognised compensation type")
                print (hex(binary_in[0x3fd0]))
                print (hex(binary_in[0x3fd1]))
                pbq()
                
    except FileNotFoundError:
        print ("unable to open file: " + filename)
        pbq()

    csvfilename = input ("enter .csv file name: ")
    if csvfilename == "":
        csvfilename = "eeprom.csv"                              #default
        print ("using default: \"" + csvfilename + "\"")
        
    binary = csv_to_binary(csvfilename)
    for l in range(len(binary), len(binary_in), 1):
        binary.append(binary_in[l])

    filename = input ("enter output binary filename: ")
    if filename == "":
        filename = "eeprom_corr.bin"
        print ("using default: \"" + filename + "\"")

    try:
        with open (filename, mode="wb") as file:
            file.write(binary)
            file.close()
            
    except FileNotFoundError:
        print ("unable to save file")
        pbq()
    print ("done")

if menu == "9":
    s_addr = input ("enter start address: 0x")
    s_word = input ("enter word size (1 - byte, 2 - word, 4 - long): ")
    addr = int(s_addr, 16)
    word = int(s_word, 10)

    while True:
        try:
            tmp = gpib_read(instr, addr, word, word)
            print (bin_to_str(tmp, 0, word))
        except:
            print ("unable to read...")
            break

if instr != None:
    instr.control_ren(6)
if rm != None:
    rm.close()
pbq()
