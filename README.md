# Data Pipeline 
Airflow와 Spark, Kafka를 활용한 데이터 파이프라인 입니다. Airflow에서 Kafka, Spark 배포 및 동작을 실행하고 가공된 데이터는 `.json` 파일로 변환 되어 Object Storage로 전달 됩니다.

# Architecture
> Kubernetes 클러스터로 구성 되어 있으며, 모두 Pod로 실행 됩니다. ![[Pasted image 20240813185429.png]]

# Basic Usage

### 1. Cluster
K-PaaS의 컨테이너 플랫폼 클러스터로 설치했으며 Master 1, Worker 2개로 이루어진 클러스터 입니다. 
- 설치 가이드: [컨테이너 플랫폼 설치 가이드](https://github.com/K-PaaS/container-platform/blob/master/install-guide/standalone/cp-cluster-install-single.md)

### 2. Airflow와 Spark Context 생성
### 3. Airflow 구성하기

```bash
helm pull apache-airflow/airflow
```

```bash
tar xvf airflow-1.13.1.tgz
mv airflow-1.13.1.tgz airflow
```

- airflow 폴더에 Dag 파일을 저장할 디렉토리를 만든다.
```bash
cd airflow && mkdir dags
```

```bash
cd ~/airflow
vi Dockerfile
vi requirements.txt
```

- Docker Repository upload
#### Airflow Custom Values 생성 하기

*진행 시나리오*
- Local에서 작업한 Resource를 Conateinr 안에서도 동일하게 작업 할 수 있도록 Volume Mount를 해준다.
	*참고: airflow의 dags 파일은 이미 다른 컨테이너와 공유 되고 있기 때문에 Local과 연결 하지 않았다.*
-  `kubeconfig-secret`과`{WEB_SERVER_SECRET_KEY}`은 아래의 절차를 따라 진행 후 입력 한다.

##### 1) kubeconfig-secret
##### 2) Webserver Secret
##### 3) Volume 생성 (StorageClass, PV/PVC)
> - kafka-spark-PV.yaml
> - stroageclass.yaml
##### 4) custom_values 적용하기
> - custom_values.yaml

### 4. Spark 구성하기
Spark를 Kubernetes에서 사용하기 위해 SparkOperator를 사용하여 데이터 처리를 Job으로 수행하는 환경을 구성한다.

1. 작업 디렉토리를 만든다
```bash
cd ~/airflow
mkdir spark
```

- Streaming이 완료 되면 쌓이는 결과 값을 nhn의 Object Stroage에 업로드 한다.
```bash
cd ~/airflow/spark
vi messaging.py
```

> 해당 부분은 자신이 구성한 클러스터에 맞게 변경 한다.
> - bootstrap_servers = ''
> - topic_name = ''
> - spark_master_url = ''

#### Spark Custom Image 생성
```bash
vi Dockerfile
```

#### SparkJob 생성
```bash
vi sparkjob.yaml
```

#### Spark PVC 생성

### 5. Kafka 구성하기 

```bash
cd ~/airflow && mkdir kafka
cd kafka
```
##### Kafka 클러스터를 구성 한다.
1. 이 가이드에서는 `Strimzi`를 사용해 Kafka Cluster를 배포한다.
2. Strimzi는 Kafka 클러스터 관리에 간소회된 Kubernetes 기반 방식을 제공한다.
3. CRD를 활용 하여 클러스터 관리를 간단하고 Kubernetes 권장사항에 부합하게 한다.

```bash
helm repo add strimzi https://strimzi.io/charts/
```

```bash
helm upgrade --install strimzi-kafka strimzi/strimzi-kafka-operator -n kafka --create-namespace
```

- Kafka의 produce, consume 등을 모니터링 하기 위한 Client를 배포 한다.
```bash
vi kafka-client.yaml
```

- produce 할 Topic을 생성한다.
```bash
vi kafka-topic.yaml
```

- Kafka와 Zookeeper volume을 생성한다.
```bash
vi kafka-volume.yaml
```

- Kafka를 생성한다.
```bash
vi kafka.yaml
```

### 6) ClusterRole & ClusterRolebinding 설정하기

### 7) Airflow 배포하기
```bash
helm repo add apache-airflow https://airflow.apache.org
helm upgrade --install airflow apache-airflow/airflow --namespace airflow --create-namespace -f custom_values.yaml
```
### 8) SparkOperator 배포하기
```bash
helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm upgrade --install -n spark --create-namespace spark-operator spark-operator/spark-operator --set webhook.enable=true
```

### Dag 파일 작성
1. Airflow의 webserver Container에 접속한다.
```bash
kubectl exec -ti -n airflow {AIRFLOW_WEB_SERVER_POD} -- bash
```

2. dag파일을 작성한다.
```bash
cd /opt/airflow/dags
vi dags.py
```

## 실행 하기
##### Airflow UI에 접속한다.
- 주소: {MASTER_NODE_IP}:{AIRFLOW_WEB_SERVER_SVC_PORT}
- id 및 password: admin/admin
##### Dag을 실행 한다.
1. 생성 된 dag을 클릭한 후 ▶️버튼을 클릭 한다.
3. 실행중인 dag의 로그를 보기 위해서는 UI의 Dag 실행 중인 task를 클릭해 로그를 볼 수 있다.
##### .json으로 변환된 결과 파일은 Spark Master, Worker 컨테이너에 접속해 `/result-data` 에서 확인 할 수 있다.


