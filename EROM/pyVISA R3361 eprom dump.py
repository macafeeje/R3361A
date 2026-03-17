print ("loading...")
import pyvisa

print ("getting device list:")
rm = pyvisa.ResourceManager()
res = rm.list_resources()

if not res:
    print ("no devices found, or missing drivers")
    quit()
else:
    for r in res:
        print (" -",r)

dev_id = input("enter device id: ")

if dev_id == "":
    dev_id = "GPIB0::8::INSTR"      #(or press 'enter' for default id)

dev_found = False
for r in res:
    if dev_id == r:
        dev_found = True
        break

if not dev_found:
    print ("no such device listed")
    quit()

instr = rm.open_resource(dev_id, read_termination='\r')

#eprom dump
address = 0x1a0000                  #start address
size = 0x4000                       #size to read
word_size = 2                       #read byte (1), word(2), long-word(4)

end_address = address + size
bwl = ""

if (word_size == 1):
    bwl = "B"
if (word_size == 2):
    bwl = "W"
if (word_size == 4):
    bwl = "L"
if bwl == "":
    print ("word_size out of bounds")
    quit()

if address + size > 0x20000000:
    print ("address out of bounds")
    quit()
    
print("working...")

with open ("eeprom.bin", mode="wb") as file:
    while True:
        tmp = instr.query("$RM" + bwl + "H" + format(address, 'X'))
        file.write(bytes.fromhex(tmp))
        #print(tmp)                 #verbose (slow)
        
        address += word_size
        if address >= end_address:
            break;
        
instr.control_ren(6)
rm.close()

print("done")
