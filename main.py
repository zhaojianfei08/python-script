# --*--coding:utf-8--*--

import time
from redis import StrictRedis
import snap7
from threading import Thread
import logging
from struct import pack, unpack


class MemoryMap(object):
    """ A class from plc memory to redis """
    DB_AREA = 0X84
    M_AREA = 0X83
    Q_AREA = 0X82
    I_AREA = 0X81

    def __init__(self,
                 addr="192.168.2.1",
                 tcp_port=102,
                 rack=0,
                 slot=1,
                 host="127.0.0.1",
                 port=6379,
                 password=None,
                 ):
        self.addr = addr
        self.tcp_port = tcp_port
        self.rack = rack
        self.slot = slot
        self.host = host
        self.port = port
        self.password = password

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.ERROR)
        self.ch = logging.StreamHandler()
        self.ch.setFormatter(logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s"))
        self.logger.addHandler(self.ch)


    def conn_plc(self):

        plc_client = snap7.client.Client()
        while True:
            try:
                plc_client.connect(self.addr, self.rack, self.slot)
                if plc_client.get_connected():
                    break
            except Exception as e:
                self.logger.error(e)

            time.sleep(2)
        return plc_client

    def get_data(self, area, db_num, start, size):
        plc_client = self.conn_plc()
        raw_data = None
        try:
            raw_data = plc_client.read_area(area, db_num, start, size)
        except Exception as e:
            self.logger.error(e)
        return raw_data

    def handle_data(self):
        raw_data = self.get_data(self.DB_AREA, 1, 0, 1000)
        # bytearray_bytes
        bytes_data = bytes(raw_data)
        data = unpack('B' * 1000, bytes_data)
        return data

    def write_data(self, area, db_num, start, bytes_data):
        plc_client = self.conn_plc()
        try:
            plc_client.write_area(area, db_num, start, bytes_data)
        except Exception as e:
            self.logger.error(e)

    def create_redis_client(self):
        redis_store = None
        try:
            redis_store = StrictRedis(host=self.host,
                                      port=self.port,
                                      password=self.password,
                                      decode_responses=True)
        except Exception as e:
            self.logger.error(e)
        return redis_store

    def upload_data(self):
        """
         function: transfer data from local to cloud_redis
         detect data every second
        """
        redis_store = self.create_redis_client()
        buffer = tuple()
        while True:
            try:
                data = self.handle_data()
                if data != buffer:
                    for index, byte in enumerate(data):
                        redis_store.hset("byte_data", f"VB{index}", byte)
                buffer = data
            except Exception as e:
                self.logger.error(e)
            time.sleep(1)

    def download_data(self, func):
        redis_store = None
        try:
            redis_store = self.create_redis_client()
        except Exception as e:
            self.logger.error(e)
        while True:
            try:
                previous_dict = redis_store.hgetall('byte_data')  # type:dict
                previous_key = list(previous_dict.keys())
                time.sleep(1)
                next_dict = redis_store.hgetall('byte_data')  # type:dict
                for key in previous_key:
                    if next_dict.get(key) != previous_dict.get(key):
                        func(key)
            except Exception as e:
                self.logger.error(e)

    def download_callback(self, *args):
        try:
            redis_store = self.create_redis_client()
            value = redis_store.hget('byte_data', args[0])
            byte_value = pack('B', int(value))
            self.write_data(self.DB_AREA, 1, int(str(args[0])[2:]), byte_value)
        except Exception as e:
            self.logger.error(e)
        return None


def main():
    mm = MemoryMap(
        addr="192.168.0.2",
        rack=0,
        slot=1,
        host="49.233.15.221",
        password="root"
    )
    thread_list = list()  # type:list
    thread_list.append(Thread(target=mm.upload_data))
    thread_list.append(Thread(target=mm.download_data, args=(mm.download_callback,)))
    for t in thread_list:
        t.start()
    for t in thread_list:
        t.join()


if __name__ == '__main__':
    main()
