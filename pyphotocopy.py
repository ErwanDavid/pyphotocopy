import exifread
import os
import platform
import shutil
import re
import sys
import datetime


srcfold = ''
destroot = ''

nbr_exist = 0
nbr_new = 0

if len(sys.argv) > 2:
    srcfold = sys.argv[1]
    destroot = sys.argv[2]
else:
    print('argument are src-folder dest-folder')
    sys.exit(2)



extensionsPhoto = ['.jpg', '.png', '.jpeg', '.bmp', '.tif', '.raw']
extensionsVideo = ['.mp4', '.avi', '.flv', '.mov', '.rm', '.mpg', '.mpeg']

exclududedFiles = ('Thumbs.db','.picasa.ini')

def GetfromExif(fullfile):
    dayfolder = ''
    year = ''
    try :
        f = open(fullfile, 'rb')        # open for meta
    except :
        return ''
    tags = exifread.process_file(f)
    for tag in tags.keys():
        if tag in ('EXIF DateTimeOriginal') :
            #print('    Exif info', tag, "\t",str(tags[tag])[:30])
            datestr = str(tags[tag])
            day = datestr.split(" ")[0]
            if day.find("/") > 0:
                year = day.split('/')[0]
                dayfolder = day.replace('/','_')
            else:
                year = day.split(":")[0]
                dayfolder = day.replace(':','_')
    if dayfolder != '':
        return year + '/' + dayfolder
    else:
        return ''

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

def modif_date(path_to_file):
    if platform.system() == 'Windows':
        return os.path.getmtime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_mtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return 0

def GetfromName(fullfilelow):
    dayfolder = ''
    match = re.search(r'(20\d{6})',fullfilelow)
    try:
        day = match.group(1)
        #print "\t\t using file name :" + day
        year = day[:4]
        month = day[4:-2]
        dom = day[-2:]
        dayfolder = year + '_' + month + '_' + dom
        #print("\t\tDate from folder name 1", dayfolder)
        return year + '/' + dayfolder
    except:
        match = re.search(r'(20\d+_\d+_\d+)',fullfilelow)
        try:
            day = match.group(1)
            year = day[:4]
            dayfolder = day
            #print("\t\tDate from folder name 2", dayfolder)
            return year + '/' + dayfolder
        except:
            match = re.search(r'(20\d+-\d+-\d+)',fullfilelow)
            try:
                day = match.group(1)
                year = day[:4]
                dayfolder = day.replace('-','_')
                #print("\t\tDate from folder name 3", dayfolder)
                return year + '/' + dayfolder
            except:
                print("\t\tDate not found", dayfolder)
                return ''

def Getfromattribute(fullfile):
    date = modif_date(fullfile)
    return datetime.datetime.fromtimestamp(date).strftime('%Y/%Y_%m_%d')

def getallfile(srcfold):
    allfile = []
    for root, dirnames, filenames in os.walk(srcfold):
      for curfile in filenames:
          if curfile not in exclududedFiles :
              fullname = root + '/'  + curfile
              allfile.append(fullname)
    return allfile


# MAIN


print("Get all files in", srcfold)
allfile=getallfile(srcfold)       
print("Listed", str(len(allfile)), 'files')

for fullfile in allfile:
    fileonly = os.path.basename(fullfile)
    fullfilelow = fullfile.lower()
    print("START ", fullfile)
    folderdest = ''
    dayfolder = ''
    source = ''

    dayfolderExif = GetfromExif(fullfile)
    dayfolderName = GetfromName(fullfile)
    dayfolderAttr = Getfromattribute(fullfile)

    """
    print("\tDate from exif", dayfolderExif)
    print("\tDate from name", dayfolderName)
    print("\tDate from attr", dayfolderAttr)
    """

    if dayfolderExif != '':
        dayfolder = dayfolderExif
        source = 'exif'
    elif dayfolderName != '':
        dayfolder = dayfolderName
        source = 'name'
    elif dayfolderAttr != '':
        dayfolder = dayfolderAttr
        source = 'attr'
    else:
        dayfolder = 'unkown'

    folderdest = destroot + '/' + dayfolder + '/'
    if not os.path.isdir(folderdest):
        os.makedirs(folderdest)

    if any(ext in fullfilelow for ext in extensionsPhoto):
        if 'I_' not in fileonly[:2] :
            fulldest = folderdest + 'I_' + fileonly
        else:
            fulldest = folderdest + fileonly
    elif any(ext in fullfilelow for ext in extensionsVideo):
        if 'V_' not in fileonly[:2] :
            fulldest = folderdest + 'V_' + fileonly
        else:
            fulldest = folderdest + fileonly
    else :
        if 'UNKN_' not in fileonly :
            fulldest = folderdest + 'UNKN_' + fileonly
        else:
            fulldest = folderdest + fileonly

    print("\t SRC", fullfile, "\n\t DATE", source, "\n\t FOLD", folderdest, "\n\t DEST", fulldest)

    if(os.path.isfile(fulldest)):
        nbr_exist = nbr_exist +1
    else:
        print ("CP\t: cp ",fullfile, ' ', fulldest)
        #shutil.copy2(fullfile, fulldest)
        shutil.move(fullfile,fulldest)
        nbr_new = nbr_new +1

print ("TOTAL\t: exist",nbr_exist, 'new', nbr_new)
