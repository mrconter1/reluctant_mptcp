import numpy as np
import matplotlib.pyplot as plt
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import Link, TCLink,Intf
from subprocess import Popen, PIPE
from mininet.log import setLogLevel
from mininet.clean import Cleanup
from datetime import datetime
import time

config = {}

config["run_count"] = 0
config["total_number_of_runs"] = 0

config["number_of_paths"] = 1
config["mptcp_is_enabled"] = True
config["amount_of_bytes_to_request"] = 1 * 1024 * 1024

config["number_of_samples_per_data_point"] = 3

config["client_path_a"] = {}
config["client_path_a"]["bandwidth"] = 100
config["client_path_a"]["delay"] = 100
config["client_path_a"]["packet_loss"] = 1 
config["client_path_a"]["queue_size"] = 10

config["client_path_b"] = {}
config["client_path_b"]["bandwidth"] = 100
config["client_path_b"]["delay"] = 100
config["client_path_b"]["packet_loss"] = 1 
config["client_path_b"]["queue_size"] = 10

config["server_path"] = {}
config["server_path"]["bandwidth"] = 100
config["server_path"]["delay"] = 100
config["server_path"]["packet_loss"] = [1, 10, 5]
config["server_path"]["queue_size"] = 10

data = []

def main():

    print()
    print("---- Starting test bed -----")
    print()

    path = ""
    parameter = ""
    values = []
    for key, value in config.items():
        if type(value) is dict:
            for sub_key, sub_value in value.items():
                if type(sub_value) is list:
                    path = key
                    parameter = sub_key
                    range_parameters = config[path][parameter]
                    values = list(range(range_parameters[0], range_parameters[1], range_parameters[2]))
                    print('Running multiple configs for config["' + path + '"]["' + parameter + '"] with')
                    print()
                    print(values)
                    print()
                    print("and with " + str(config["number_of_samples_per_data_point"]) + " samples per data point.")
                    print()


    if path != "" and parameter != "":

        config["total_number_of_runs"] = len(values) * config["number_of_samples_per_data_point"]

        print("Total number of runs to be executed:", config["total_number_of_runs"])

        print()
        print("----------------------------")
        print()

        for val in values:
            config[path][parameter] = val
            runConfig()
    else:

        config["total_number_of_runs"] = config["number_of_samples_per_data_point"]

        print("Running config with " + str(config["number_of_samples_per_data_point"]) + " samples per data point.")

        print("Total number of runs to be executed:", config["total_number_of_runs"])

        print()
        print("----------------------------")
        print()

        runConfig()

    print()
    print("Plotting following data:")
    print(data)
    print()

    plt.boxplot(data)

    if path != "" and parameter != "":
        plt.xlabel(parameter + " for " + path)

    plt.ylabel("Transfer time (seconds)")

    now = datetime.now()
    date_time = now.strftime("_%m_%d_%Y__%H_%M_%S")

    plt.savefig('experiment' + date_time + '.png')
    plt.show()

def runConfig():

    data_point = []

    i = 0
    for i in range(config["number_of_samples_per_data_point"]):

        net, h1, h2 = initMininet()

        print("Run " + str(config["run_count"]  + 1) + " out of " + str(config["total_number_of_runs"]))
        print()

        h2.cmd("python3 server.py &")

        # Sleep for waiting for server to start
        time.sleep(0.1)

        res = h1.cmd("python3 client.py " + str(int(config["amount_of_bytes_to_request"])))
        print(res)
        total_time = float(res.split('\n')[0].split(' ')[-2])
        data_point.append(total_time)

        net.stop()

        #Cleanup.cleanup()

        i += 1
        config["run_count"] += 1

    data.append(data_point)

def initMininet():

    net = Mininet(link=TCLink)
    key = "net.mptcp.mptcp_enabled"
    value = 1 if config["mptcp_is_enabled"] else 0
    p = Popen("sysctl -w %s=%s" % (key, value), shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

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

    if config["number_of_paths"] == 1:
        h1.cmd("ip link set h1-eth1 down")

    return net, h1, h2

if '__main__' == __name__:
    main()

