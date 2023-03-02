from mininet.link import Link, TCLink,Intf
from mininet.log import setLogLevel
from subprocess import Popen, PIPE
from mininet.clean import Cleanup
from mininet.net import Mininet
from datetime import datetime
from mininet.cli import CLI
from pathlib import Path

import numpy as np
import time
import os

number_of_paths = 2
mptcp = 1

global_transfer_size = 100

# ------ Test instance run settings ----

config = {}

config["run_count"] = 0
config["total_number_of_runs"] = 0

config["number_of_paths"] = 2
config["mptcp_is_enabled"] = True

config["bytes_to_transfer"] = (global_transfer_size / 1000) * 1000 ** 3

config["number_of_samples_per_data_point"] = 50

config["client_path_a"] = {}
config["client_path_a"]["bandwidth"] = 250
config["client_path_a"]["delay"] = 5
config["client_path_a"]["packet_loss"] = 0
config["client_path_a"]["queue_size"] = 10

config["client_path_b"] = {}
config["client_path_b"]["bandwidth"] = 3
config["client_path_b"]["delay"] = 150
config["client_path_b"]["packet_loss"] = 0
config["client_path_b"]["queue_size"] = 10

config["server_path"] = {}
config["server_path"]["bandwidth"] = 1000
config["server_path"]["delay"] = 0
config["server_path"]["packet_loss"] = 0
config["server_path"]["queue_size"] = 10

data = []

def file_write(filename, text):
    with open(filename, 'a') as f:
        f.write(text)

def sample_sum_from_config(samples):

    times = []

    for i in range(samples):

        net, h1, h2 = initMininet()

        execute_cmd(net, "h2 python3 server.py &")

        time.sleep(0.3)

        res = execute_cmd(net, "h1 python3 client.py " + str(int(config["bytes_to_transfer"])))
        data_value = float(res.split("Total time: ")[-1].split(" ")[0])

        net.stop()

        times.append(data_value)

    print(times)

    return sum(times)

# Samples a config using single path topology and single path TCP
def sample_tcp(config, samples):

    number_of_paths = 1
    mptcp = 0

    sum_tcp = sample_sum_from_config(samples)
    print("Sum tcp:", sum_tcp)

    return sum_tcp

# Samples a config using multi path topology and MPTCP
def sample_mptcp(config, samples):

    number_of_paths = 2
    mptcp = 1

    sum_mptcp = sample_sum_from_config(samples)
    print("Sum mptcp:", sum_mptcp)

    return sum_mptcp

# This function takes a two dimensional list and generates a html-page with a table for it
def generate_table(data):

    html_filename = 'index.html'

    html = ''
    html += '<!DOCTYPE html>' + '\n'
    html += '<html>' + '\n'
    html += '<head>' + '\n'
    html += '\t' + '<meta http-equiv="refresh" content="5">' + '\n'
    html += '</head>' + '\n'
    html += '<style>' + '\n'
    html += 'table, th, td {' + '\n'
    html += '\t' + 'border:1px solid black;' + '\n'
    html += '}' + '\n'
    html += '</style>' + '\n'
    html += '<body>' + '\n'
    html += '\n'
    html += '<table style="width:100%">' + '\n'
    
    for row in data:
        html += '\t' + '<tr>' + '\n'
        for el in row:
            html += '\t\t' + '<th>' + str(el) + '</th>' + '\n'
        html += '\t' + '<tr>' + '\n'

    html += '</body>' + '\n'
    html += '</html>' + '\n'

    try:
        os.remove(html_filename)
    except:
        pass

    file_write(html_filename, html)

def run_large():

    sample_size = 3

    # ----- Experiment range -----
    transfer_sizes = [0.01, 0.1, 1, 10, 100]

    primary_bws = [100, 300, 800]
    primary_delays = [1, 10, 25]

    secondary_bws = [2, 10, 30, 50, 70, 125, 300, 800]
    secondary_delays = [1, 10, 25, 50, 100, 300]

    count = 0
    total = len(transfer_sizes) * len(primary_bws) * len(primary_delays) * len(secondary_bws) * len(secondary_delays)

    data = []
    data.append([])
    data.append([])

    for i in range(3):
        data[0].append('')
        data[1].append('')

    for secondary_bw in secondary_bws:
        for secondary_delay in secondary_delays:
            data[0].append(str(secondary_bw) + ' bw')
            data[1].append(str(secondary_delay) + ' ms')

    for transfer_size in transfer_sizes:
        for primary_bw in primary_bws:
            for primary_delay in primary_delays:

                data.append([])

                global_transfer_size = transfer_size

                config["client_path_a"]["bandwidth"] = primary_bw
                config["client_path_a"]["delay"] = primary_delay

                sum_tcp = sample_tcp(config, sample_size)

                data[-1].append(global_transfer_size)
                data[-1].append(primary_bw)
                data[-1].append(primary_delay)

                for secondary_bw in secondary_bws:
                    for secondary_delay in secondary_delays:

                        print("Run", count, "out of", total)

                        config["client_path_b"]["bandwidth"] = secondary_bw
                        config["client_path_b"]["delay"] = secondary_delay

                        sum_mptcp = sample_mptcp(config, sample_size)

                        procentage_diff = round(100 * (sum_mptcp / sum_tcp))

                        print(procentage_diff)

                        data[-1].append(procentage_diff)

                        generate_table(data)

                        count += 1

    return None

