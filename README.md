# SSL Error after migrating to APISIX Gateway 3.9.0

## Steps to reproduce

1. Clone this repo and cd into it:
```shell
git clone https://github.com/rastiehaiev/apisix-migration-to-3_9_0-bug.git
cd apisix-migration-to-3_9_0-bug.git
```

2. Run APISIX Gateway + etcd:
```shell
docker-compose up -d
```

3. Run python script to create upstream, service, route and ssl:
```shell
pip install requests
pip install PyYAML

cd script
python3 script.py
cd ../
```

4. From your local machine, verify that apisix installed properly:
```shell
for i in {1..10}; do curl -k --resolve 'example.com:9443:127.0.0.1' 'https://example.com:9443/get?query=1' -vvv -I || { echo "curl failed at attempt $i"; break; }; done
```

5. Uninstall current installation (make sure etcd volume is not deleted):
```shell
docker-compose down
```
6. In `docker-compose.yaml`, change the version of APISIX image from `3.6.0` to `3.9.0`. 
7. In `config.yaml` uncomment line #53 and comment line #59 (there was a breaking change in apisix configuration in `3.9.0` version).
8. Run APISIX Gateway + etcd again:
```shell
docker-compose up -d
```

9. Run curl again, now it fails:
```shell
for i in {1..10}; do curl -k --resolve 'example.com:9443:127.0.0.1' 'https://example.com:9443/get?query=1' -vvv -I || { echo "curl failed at attempt $i"; break; }; done
```

## How to fix

To fix the issue, ssl should be re-created:
```shell
cd script
python3 script.py
cd ../
```
Verify (now it works):
```shell
for i in {1..10}; do curl -k --resolve 'example.com:9443:127.0.0.1' 'https://example.com:9443/get?query=1' -vvv -I || { echo "curl failed at attempt $i"; break; }; done
```