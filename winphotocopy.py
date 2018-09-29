import exifread
import os
import platform
import shutil
import re
import sys
import datetime


srcfold = ''
destroottof = ''
destrootvid = ''
nbr_exist = 0
nbr_new = 0

if len(sys.argv) > 3:
    srcfold = sys.argv[1]
    destroottof = sys.argv[2]
    destrootvid = sys.argv[3]
else:
    print('argument are src-folder dest-photo dest-video')
    sys.exit(2)



extensionsPhoto = ['.jpg', '.png', '.jpeg', '.bmp']

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
                dayfolder = day
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
          if curfile not in ('Thumbs.db','.picasa.ini'):
              fullname = root + '/'  + curfile
              allfile.append(fullname)
    return allfile


# MAIN


print("Get all files in", srcfold)
allfile=getallfile(srcfold)       
print("Listed", str(len(allfile)), 'files')

for fullfile in allfile:
    fullfilelow = fullfile.lower()
    #print("START ", fullfile)
    folderdest = ''
    dayfolder = ''
    # Get from exif
    dayfolder = GetfromExif(fullfile)
    #print("\tDate from exif", dayfolder)
    if dayfolder == '':
        dayfolder = GetfromName(fullfilelow)
        #print("\tDate from name", dayfolder)

    if dayfolder == '':
        dayfolder = Getfromattribute(fullfile)
        #print("\tDate from attr", dayfolder)

    if dayfolder == '' :
        folderdest = destrootvid + '/unkown'
    else:
        if any(ext in fullfilelow for ext in extensionsPhoto):
            folderdest = destroottof + '/' + dayfolder
        else:
            folderdest = destrootvid + '/' + dayfolder

    print("File", fullfile, "DEST", folderdest)


    if not os.path.isdir(folderdest):
        if folderdest != '':
            os.makedirs(folderdest)
    try:
        fileonly = os.path.basename(fullfile)
        fulldest = folderdest + '/' + fileonly
        if(os.path.isfile(fulldest)):
            nbr_exist = nbr_exist +1
        else:
            print ("CP\t: cp ",fullfile, ' ', folderdest)
            shutil.copy2(fullfile, folderdest)
            nbr_new = nbr_new +1
    except:
        print  ("Error on ",fullfile)
print ("TOTAL\t: exist",nbr_exist, 'new', nbr_new)
