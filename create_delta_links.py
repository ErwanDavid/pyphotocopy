import sys, os
from datetime import datetime


srcfold = ''
destroottof = ''

date_format = "%Y_%m_%d"

if len(sys.argv) > 2:
    srcfold = sys.argv[1]
    destroottof = sys.argv[2]
else:
    print('Usage : create_delta_links.py source-dir dest-dir')
    sys.exit(2)

naissance_luc = '2014_07_25'
naissance_marcus = '2013_03_12'

dt_luc = datetime.strptime(naissance_luc, date_format)
dt_marcus = datetime.strptime(naissance_marcus, date_format)


def normalize(agedays):
    return str(int(agedays / 10)*10)

def linkfolder(src, luc, marcus):
    lucfolder = os.path.join(destroottof, luc)
    marcusfolder = os.path.join(destroottof, marcus)
    if not os.path.exists(lucfolder) and not '-' in lucfolder :
        os.makedirs(lucfolder)
    if not os.path.exists(marcusfolder):
        os.makedirs(marcusfolder)
    for root, dirs, files in os.walk(src):
        for name in files:
            if '-' in luc:
                print("Luc trop petit")
            else:
                namedst = "luc_" + luc +'_' + name
                #print("link src", os.path.join(root, name), "to", os.path.join(lucfolder, namedst))
                os.symlink(os.path.join(root, name), os.path.join(lucfolder, namedst))
            namedst = "marcus_" + marcus +'_' + name
            #print("link src", os.path.join(root, name), "to", os.path.join(marcusfolder, namedst))
            os.symlink(os.path.join(root, name), os.path.join(marcusfolder, namedst))

print("Source", srcfold)
for root, dirs, files in os.walk(srcfold):
    for name in dirs:
        folder = os.path.join(root, name)
        print ("F:", folder)
        try:
            dt_folder = datetime.strptime(name, date_format)
            delta_luc = dt_folder - dt_luc
            delta_marcus = dt_folder - dt_marcus
            if delta_marcus.days < 0:
                print(folder, 'trop tot')
            else:
                age_normal_luc = normalize(delta_luc.days)
                age_normal_marcus = normalize(delta_marcus.days)
                print("date", name, "Luc", delta_luc.days, "", age_normal_luc, "Marcus", delta_marcus.days, "", age_normal_marcus)
                linkfolder(folder,age_normal_luc,age_normal_marcus)
        except:
            print('Skip', folder)

