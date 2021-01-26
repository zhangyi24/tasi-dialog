import re
infile = open("address.txt","r")
lines = infile.read().splitlines()
outfile = open("valueset.txt","w")
for line in lines:
    alias = re.sub("[县|市|区|]","",line)
    outfile.write(f"\"{line}\":[\"{alias}\"],\n")
    
outfile.close()
infile.close()