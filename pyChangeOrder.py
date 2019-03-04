from __future__ import with_statement

import os
import exifread
import sys
import errno
import os
import pathlib
import re
import hashlib

import time

from pymongo import MongoClient
from fuse import FUSE, FuseOSError, Operations


client = MongoClient('mongodb://localhost:27017/')
db = client['myphoto']
coll = db['photo_and_video_201902b']

def sha256sum(filename):
    h  = hashlib.sha256()
    b  = bytearray(128*1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        for n in iter(lambda : f.readinto(mv), 0):
            h.update(mv[:n])
    return h.hexdigest()

def GetfromExif(fullfile):
    dayfolder = ''
    return_exif = {}
    try :
        f = open(fullfile, 'rb')        # open for meta
    except :
        return ''
    tags = exifread.process_file(f, details=False)
    if 'JPEGThumbnail' in tags.keys():
        tags["JPEGThumbnail"] = ''
    for tag in tags.keys():
        #print(tag, "\t",str(tags[tag])[:30])
        if tag != 'JPEGThumbnail' : 
            return_exif[tag] = str(tags[tag])[:100]

        if 'DateTimeOriginal' in tag:
            #print('  date found in exif', tag, "\t",str(tags[tag]))
            datestr = str(tags[tag])
            if datestr.find("/") > 0:
                dayfolder = datestr.replace('/','_').replace(' ', '-')
            else:
                dayfolder = datestr.replace(':','_').replace(' ', '-')
    if dayfolder != '':
        return dayfolder, return_exif
    else:
        return False, return_exif


def _get_all_path(directory):
    print("    _get_all_path from", directory)
    coll.remove()
    cpt = 0
    for path in sorted(pathlib.Path(directory).rglob('*')):
        if path.is_file() : 
            folderdate,exif_obj = GetfromExif(str(path))
            sha256 = sha256sum(str(path))
            if folderdate:
                cpt += 1
                mongoObj = {}
                mongoObj['root'] = directory
                mongoObj['depth'] = len(path.relative_to(directory).parts)
                mongoObj['ext'] = path.suffix.lower()
                mongoObj['fpath'] = str(path)
                mongoObj['file'] = path.name
                mongoObj['st_size'] = path.stat().st_size
                mtime = path.stat().st_mtime
                mongoObj['st_mtime'] = mtime
                mongoObj['Exif'] = exif_obj
                mongoObj['sha256'] = sha256
                #mongoObj['fuseFolder'] = time.strftime('%Y-%m', time.gmtime(mtime))
                
                # try:
                    # found = re.search('(20\d\d_\d\d)_', mongoObj['fpath']).group(1)
                # except AttributeError:
                    # # AAA, ZZZ not found in the original string
                    # print("Error date on ", mongoObj)
                    # found = 'ERROR'
                mongoObj['fuseFolder'] = folderdate[:7]
                appModel = ''
                if 'Image Model' in exif_obj.keys():
                    appModel = exif_obj['Image Model']
                    #print("appModel 1", appModel)
                    appModel = re.sub(r"\s+", "_", appModel)
                    appModel = re.sub(r"_$", "", appModel)
                    #print("appModel 2", appModel)
                    appModel = re.sub(r"[^0-9A-Za-z\-_]+", "", appModel)
                    #print("appModel 3", appModel)
                    appModel = appModel[:30]
                else:
                    appModel ='unknown'
                strFuse = folderdate.replace('_', '') + '_' + appModel + '_' + mongoObj['sha256'][:10] + mongoObj['ext']
                #print("strFuse", strFuse)
                mongoObj['fuseCamera'] = appModel
                mongoObj['fuseFile'] = strFuse # mongoObj['file']
                mongoObj['fusePath'] = mongoObj['fuseFolder'] + '/' + mongoObj['fuseFile']
                
                try: #print("Obj", mongoObj)
                    coll.insert(mongoObj)
                except:
                    print("Error cannot insert", mongoObj['fusePath'])
        
        

class Passthrough(Operations):
    
    def __init__(self, root):
        print("Init...")
        #_get_all_path(root)
        self.root = root
    # Helpers
    # =======

    def _full_path(self, partial):
        
        if partial.startswith("/"):
            partial = partial[1:]
        fileObj = coll.find_one({"fusePath" : partial})
        path = fileObj["fpath"]
        print("    _fullpath: ", partial, "to", path)
        return path
        
    # Filesystem methods
    # ==================

    def access(self, path, mode):
        print("Access", path)

    def getattr(self, path, fh=None):
        print("Getattr", path)
        if path.startswith("/"):
                path = path[1:]
        fileObj = coll.find_one({"fusePath" : path})
        myDic = {}
        if fileObj:
            myDic['st_atime'] = fileObj["st_mtime"]
            myDic['st_ctime'] = fileObj["st_mtime"]
            myDic['st_gid']   = 1000
            myDic['st_mode']  = 33279
            myDic['st_mtime'] = fileObj["st_mtime"]
            myDic['st_nlink'] = 1
            myDic['st_size']  = fileObj["st_size"]
            myDic['st_uid']   = 1000
        else:
            st = os.lstat(self.root)
            myDic = dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                         'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        print("    DIC", myDic)
        return myDic

    def readdir(self, path, fh):
        print("Readdir", path)
        dirents = ['.', '..']
        if path == '/':
            dirents.extend(coll.find().distinct("fuseFolder"))
        else:
            if path.startswith("/"):
                path = path[1:]
                dirents.extend(coll.find({"fuseFolder" : path}).distinct("fuseFile"))
        print("    list", dirents)
        for r in dirents:
            yield r


    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # File methods
    # ============

    def open(self, path, flags):
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)
    def flush(self, path, fh):
        return os.fsync(fh)
        
    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)


def main(mountpoint, root):
    FUSE(Passthrough(root), mountpoint, nothreads=True, allow_other=True,  foreground=False)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
