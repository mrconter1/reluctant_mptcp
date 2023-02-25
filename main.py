import numpy as np
import matplotlib.pyplot as plt
import datetime
from matplotlib import colors
from matplotlib.ticker import PercentFormatter
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import Link, TCLink,Intf
from subprocess import Popen, PIPE
import matplotlib.pyplot as plt
from mininet.log import setLogLevel
from mininet.clean import Cleanup
from datetime import datetime
import time
import os

number_of_paths = 2
mptcp = 1

transfer_size = 100

# ------ Test run settings ----

diagram_name_comment = "250_Mbps_5_ms_and_5_Mpbs_50_ms_and_100_Mb_transfer"

config = {}

config["run_count"] = 0
config["total_number_of_runs"] = 0

config["number_of_paths"] = 2
config["mptcp_is_enabled"] = True

config["bytes_to_transfer"] = (transfer_size / 1000) * 1000 ** 3

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

def sample_mean_from_config(samples):

    times = []

    for i in range(samples):

        net, h1, h2 = initMininet()

        run_cmd(net, "h2 python3 server.py &")

        time.sleep(0.3)

        res = run_cmd(net, "h1 python3 client.py " + str(int(config["bytes_to_transfer"])))
        data_value = float(res.split("Total time: ")[-1].split(" ")[0])

        net.stop()

        times.append(data_value)

    print(times)

    #mean = np.median(times)
    mean = sum(times)

    return mean 

def sample_tcp(config, samples):

    number_of_paths = 1
    mptcp = 0

    mean_tcp = sample_mean_from_config(samples)
    print("Sum tcp:", mean_tcp)

    return mean_tcp

def sample_mptcp(config, samples):

    number_of_paths = 2
    mptcp = 1

    mean_mptcp = sample_mean_from_config(samples)
    print("Sum mptcp:", mean_mptcp)

    return mean_mptcp

def run_large():



    return None

def run_2d_hist():

    transfer_size = 100
    sample_size = 50

    mean_tcp = sample_tcp(config, sample_size)

    H = np.array([[1, 1, 1, 1, 1],
                  [1, 1, 1, 1, 1],
                  [1, 1, 1, 1, 1],
                  [1, 1, 1, 1, 1],
                  [1, 1, 1, 1, 1]])  

    data_samples = []

    bandwidth_range = np.arange(0.1, 50, 7)
    delay_range = range(0, 300, 50)

    c = 0
    diff_times = []
    for bandwidth in bandwidth_range:

        delay_list = []


        for delay in delay_range:

            start_time = time.time()

            config["client_path_b"]["bandwidth"] = bandwidth
            config["client_path_b"]["delay"] = delay

            mean_mptcp = sample_mptcp(config, sample_size)

            procentage_diff = mean_mptcp / mean_tcp
            delay_list.append(procentage_diff)

            print("Bandwidth:", bandwidth, ", Delay:", delay)
            print("Procentage difference:", procentage_diff)
            print()

            c += 1

            diff_time = time.time() - start_time
            diff_times.append(diff_time)

            print("Estimated time left:", ((sum(diff_times) / len(diff_times)) * (len(bandwidth_range) * len(delay_range) - c)) / 3600, "hours")


        data_samples.append(delay_list)

        for data_sample in data_samples:

            outStr = ""
            for point in data_sample:
                outStr += str(round(point, 5)) + "\t"
                
            print(outStr)


    '''
    np_list = np.array(data_samples)
    plt.imshow(np_list)

    cdict = {'red':  ((0.0, 0.0, 0.0),   
                      (0.5, 1.0, 1.0),    
                      (1.0, 0.8, 0.8)),   

            'green': ((0.0, 0.8, 0.8),    
                      (0.5, 1.0, 1.0),   
                      (1.0, 0.0, 0.0)),  

            'blue':  ((0.0, 0.0, 0.0),   
                      (0.5, 1.0, 1.0),    
                      (1.0, 0.0, 0.0))   
           }

    GnRd = colors.LinearSegmentedColormap('GnRd', cdict)
    fig,ax = plt.subplots(1)
    p=ax.pcolormesh(H,cmap=GnRd,vmin=-0.995,vmax=1.005)
    fig.colorbar(p,ax=ax)

    now = datetime.now()
    date_time = now.strftime("_%m_%d_%Y__%H_%M_%S")
    diagram_path = diagram_name_comment + '_experiment' + date_time + '.png'

    plt.savefig(diagram_path)
    os.system("feh " + diagram_path+ " &")
    '''

def main():

    print()
    print("---- Starting test bed -----")
    print()

    diagrams_folder = "diagrams"

    # Create folder for diagrams
    try:
        os.mkdir(diagrams_folder)
    except:
        pass

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
        plt.xlabel(parameter + " for " + path + " (sample size: " + str(config["number_of_samples_per_data_point"]) + ")")
    else:
        plt.xlabel("(sample size: " + str(config["number_of_samples_per_data_point"]) + ")")

    plt.ylabel("Transfer time (seconds)")

    now = datetime.now()
    date_time = now.strftime("_%m_%d_%Y__%H_%M_%S")

    diagram_path = diagrams_folder + "/" + diagram_name_comment + '_experiment' + date_time + '.png'
    plt.savefig(diagram_path)
    os.system("feh " + diagram_path+ " &")

def delete_file(file_path):

    if os.path.exists(file_path):
        os.remove(file_path)

def run_cmd(net, cmd_str):

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

def runConfig():

    data_point = []

    i = 0
    for i in range(config["number_of_samples_per_data_point"]):

        net, h1, h2 = initMininet()

        print("Run " + str(config["run_count"]  + 1) + " out of " + str(config["total_number_of_runs"]))
        print()

        run_cmd(net, "h2 python3 server.py &")

        time.sleep(1)

        res = run_cmd(net, "h1 python3 client.py " + str(int(config["bytes_to_transfer"])))
        data_value = float(res.split("Total time: ")[-1].split(" ")[0])

        print("Total time:", data_value, "seconds")

        print()

        net.stop()

        data_point.append(data_value)

        i += 1
        config["run_count"] += 1

    data.append(data_point)

def initMininet():

    net = Mininet(link=TCLink)
    key = "net.mptcp.mptcp_enabled"
    #value = 1 if config["mptcp_is_enabled"] else 0
    #value = 1
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
    run_2d_hist()
    run_large()
    #main()


