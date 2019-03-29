#!/usr/bin/python

import hashlib
try:
    import sha3 # requires pysha3 on python 2.7
except ImportError:
    pass # already existing in hashlib from python 3.6 onwards
from PyQt5.QtCore import pyqtSlot, pyqtSignal

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QFrame


def byteArrayToBitArray(b):
    x = [0 for _ in range(len(b)*8)]
    for j in range(len(b)):
        for i in range(8):
            x[j * 8 + i] = 1 if (b[j] & (1 << i)) > 0 else 0
    return x


def getBitSeqFromBooleanArray(bit_index, bit_length, bb):
    a = 0
    m = 1
    i = bit_index + bit_length - 1
    while i >= bit_index:
        a += m if bb[i] else 0
        m <<= 1
        i -= 1
    return a


class HashView(QWidget):

    # colors copied from XFiles' HashView.java
    colors16_ordered = (QColor(0, 0, 0), QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
                        QColor(255, 255, 255), QColor(255, 255, 0), QColor(0, 255, 255), QColor(255, 0, 255),
                        QColor(0x7F, 0, 0), QColor(0, 0x7F, 0x7F), QColor(0, 0x7F, 0), QColor(0x7F, 0x7F, 0),
                        QColor(0x7F, 0x44, 0), QColor(0x7F, 0, 0x6E), QColor(0xFF, 0x88, 0), QColor(0x7F, 0x7F, 0x7F))

    hvSignal = pyqtSignal(bytearray)

    @pyqtSlot(bytearray)
    def update_hv(self, data):
        self.data = data
        self.initUI()

    def __init__(self,data,gridSize,bitsPerCell,width,height):
        super(HashView, self).__init__()
        self.data = data
        self.gridSize = gridSize
        self.bitsPerCell = bitsPerCell
        self.width_ = width
        self.height_ = height
        self.framegrid = []
        self.initUI()
        self.hvSignal.connect(self.update_hv)

    def initUI(self):
        rSize = min(self.width_,self.height_) // self.gridSize
        outSize = self.gridSize * self.gridSize * self.bitsPerCell

        if not self.framegrid:
            for i_ in range(self.gridSize):
                row = []
                for j_ in range(self.gridSize):
                    square = QFrame(self)
                    square.setGeometry(i_ * rSize, j_ * rSize, rSize, rSize)
                    row.append(square)
                self.framegrid.append(row)

        if self.data is not None:
            h = hashlib.shake_128()
            h.update(self.data)
            outDigest = bytearray(h.digest(outSize // 8))
            bb = byteArrayToBitArray(outDigest)

            for i_ in range(self.gridSize):
                for j_ in range(self.gridSize):
                    rColor = getBitSeqFromBooleanArray(self.bitsPerCell * (self.gridSize * i_ + j_), self.bitsPerCell,
                                                       bb)
                    col = HashView.colors16_ordered[rColor]
                    self.framegrid[i_][j_].setStyleSheet("QWidget { background-color: %s }" % col.name())
        else:
            [sq.setStyleSheet("QWidget { background-color: black }") for j in self.framegrid for sq in j]

        self.setGeometry(300, 300, self.gridSize*rSize, self.gridSize*rSize)
        self.setWindowTitle('HashView')
        self.show()
        self.update()