def delete_file(file_path):

    if os.path.exists(file_path):
        os.remove(file_path)

# Hack-ish solution to avoid namespace problems when executing commands in a Mininet node
def execute_cmd(net, cmd_str):

    script_name = ".temp.sh"
    output_name = ".temp.out"
    
    delete_file(script_name)
    delete_file(output_name)

    f = open(script_name, 'a+')
    f.write(cmd_str + " > " + output_name)
    f.close()

    CLI(net, script=script_name)

    res = Path(output_name).read_text()

    delete_file(script_name)
    delete_file(output_name)

    return res

def initMininet():

    net = Mininet(link=TCLink)
    key = "net.mptcp.mptcp_enabled"
    value = mptcp
    p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE, stderr=PIPE)

    tcp_nms_key = "net.ipv4.tcp_no_metrics_save"
    tcp_no_metrics_save = 1
    p = Popen ("sysctl -w %s=%s" % (tcp_nms_key, tcp_no_metrics_save), shell=True, stdout=PIPE, stderr=PIPE)

    h1 = net.addHost('h1')
    h2 = net.addHost('h2')
    r1 = net.addHost('r1')

    net.addLink(r1, h1, cls=TCLink,
                    bw=config["client_path_a"]["bandwidth"], 
                    delay=str(config["client_path_a"]["delay"])+'ms', 
                    loss=config["client_path_a"]["packet_loss"])

    net.addLink(r1, h1, cls=TCLink,
                    bw=config["client_path_b"]["bandwidth"], 
                    delay=str(config["client_path_b"]["delay"])+'ms', 
                    loss=config["client_path_b"]["packet_loss"])

    net.addLink(r1, h2, cls=TCLink,
                    bw=config["server_path"]["bandwidth"], 
                    delay=str(config["server_path"]["delay"])+'ms', 
                    loss=config["server_path"]["packet_loss"])
    
    net.build()

    r1.cmd("ifconfig r1-eth0 0")
    r1.cmd("ifconfig r1-eth1 0")
    r1.cmd("ifconfig r1-eth2 0")

    h1.cmd("ifconfig h1-eth0 0")
    h1.cmd("ifconfig h1-eth1 0")
    h2.cmd("ifconfig h2-eth0 0")

    r1.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")

    r1.cmd("ifconfig r1-eth0 10.0.0.1 netmask 255.255.255.0")
    r1.cmd("ifconfig r1-eth1 10.0.1.1 netmask 255.255.255.0")
    r1.cmd("ifconfig r1-eth2 10.0.2.1 netmask 255.255.255.0")
    h1.cmd("ifconfig h1-eth0 10.0.0.2 netmask 255.255.255.0")
    h1.cmd("ifconfig h1-eth1 10.0.1.2 netmask 255.255.255.0")
    h2.cmd("ifconfig h2-eth0 10.0.2.2 netmask 255.255.255.0")

    h1.cmd("ip rule add from 10.0.0.2 table 1")
    h1.cmd("ip rule add from 10.0.1.2 table 2")
    h1.cmd("ip route add 10.0.0.0/24 dev h1-eth0 scope link table 1")
    h1.cmd("ip route add default via 10.0.0.1 dev h1-eth0 table 1")
    h1.cmd("ip route add 10.0.1.0/24 dev h1-eth1 scope link table 2")
    h1.cmd("ip route add default via 10.0.1.1 dev h1-eth1 table 2")
    h1.cmd("ip route add default scope global nexthop via 10.0.0.1 dev h1-eth0")
    h2.cmd("ip rule add from 10.0.2.2 table 1")
    h2.cmd("ip route add 10.0.2.0/24 dev h2-eth0 scope link table 1")
    h2.cmd("ip route add default via 10.0.2.1 dev h2-eth0 table 1")
    h2.cmd("ip route add default scope global nexthop via 10.0.2.1 dev h2-eth0")

    if number_of_paths == 1:
        h1.cmd("ip link set h1-eth1 down")

    return net, h1, h2

def prevent_screen_from_turning_off():
    os.system("xset -dpms")
    os.system("xset s noblank")
    os.system("xset s off")
    os.system("xset s off -dpms")

if '__main__' == __name__:
    prevent_screen_from_turning_off()
    run_large()

