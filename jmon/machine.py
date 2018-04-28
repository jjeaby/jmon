import argparse
import datetime
import json
import os
import pprint
import socket
import subprocess
import time
import re

from influxdb import InfluxDBClient


class Machine(object):
    def __init__(self, host_ip='', host_port='8086', id='', password='', database='machine_information'):
        self.host_ip = host_ip
        self.host_port = host_port
        self.id = id
        self.password = password
        self.database = database

    def machine_information(self):
        info = os.popen('uname -a').readlines()[-1].split()[0:]
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            socket_instance.connect(('192.0.0.8', 1027))
            ip_address = socket_instance.getsockname()[0]
        except socket.error:
            ip_address = "OffLine"

        machine_info = {
            "machine_os_platform": info[0],
            "machine_name": info[1],
            "machine_ip_address": ip_address
        }
        return machine_info

    def get_gpu_infomation(self):
        whereis_nvidia_smi_cmd = [r"whereis", "nvidia-smi"]
        whereis_nvidia_smi_cmd_output = str(subprocess.check_output(whereis_nvidia_smi_cmd))
        whereis_nvidia_smi_path = str(whereis_nvidia_smi_cmd_output.split(" ")[1])
        nvidia_smi_output = [whereis_nvidia_smi_path, "--format=csv,noheader,nounits",
                             "--query-gpu=uuid,index,name,memory.total,memory.used,memory.free,temperature.gpu"]
        gpu_data = str(subprocess.check_output(nvidia_smi_output).decode("utf-8")).split(os.linesep)
        # gpu_data = r'GPU-fbce4a93-3a20-a778-aa32-4b396f8df6d8, 0, GeForce GTX 1080 Ti, 11172, 10, 11162, 35', r'GPU-5fa30715-d37c-d266-0f11-e76c147b809a, 1, GeForce GTX 1080 Ti, 11171, 4547, 6624, 43', ''
        gpu_info = []
        for idx, data in enumerate(gpu_data):
            gpu_value = data.split(",")
            if len(gpu_value) > 1:
                temp_info = {"gpu" + str(idx) + "_uuid": gpu_value[0].strip(),
                             "gpu" + str(idx) + "_index_id": gpu_value[1].strip(),
                             "gpu" + str(idx) + "_name": gpu_value[2].strip(),
                             "gpu" + str(idx) + "_total_memory": int(gpu_value[3].strip()),
                             "gpu" + str(idx) + "_used_memory": int(gpu_value[4].strip()),
                             "gpu" + str(idx) + "_free_memory": int(gpu_value[5].strip()),
                             "gpu" + str(idx) + "_temperature": float(gpu_value[6].strip())}
                gpu_info.append(temp_info)
        return gpu_info

    def memory_information(self):
        memory_total, memory_used, memory_free = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
        memory_info = {
            "memory_total": memory_total,
            "memory_used": memory_used,
            "memory_free": memory_free
        }

        return memory_info

    def get_cpu_status(self):
        # http://stackoverflow.com/questions/23367857/accurate-calculation-of-cpu-usage-given-in-percentage-in-linux
        # read in cpu information from file
        # The meanings of the columns are as follows, from left to right:
        # 0cpuid: number of cpu
        # 1user: normal processes executing in user mode
        # 2nice: niced processes executing in user mode
        # 3system: processes executing in kernel mode
        # 4idle: twiddling thumbs
        # 5iowait: waiting for I/O to complete
        # 6irq: servicing interrupts
        # 7softirq: servicing softirqs
        # 8steal:
        # 9guest:
        # 10guest_nice:
        #
        # #the formulas from htop
        #      user    nice   system  idle      iowait irq   softirq  steal  guest  guest_nice
        # cpu  74608   2520   24433   1117073   6176   4054  0        0      0      0
        #
        #
        # Idle=idle+iowait
        # NonIdle=user+nice+system+irq+softirq+steal
        # Total=Idle+NonIdle # first line of file for all cpus
        #
        # CPU_Percentage=((Total-PrevTotal)-(Idle-PrevIdle))/(Total-PrevTotal)

        cpu_infos = {}  # collect here the information
        with open("/proc/stat", "r") as f_stat:
            lines = [line.split(" ") for content in f_stat.readlines() for line in content.split('\n') if
                     line.startswith("cpu")]

            # compute for every cpu
            for cpu_line in lines:
                if '' in cpu_line: cpu_line.remove('')  # remove empty elements
                cpu_line = [cpu_line[0]] + [float(i) for i in cpu_line[1:]]  # type casting
                cpu_id, user, nice, system, idle, iowait, irq, softrig, steal, guest, guest_nice = cpu_line

                Idle = idle + iowait
                NonIdle = user + nice + system + irq + softrig + steal

                Total = Idle + NonIdle
                # update dictionionary
                cpu_infos.update({cpu_id: {"total": Total, "idle": Idle}})
            return cpu_infos

    def cpu_infomation(self):
        start = self.get_cpu_status()
        # wait a second
        time.sleep(0.1)
        stop = self.get_cpu_status()

        cpu_load = {}

        for cpu in start:
            Total = stop[cpu]["total"]
            PrevTotal = start[cpu]["total"]

            Idle = stop[cpu]["idle"]
            PrevIdle = start[cpu]["idle"]
            CPU_Percentage = ((Total - PrevTotal) - (Idle - PrevIdle)) / (Total - PrevTotal) * 100
            cpu_load.update({cpu: CPU_Percentage})

        cpu_info = {"cpu_usage": round(cpu_load["cpu"], 2)}
        # device_type = subprocess.check_output(['cat', '/sys/class/thermal/thermal_zone*/type']).decode("utf-8")
        device_type = os.popen('cat /sys/class/thermal/thermal_zone*/type').readlines()
        device_temperature = os.popen('cat /sys/class/thermal/thermal_zone*/temp').readlines()
        cpu_temperature = 0
        for idx, device in enumerate(device_type):
            if str(device).startswith("x86_pkg"):
                cpu_temperature = device_temperature[idx]
                break

        cpu_info["cpu_temperature"] = float(float(cpu_temperature) / 1000)

        return cpu_info

    def influxdbInsertData(self, server_info):

        host = self.host_ip
        port = self.host_port
        user = str(self.id)
        password = self.password
        dbname = self.database

        """Instantiate a connection to the InfluxDB."""
        #client = InfluxDBClient(host=host, port=port, user=user, password=password, dbname=dbname, time=100000)
        client = InfluxDBClient(host=host, port=port, username=user, password=password, database=dbname, timeout=30)
        # print("Write : cpu,atag=test1 idle=100,usertime=10,system=1")
        # client.write(['cpu,atag=test1 idle=100,usertime=10,system=1'], {'db': dbname}, 204, 'line')

        machine = server_info["machine"]
        cpu = server_info["cpu"]
        memory = server_info["memory"]
        gpu = server_info["gpu"]

        fields_data = {}
        tags_data = {}
        for data in dict(machine.items()):
            tags_data[data] = machine[data].strip()
        for data in dict(cpu.items()):
            fields_data[data] = cpu[data]
        for data in dict(memory.items()):
            fields_data[data] = memory[data]
        for idx, list in enumerate(gpu):
            for data in dict(list.items()):
                fields_data[data] = gpu[idx][data]
        tags_data = json.dumps(tags_data)
        fields_data = json.dumps(fields_data)
        # print(tags_data)
        # print(fields_data)
        # now = datetime.datetime.today()
        # print(now)
        points = []
        point = {"measurement": 'machine_information',
                 # "time": now.strftime('%Y-%m-%d %H:%M:%S'),
                 # "time": 1000000000 * int(now.strftime('%s')),
                 # "time": int(round(time.time() * 1000)),
                 # "fields": fields_data
                 }
        point["tags"] = json.loads(tags_data)
        point["fields"] = json.loads(fields_data)

        # pprint.pprint(point)
        points.append(point)

        if self.isValidIP(self.host_ip):
            ret = client.write_points(points)
            # print("DB 입력 결과 : [" + str(ret) + "]")
        # pprint.pprint(point)


    def isValidIP(self, ip):
        m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
        return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))

    def print_satus(self, server_info):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("-" *80)
        print("TIME : ", datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        print("-" *80)
        pprint.pprint(server_info)
        print("-" *80)
        print("")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Machine's CPU, MEMORY, GPU Status diplay and send InfluxDB")
    parser.add_argument('--ip', type=str, required=False, default='', help='ip address of InfluxDB http API')
    parser.add_argument('--port', type=int, required=False, default=8086, help='port of InfluxDB http API')
    parser.add_argument('--id', type=str, required=False, default='', help='influxDB user id')
    parser.add_argument('--password', type=str, required=False, default='', help='influxDB user password')
    parser.add_argument('--database', type=str, required=False, default='machine_information',
                        help='influxDB Database Name')
    parser.add_argument('--interval', type=int, required=False, default=5, help='monitoring interval second')
    parser.add_argument('--log', type=str, required=False, default='true', help=r"set true is machine's cpu, memory, gpu status show console log as a json format")

    args = parser.parse_args()
    machinemonitor = Machine(host_ip=str(args.ip), host_port=args.port, id=args.id, password=args.password, database=args.database)
    log = args.log.lower()

    if log not in {'true', 'false'}:
        print("machine.py: error: the following argument value is only true, false: --log")
        exit(1)


    # print(args)
    # print( machinemonitor.isValidIP(args.ip))
    if len(args.ip) > 0 and not machinemonitor.isValidIP(args.ip):
        print("influxDB ip address is invalid!")
        exit(1)

    while True:
        server_info = {
            "machine": machinemonitor.machine_information(),
            "cpu": machinemonitor.cpu_infomation(),
            "gpu": machinemonitor.get_gpu_infomation(),
            "memory": machinemonitor.memory_information(),
        }
        if machinemonitor.isValidIP(str(args.ip)):
            machinemonitor.influxdbInsertData(server_info)
        if len(log) > 0 and log == 'true':
            machinemonitor.print_satus(server_info)
        time.sleep(args.interval)
