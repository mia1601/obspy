# -*- coding: utf-8 -*-

from sqlalchemy import ForeignKey, Column, Integer, DateTime, Float, String, \
    PickleType, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation
from obspy.core import Trace, UTCDateTime
import numpy as np
from sqlalchemy.schema import UniqueConstraint
import pickle


Base = declarative_base()


class WaveformPath(Base):
    __tablename__ = 'default_waveform_paths'
    __table_args__ = (UniqueConstraint('path'))

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False, index=True)
    archived = Column(Boolean, default=False)

    files = relation("WaveformFile", order_by="WaveformFile.id",
                     backref="path", cascade="all, delete, delete-orphan")

    def __init__(self, data={}):
        self.path = data.get('path')

    def __repr__(self):
        return "<WaveformPath('%s')>" % self.path


class WaveformFile(Base):
    __tablename__ = 'default_waveform_files'

    id = Column(Integer, primary_key=True, index=True)
    file = Column(String, nullable=False, index=True)
    size = Column(Integer, nullable=False)
    mtime = Column(Integer, nullable=False, index=True)
    format = Column(String, nullable=False, index=True)
    path_id = Column(Integer, ForeignKey('default_waveform_paths.id'))

    channels = relation("WaveformChannel", order_by="WaveformChannel.id",
                        backref="file", cascade="all, delete, delete-orphan")

    def __init__(self, data={}):
        self.file = data.get('file')
        self.size = data.get('size')
        self.mtime = int(data.get('mtime'))
        self.format = data.get('format')

    def __repr__(self):
        return "<WaveformFile('%s')>" % (self.id)


class WaveformChannel(Base):
    __tablename__ = 'default_waveform_channels'
    __table_args__ = (UniqueConstraint('network', 'station', 'location',
                                       'channel', 'starttime', 'endtime'))

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey('default_waveform_files.id'),
                     index=True)
    network = Column(String(2), nullable=False, index=True)
    station = Column(String(5), nullable=False, index=True)
    location = Column(String(2), nullable=False, index=True)
    channel = Column(String(3), nullable=False, index=True)
    starttime = Column(DateTime, nullable=False, index=True)
    endtime = Column(DateTime, nullable=False, index=True)
    calib = Column(Float, nullable=False)
    sampling_rate = Column(Float, nullable=False)
    npts = Column(Integer, nullable=False)
    preview = Column(PickleType, nullable=True)

    gaps = relation("WaveformGaps", order_by="WaveformGaps.id",
                    backref="channel", cascade="all, delete, delete-orphan")

    features = relation("WaveformFeatures", order_by="WaveformFeatures.id",
                        backref="channel",
                        cascade="all, delete, delete-orphan")

    def __init__(self, data={}):
        self.update(data)

    def update(self, data):
        self.network = data.get('network', '')
        self.station = data.get('station', '')
        self.location = data.get('location', '')
        self.channel = data.get('channel', '')
        self.starttime = data.get('starttime')
        self.endtime = data.get('endtime')
        self.calib = data.get('calib', 1.0)
        self.npts = data.get('npts', 0)
        self.sampling_rate = data.get('sampling_rate', 1.0)
        self.preview = data.get('preview', None)

    def __repr__(self):
        return "<WaveformChannel('%s')>" % (self.id)

    def getPreview(self, apply_calibration=False):
        data = np.loads(str(self.preview))
        if apply_calibration:
            data = data * self.calib
        tr = Trace(data=data)
        tr.stats.starttime = UTCDateTime(self.starttime)
        tr.stats.delta = 60.0
        tr.stats.network = self.network
        tr.stats.station = self.station
        tr.stats.location = self.location
        tr.stats.channel = self.channel
        tr.stats.calib = self.calib
        return tr


class WaveformGaps(Base):
    __tablename__ = 'default_waveform_gaps'

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('default_waveform_channels.id'),
                        index=True)
    gap = Column(Boolean, nullable=False, index=True)
    starttime = Column(DateTime, nullable=False, index=True)
    endtime = Column(DateTime, nullable=False, index=True)
    samples = Column(Integer, nullable=False)

    def __init__(self, data={}):
        self.gap = data.get('gap', True)
        self.starttime = data.get('starttime')
        self.endtime = data.get('endtime')
        self.samples = data.get('samples', 0)

    def __repr__(self):
        return "<WaveformGaps('%s')>" % (self.id)


class WaveformFeatures(Base):
    __tablename__ = 'default_waveform_features'
    __table_args__ = (UniqueConstraint('channel_id', 'key'))

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('default_waveform_channels.id'),
                        index=True)
    key = Column(String, nullable=False, index=True)
    value = Column(PickleType, nullable=True)

    def __init__(self, data={}):
        self.key = data.get('key')
        self.value = pickle.dumps(data.get('value', None))

    def __repr__(self):
        return "<WaveformFeatures('%s')>" % (self.id)
