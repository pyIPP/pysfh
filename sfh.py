from ctypes import cdll, c_int16, c_uint16, c_int32, c_uint32, c_uint64, c_char_p, byref, c_void_p, _sys, c_buffer
from os import environ
import numpy
import StringIO
import sys

libsfh = cdll.LoadLibrary('/afs/ipp-garching.mpg.de/aug/ads/%s/lib64/libsfh8.so' % environ['SYS'])

__type__ = {numpy.int8:1,
            ' ':2,
            numpy.int16:3,
            numpy.int32:4,
            numpy.float32:5,
            numpy.float64:6,
            numpy.bool:7,
            numpy.uint16:9,
            numpy.int64:13,
            numpy.uint32:14,
            numpy.uint64:15,
            ' '*8:1794,
            ' '*16:3842,
            ' '*32:7938,
            ' '*48:12034,
            ' '*64:16130,
            ' '*72:18178}

def GetError(error):
    try:
        err = c_int32(error)
    except TypeError:
        err = error
    if err.value==0:
        return
    userstring = ''
    string = c_char_p(userstring)
    length = c_uint64(0)
    libsfh.sfherror_(byref(err), string, length);
    raise Exception('libsfh error occured.')

class ObjectInfo(object):
    def __init__(self, name, type, nDim, nSteps, format):
        object.__init__(self)
        self.name = name
        for el in ['type', 'nDim', 'nSteps', 'format']:
            try:
                vars(self)[el] = numpy.uint32(vars()[el].value)
            except AttributeError:
                vars(self)[el] = numpy.uint32(vars()[el])


