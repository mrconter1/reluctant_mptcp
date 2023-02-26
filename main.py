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

global_transfer_size = 100

# ------ Test run settings ----

diagram_name_comment = "250_Mbps_5_ms_and_5_Mpbs_50_ms_and_100_Mb_transfer"

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

def file_write(filename, text):
    with open(filename, 'a') as f:
        f.write(text)

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

    sample_size = 5

    transfer_sizes = [0.01, 0.1, 1, 10, 100]
    #transfer_sizes = [10, 100]

    primary_bws = [100, 300, 800]
    #primary_bws = [100, 300, 500]
    primary_delays = [1, 10, 25]

    secondary_bws = [2, 10, 30, 50, 70, 125, 300, 800]
    #secondary_bws = [2, 10, 30, 50, 70, 125, 300, 500]
    secondary_delays = [1, 10, 25, 50, 100, 300]
    #secondary_delays = [1, 10, 25]

    count = 0
    total = len(transfer_sizes) * len(primary_bws) * len(primary_delays) * len(secondary_bws) * len(secondary_delays)

    try:
        os.remove("out.csv")
    except:
        pass

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

                mean_tcp = sample_tcp(config, sample_size)

                with open('out.csv', 'a') as f:
                    f.write(str(global_transfer_size) + ',' + str(primary_bw) + ',' + str(primary_delay) + ',')

                data[-1].append(global_transfer_size)
                data[-1].append(primary_bw)
                data[-1].append(primary_delay)

                for secondary_bw in secondary_bws:
                    for secondary_delay in secondary_delays:

                        print("Run", count, "out of", total)

                        config["client_path_b"]["bandwidth"] = secondary_bw
                        config["client_path_b"]["delay"] = secondary_delay

                        mean_mptcp = sample_mptcp(config, sample_size)

                        procentage_diff = round(100 * (mean_mptcp / mean_tcp))

                        with open('out.csv', 'a') as f:
                            f.write(str(procentage_diff) + ",")

                        print(procentage_diff)

                        data[-1].append(procentage_diff)

                        generate_table(data)

                        count += 1

                with open('out.csv', 'a') as f:
                    f.write('\n')


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
    run_large()
    #run_2d_hist()
    #main()


