__author__ = 'shirin'

from struct import *
from utils import *
import hashlib
import xmlrpclib
import sys
import re
import httplib, urllib2
from urlparse import urlparse
import socket
import time
import uuid
from packets import make_packets_dict
from datetime import datetime

packets_dict = make_packets_dict()
output_string = []
ack_need_list = []
wearable = []


def login(first, last, passwd, uri):
    login_params = {
        'first': first,
        'last': last,
        'passwd': '$1$'+hashlib.md5(passwd).hexdigest(),
        'version': '0.1',
        'start': 'last',
        'channel': 'shimbil',
        'platform': 'Lin'
    }

    xmlrpc = xmlrpclib.ServerProxy(uri)
    res = xmlrpc.login_to_simulator(login_params)
    return res


def get_caps(result, cap_key, request_keys):
    _, netloc, path, _, _, _ = urlparse(result[cap_key])
    params = "<llsd><array><string>"+request_keys[0]+"</string></array></llsd>"
    headers = {"content_type": "application/xml"}
    conn = httplib.HTTPSConnection(netloc)
    conn.request("POST", path, params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return data


def extract_cap(cap_result):
    trim_xml = re.compile(r"<key>([a-zA-Z_]+)</key><string>([a-zA-Z_:/0-9-.]+)</string>")
    new_key = trim_xml.search(cap_result).group(1)
    new_cap = trim_xml.search(cap_result).group(2)
    return new_key, new_cap


def schedule_ack_message(data):
    if not ord(data[0]) & 0x40:
        print "WTF! whats wrong in acknowledge messages!"
        return
    else:
        ID = data[1:5]
        if (ord(data[0]) & 0x40) & 0x80:
            ID = zero_decode_id(ID)
        ack_need_list.append(unpack(">L", ID)[0])
    return


def pack_acks():
    ack_sequence = ""
    for msgnum in ack_need_list:
        ack_sequence += pack("<L", msgnum)

    return ack_sequence


#def send_acks():
    # if len(ack_need_list) > 0:


def send_uuid_name_request(sock, port, host, current_sequence, agent_uuid):
    packed_data = ""
    fix_id = int("ffff0000", 16)+235
    data_header = pack(">BLB", 0x00, current_sequence, 0x00)

    # for x in agent_uuid:
    #     packed_data += uuid.UUID(x).bytes

    packed_data += uuid.UUID(agent_uuid).bytes

    packed_data = data_header + pack("L", fix_id) + pack(">B", len(agent_uuid)) + packed_data

    sock.sendto(packed_data, (host, port))
    return


def send_region_handshake_replay(sock, port, host, current_sequence, agent_uuid, session_uuid):
    packed_data = ""

    low_id = "ffff00%2x" % 149
    data_header = pack(">BLB", 0x00, current_sequence, 0x00)
    packed_data += uuid.UUID(agent_uuid).bytes + uuid.UUID(session_uuid).bytes + pack(">L", 0x00)
    packed_data = data_header + pack(">L", int(low_id, 16)) + packed_data

    sock.sendto(packed_data, (host, port))
    return


def send_agent_update(sock, host, port, current_sequence, result):
    temp_acks = pack_acks()
    del ack_need_list[:]
    if temp_acks == "":
        flags = 0x00
    else:
        flags = 0x10

    data_header = pack('>BLB', flags, current_sequence, 0x00)
    packed_data_message_id = pack('>B', 0x04)
    packed_data_id = uuid.UUID(result["agent_id"]).bytes + uuid.UUID(result["session_id"]).bytes
    packed_data_quatrots = pack("<ffff", 0.0, 0.0, 0.0, 0.0)+pack("<ffff", 0.0, 0.0, 0.0, 0.0)
    packed_data_state = pack('<B', 0x00)
    packed_data_camera = pack("<fff", 0.0, 0.0, 0.0)+pack('<fff', 0.0, 0.0, 0.0)+\
                         pack('<fff', 0.0, 0.0, 0.0)+pack('<fff', 0.0, 0.0, 0.0)
    packed_data_flags = pack('<fLB', 0.0, 0x00, 0x00)
    encoded_packed_data = zero_encode(packed_data_message_id+packed_data_id+
                                      packed_data_quatrots+packed_data_state+
                                      packed_data_camera+packed_data_flags)
    packed_data = data_header + encoded_packed_data + temp_acks
    print "sending AgentUpdate to server", byte_to_hex(data_header+zero_decode(encoded_packed_data)+temp_acks)
    sock.sendto(packed_data, (host, port))
    return


def send_complete_ping_check(sock, port, host, current_sequence, data, last_ping_sent):
    data_header = pack('>BLB', 0x00, current_sequence, 0x00)
    packed_data_message_id = pack('>B',0x02)
    packed_data = data_header + packed_data_message_id + pack('>B', last_ping_sent)
    print "CompletePingCheck packet sent:", byte_to_hex(packed_data)
    sock.sendto(packed_data, (host, port))

    return


def send_packet_ack(sock, port, host, current_sequence):
    tmp_acks = pack_acks()
    tmp_len = len(ack_need_list)
    del ack_need_list[:]
    data_header = pack('>BLB', 0x00, current_sequence, 0x00)
    packed_data_message_id = pack('>L', 0xFFFFFFFB)
    packed_ack_len = pack('>B', tmp_len)

    packed_data = data_header + packed_data_message_id + packed_ack_len + tmp_acks
    sock.sendto(packed_data, (host, port))
    return


def send_logout_request(sock, port, host, seqnum, agent_uuid, session_uuid):
    packed_data = ""
    packed_data_message_id = pack('>L',0xffff00fc)
    data_header = pack('>BLB', 0x00, seqnum, 0x00)
    packed_data += uuid.UUID(agent_uuid).bytes + uuid.UUID(session_uuid).bytes + pack(">L", 0x00)

    packed_data = data_header + packed_data_message_id + packed_data
    sock.sendto(packed_data, (host, port))
    return


def send_wearable_request(sock, port, host, seqnum, agent_uuid, session_uuid):
    data = pack('>BLBBBH', 0x00, seqnum, 00, 0xff, 0xff,  0x017d) + \
           uuid.UUID(agent_uuid).bytes + \
           uuid.UUID(session_uuid).bytes
    sock.sendto(data, (host, port))


def send_agent_is_now_wearing(sock, port, host, seqnum, agent_uuid, session_uuid):
    header = pack('>BLB', 0x00, seqnum, 00)
    data = pack('>BBH', 0xff, 0xff,  0x017f) + \
           uuid.UUID(agent_uuid).bytes + \
           uuid.UUID(session_uuid).bytes + \
           pack("<B", len(wearable)) + ''.join(wearable)
    sock.sendto(header+zero_encode(data), (host, port))




def establish_presence(host, port, circuit_code, result):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = pack('>BLBL', 0x00, 1, 00, 0xffff0003) + pack('<L', circuit_code) + \
           uuid.UUID(result["session_id"]).bytes + uuid.UUID(result["agent_id"]).bytes
    sock.sendto(data, (host, port))
    
    data = pack('>BLBL', 0x00, 2, 00, 0xffff00f9) + uuid.UUID(result["agent_id"]).bytes + \
           uuid.UUID(result["session_id"]).bytes + pack('<L', circuit_code)
    sock.sendto(data, (host, port))
    
    send_agent_update(sock, host, port, 3, result)
    agent_uuid = result["agent_id"]
    session_uuid = result["session_id"]
    send_uuid_name_request(sock, port, host, 4, agent_uuid)
    
    buf = 1024 * 4
    i = 0
    trusted_count = 0
    ackable = 0
    trusted_and_ackable = 0
    ack_need_list_changed = False
    seqnum = 5
    last_ping_sent = 0 
    trusted = 0

    # count = 0
    while True:
        if i == 100:
            send_wearable_request(sock, port, host, seqnum, result["agent_id"], result["session_id"])
            seqnum += 1

        # count += 1
        # if count % 10 == 0:
        #     send_agent_update(sock, host, port, seqnum, result)
        #     seqnum += 1

        if ack_need_list_changed:
            ack_need_list_changed = False
            send_packet_ack(sock, port, host, seqnum)
            seqnum += 1
            # sendAgentUpdate(sock, port, host, seqnum, result)
            # seqnum += 1
        # sendacks()
        i += 1
        data, addr = sock.recvfrom(buf)
        t = datetime.now()
        t.strftime("%H:%M:%S")
        
        if not data:
            print "Client has exited!"
            break
        else:
            test = byte_to_hex(data).split()
            ID = data[6:12]

            if ord(data[0]) & 0x80:
                ID = zero_decode_id(data[6:12])

            if ord(data[0]) & 0x40:
                schedule_ack_message(data);
                ack_need_list_changed = True

            # print test
            # print "ID =", byte_to_hex(ID)
            # print "ID =", unpack(">L", ID[:4])
            if ID[0] == '\xFF':
                if ID[1] == '\xFF':
                    if ID[2] == '\xFF':
                        # myentry = make_packets_dict()[("Fixed", "0x"+byte_to_hex(ID[0:4]).replace(' ', ''))]
                        myentry = make_packets_dict()[("Fixed", int(byte_to_hex(ID[3:4]).replace(' ', ''), 16))]
                        if myentry[1] == "Trusted":
                            trusted += 1;
                        ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)
                        # print ti, "Message #", i, "trusted count is", trusted,"Flags: 0x" + test[0], myentry,  "sequence #", unpack(">L",data[1:5])

                        # if myentry[1] == "Trusted": trusted_count += 1;print "number of trusted messages =", trusted_count
                        # if ord(data[0])&0x40 and myentry[1] == "Trusted": trusted_and_ackable += 1; print "trusted_and_ackable =", trusted_and_ackable
                        # if ord(data[0])&0x40: ackable += 1; print "number of ackable messages = ", ackable
                    else:
                        myentry = packets_dict[("Low", int(byte_to_hex(ID[2:4]).replace(' ', ''), 16))]
                        if myentry[1] == "Trusted":
                            trusted += 1;
                        ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)
                        # print ti, "Message #", i,"trusted count is", trusted,"Flags: 0x" + test[0], myentry,   "sequence #", unpack(">L",data[1:5])
                        if myentry[0] == "UUIDNameReply":
                            pass
                            #print ByteToHex(data)
                            #print data[:28]
                            #print data[28:36],data[38:45]
                        elif myentry[0] == "RegionHandshake":
                            send_region_handshake_replay(sock, port, host, seqnum,result["agent_id"],result["session_id"])
                            seqnum += 1
                        elif myentry[0] == "AgentWearablesUpdate":
                            print ">get wearable update.", byte_to_hex(data)
                            data = zero_decode(data[10:])
                            print "\t agent_id: ", uuid.UUID(bytes=data[0:16])
                            print "\t session_id: ", uuid.UUID(bytes=data[16:32])
                            print "\t serial_num: ", unpack("<L", data[32:36])
                            print "\t variable: ", int(unpack('<B', data[36])[0])
                            for i in xrange(int(unpack('<B', data[36])[0])):
                                wearable.append(data[37+i*33:37+i*33+16]+data[37+i*33+16+16])

                                print "\t\t\t ", \
                                    "last index:", 37+i*33+33, \
                                    uuid.UUID(bytes=data[37+i*33:37+i*33+16]), \
                                    uuid.UUID(bytes=data[37+i*33+16:37+i*33+16+16]), \
                                    unpack('<B', data[37+i*33+16+16])

                            send_agent_is_now_wearing(sock, port, host, seqnum, result["agent_id"], result["session_id"])
                            seqnum += 1

                                # if myentry[1] == "Trusted": trusted_count += 1;print "number of trusted messages =", trusted_count
                                # if ord(data[0])&0x40 and myentry[1] == "Trusted": trusted_and_ackable += 1; print "trusted_and_ackable =", trusted_and_ackable
                                # if ord(data[0])&0x40: ackable += 1; print "number of ackable messages = ", ackable
                else:
                    myentry = packets_dict[("Medium", int(byte_to_hex(ID[1:2]).replace(' ', ''), 16))]
                    if myentry[1] == "Trusted":
                        trusted += 1;
                    ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)
                    # print ti, "Message #", i,"trusted count is", trusted,"Flags: 0x" + test[0], myentry,  "sequence #", unpack(">L",data[1:5])

                    # if myentry[1] == "Trusted": trusted_count += 1;print "number of trusted messages =", trusted_count
                    # if ord(data[0])&0x40 and myentry[1] == "Trusted": trusted_and_ackable += 1; print "trusted_and_ackable =", trusted_and_ackable
                    # if ord(data[0])&0x40: ackable += 1; print "number of ackable messages = ", ackable
            else:
                myentry = packets_dict[("High", int(byte_to_hex(ID[0]), 16))]
                if myentry[0] == "StartPingCheck":
                    print "data from StartPingCheck", test
                    send_complete_ping_check(sock, port, host, seqnum, data, last_ping_sent)
                    last_ping_sent += 1
                    seqnum += 1

                if myentry[1] == "Trusted":
                    trusted += 1;
                ti = "%02d:%02d:%02d.%06d" % (t.hour,t.minute,t.second,t.microsecond)

                # print ti, "Message #", i,"trusted count is", trusted,"Flags: 0x" + test[0], myentry,   "sequence #", unpack(">L",data[1:5])

                # if myentry[1] == "Trusted": trusted_count += 1;print "number of trusted messages =", trusted_count
                # if ord(data[0])&0x40 and myentry[1] == "Trusted": trusted_and_ackable += 1; print "trusted_and_ackable =",  trusted_and_ackable
                # if ord(data[0])&0x40: ackable += 1; print "number of ackable messages = ", ackable
    send_logout_request(sock, port, host,seqnum,agent_uuid,session_uuid)
    sock.close()
    print "final number of trusted messages =", trusted_count

    return


if __name__ == "__main__":
    result = login("shirin", "saednia", "godisbig1317", "http://192.168.2.10:9000")
    myhost = result["sim_ip"]
    myport = result["sim_port"]
    mycircuit_code = result["circuit_code"]
    print result["agent_id"], result["session_id"]
    establish_presence(myhost, myport, mycircuit_code, result)
    cap_out = get_caps(result,"seed_capability", ["ChatSessionRequest"])
