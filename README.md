# jmon is Machine's Cpu, Memory, Cuda Information Monitoring and Save with InfluxDB 



### CPU, MEMORY, GPU 의 사용량 온도를 확인하여 InfluxDB 에 저장해주는 모듈입니다. 
- ip 를 지정하지 않으면 Console 에 JSON 으로 수집된 정보를 출력만 합니다. 
- ip 를 지정하면 해당 ip 에 설치된 InfluxDB 에 수집된 정보를 입력 합니다. 

 
 

#####[설치 방법]
```
pip install -U jmon
```



#####[사용 방법]
```
[] 파라미터는 옵션, [] 없는 파라미터는 필수 값임
 
python -m jmon.machine  [-h] 
                        [--ip IP] 
                        [--port PORT] 
                        [--id ID ]
                        [ --password PASSWORD]
                        [--database DATABASE] 
                        [--interval INTERVAL]

파라미터 설명 : 
    -h, --help           파라미터 설명 보여주기(show this help message and exit)
    --ip IP              InfluxDB 가 설치된 장비의 InfluxDB IP(ip address of InfluxDB http API)
    --port PORT          InfluxDB 가 설치된 장비의 InfluxDB PORT(port of InfluxDB http API)       
    --id ID              InfluxDB 사용자 ID(InfluxDB user id)                 
    --password PASSWORD  InfluxDB 사용자 PASSWORD(InfluxDB user password) 
    --database DATABASE  정보를 저장할 InfluxDB의 Database(InfluxDB Database Name) 
    --interval INTERVAL  CPU, MEMORY, GPU 정보를 가져올 주기(monitoring interval second) 
```