class ShotfileHeader(object):
    def __init__(self, filename=None):
        object.__init__(self)
        self.sfhref = c_int32(0)
        if filename != None:
            self.open(filename)

    def __del__(self):
        self.close()

    def open(self, filename):
        self.close()
        try:
            name = c_char_p(filename)
        except TypeError:
            name = c_char_p(filename.encode())
        namel = c_uint64(len(filename))
        error = c_int32(0)
        libsfh.sfhopen_(byref(error), name, byref(self.sfhref), namel)
        GetError(error)

    def close(self):
        if not self.status:
            return
        error = c_int32(0)
        libsfh.sfhclose_(byref(error), byref(self.sfhref))
        GetError(error)
        self.sfhref.value = 0

    def status():
        def fget(self):
            return self.sfhref.value!=0
        return locals()
    status = property(**status())

    def GetObjects(self):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        error = c_int32(0)
        listlen = c_int16(100)
        namelist = b' '*8*100
        onaml = c_uint64(8*100)
        onamlist = c_char_p(namelist)
        objectType = numpy.zeros(100, dtype=numpy.uint16)
        libsfh.sfhlonam_(byref(error), byref(self.sfhref), byref(listlen), onamlist, objectType.ctypes.data_as(c_void_p), onaml)
        GetError(error)
        outputNames = []
        outputType = []
        for i in xrange(100):
            if objectType[i]!=0:
                outputNames.append(namelist[i*8:(i+1)*8].strip())
                outputType.append(objectType[i])
        return outputNames, numpy.uint32(outputType)

    def GetPhysDim(self, name):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        error = c_int32(0)
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        physdim = c_uint16(0)
        libsfh.sfhrdphysdim_(byref(error), byref(self.sfhref), onam, byref(physdim), onaml)
        GetError(error)
        return numpy.uint16(physdim.value)

    def GetObjectInfo(self, name):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        error = c_int32(0)
        objtyp = c_uint16(0)
        numDim = c_uint32(0)
        length = c_uint32(0)
        sfh_format = c_uint16(0)
        onaml = c_uint64(len(name))
        libsfh.sfhrdobj_(byref(error), byref(self.sfhref), onam, byref(objtyp), byref(numDim), byref(length), byref(sfh_format), onaml)
        GetError(error)
        return ObjectInfo(name, objtyp, numDim, length, sfh_format)

    def GetStatus(self, name):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        error = c_int32(0)
        status = c_int32(0)
        onaml = c_uint64(len(name))
        libsfh.sfhrstatus_(byref(error), byref(self.sfhref), onam, byref(status), onaml)
        GetError(error)
        return numpy.int32(status.value)

    def SetStatus(self, name, status):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        error = c_int32(0)
        stat = c_int32(status)
        onaml = c_uint64(len(name))
        libsfh.sfhwstatus_(byref(error), byref(self.sfhref), onam, byref(stat), onaml)
        GetError(error)

    def GetModus(self):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        error = c_int32(0)
        modus = b' '*8
        _modus = c_char_p(modus)
        length = c_uint64(8)
        libsfh.sfhrdgmod_(byref(error), byref(self.sfhref), _modus, length)
        GetError(error)
        return modus.strip().replace('\x00', '')

    def SetModus(self, modus):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        error = c_int32(0)
        try:
            mod = c_char_p(modus)
        except TypeError:
            mod = c_char_p(modus.encode())
        modusl = c_uint64(len(modus))
        libsfh.sfhdiagmod_(byref(error), byref(self.sfhref), modus, modusl)
        GetError(error)

    def NewObject(self, name, objectType, subType):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        objtype = c_uint16(objectType)
        subtype = c_uint16(subType)
        libsfh.sfhnewobj_(byref(error), byref(self.sfhref), onam, byref(objtype), byref(subtype), onaml)
        GetError(error)

    def GetFormat(self, name):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        sfh_format = c_uint16(0)
        libsfh.sfhrdformat_(byref(error), byref(self.sfhref), onam, byref(sfh_format), onaml)
        GetError(error)
        return numpy.uint16(sfh_format.value)

    def ModifyFormat(self, name, format):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            form = numpy.uint16(__type__[format])
        except KeyError:
            form = numpy.uint16(format)
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        sfh_format = c_uint16(form)
        libsfh.sfhmdformat_(byref(error), byref(self.sfhref), onam, byref(sfh_format), onaml)
        GetError(error)

    def GetNSteps(self, name):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        steps = c_uint32(0)
        libsfh.sfhrdnsteps_(byref(error), byref(self.sfhref), onam, byref(steps), onaml)
        GetError(error)
        return numpy.uint32(steps.value)

    def ModifyName(self, name, newName):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        try:
            nonam = c_char_p(newName)
        except TypeError:
            nonam = c_char_p(newName.encode())
        error = c_int32(0)
        nonaml = c_uint64(len(newName))
        libsfh.sfhmonam_(byref(error), byref(self.sfhref), onam, nonam, onaml, nonaml)
        GetError(error)

    def Rename(self, newDiagName):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(newDiagName)
        except TypeError:
            onam = c_char_p(newDiagName.encode())
        onaml = c_uint64(len(newDiagName))
        error = c_int32(0)
        libsfh.sfhrename_(byref(error), byref(self.sfhref), onam, onaml);
        GetError(error)

    def ModifyTimebase(self, name, nVals):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        nvals = c_uint32(nVals)
        libsfh.sfhmodtim_(byref(error), byref(self.sfhref), onam, byref(nvals), onaml)
        GetError(error)

    def ModifyText(self, name, text):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        try:
            tex = c_char_p(text)
        except TypeError:
            tex = c_char_p(text.encode())
        texl = c_uint64(len(text))
        error = c_int32(0)
        libsfh.sfhmtext_(byref(error), byref(self.sfhref), onam, tex, onaml, texl)
        GetError(error)

    def SetRelation(self, name, relation):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        try:
            relName = c_char_p(relation)
        except TypeError:
            relName = c_char_p(relation.encode())
        relNamel = c_uint64(len(relation))     
        error = c_int32(0)
        libsfh.sfhstrel_(byref(error), byref(self.sfhref), onam, relName, onaml, relNamel)
        GetError(error)

    def ModifyRelation(self, name, oldRelation, newRelation):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        try:
            oldrelname = c_char_p(oldRelation)
        except TypeError:
            oldrelname = c_char_p(oldRelation.encode())
        oldrelnamel = c_uint64(len(oldRelation))     
        try:
            newrelname = c_char_p(newRelation)
        except TypeError:
            newrelname = c_char_p(newRelation.encode())
        newrelnamel = c_uint64(len(newRelation))     
        error = c_int32(0)
        libsfh.sfhmdrel_(byref(error), byref(self.sfhref), onam, oldrelname, newrelname, onaml, oldrelnamel, newrelnamel)
        GetError(error)

    def DeleteRelation(self, name, relation):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        try:
            relName = c_char_p(relation)
        except TypeError:
            relName = c_char_p(relation.encode())
        relNamel = c_uint64(len(relation))     
        error = c_int32(0)
        libsfh.sfhdelrel_(byref(error), byref(self.sfhref), onam, relName, onaml, relNamel)
        GetError(error)

    def GetIndex1(self, name):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        index1 = c_uint32(0)
        libsfh.sfhrdindex1_(byref(error), byref(self.sfhref), onam, byref(index1), onaml)
        GetError(error)
        return numpy.uint32(index1.value)

    def GetIndex24(self, name):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        index2 = c_uint32(0)
        index3 = c_uint32(0)
        index4 = c_uint32(0)
        libsfh.sfhrdindex24_(byref(error), byref(self.sfhref), onam, byref(index2), byref(index3), byref(index4), onaml)
        GetError(error)
        return numpy.uint32(index2.value), numpy.uint32(index3.value), numpy.uint32(index4.value)

    def ModifyIndex1(self, name, index1):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        ind1 = c_uint32(index1)
        libsfh.sfhmdindex1_(byref(error), byref(self.sfhref), onam, byref(ind1), onaml)
        GetError(error)

    def ModifyIndex24(self, name, index2, index3, index4):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        ind2 = c_uint32(index2)
        ind3 = c_uint32(index3)
        ind4 = c_uint32(index4)
        libsfh.sfhmdindex24_(byref(error), byref(self.sfhref), onam, byref(ind2), byref(ind3), byref(ind4), onaml)
        GetError(error)

    def DeviceInfo(self, name):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        error = c_int32(0)
        crnum = c_int16(0)
        stnum = c_int32(0)
        libsfh.sfhdevinfo_(byref(error), byref(self.sfhref), onam, byref(crnum), byref(stnum), onaml)
        GetError(error)
        return numpy.int16(crnum.value), numpy.int32(stnum.value)

    def SetRelationTimebase(self, name, timebase):
        if not self.status:
            raise Exception('Shotfile Header not open.')
        try:
            onam = c_char_p(name)
        except TypeError:
            onam = c_char_p(name.encode())
        onaml = c_uint64(len(name))
        try:
            tbnam = c_char_p(timebase)
        except TypeError:
            tbname = c_char_p(timebase.encode())
        tbnaml = c_uint64(len(timebase))
        error = c_int32(0)
        libsfh.sfhstreltb_(byref(error), byref(self.sfhref), onam, tbnam, onaml, tbnaml)
        GetError(error)



    
