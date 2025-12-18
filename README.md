# Mordente
Mordente is a tool to perform a differential verification of information flow requirements in SEAndroid access control policies.

## Prerequisites
Clone the main repository
```
git clone https://github.com/edoxthebest/Mordente.git
```

Clone the libraries on which Mordente relies
```
cd mordente
git clone https://github.com/edoxthebest/mata.git
git clone --branch 4.5.1 --depth 1 https://github.com/SELinuxProject/setools.git 
git clone --branch 3.8.1 --depth 1 git@github.com:SELinuxProject/selinux.git
```

The tool [`payload-dumper-go`](https://github.com/ssut/payload-dumper-go) is needed to extract the policies from a given android firmware.
On a Linux or macOS system you can download this tool as follows.
```
cd src/selinuxtool/android-extract
wget -q https://github.com/ssut/payload-dumper-go/releases/download/1.3.0/payload-dumper-go_1.3.0_linux_amd64.tar.gz
tar -xvzf payload-dumper-go_1.3.0_linux_amd64.tar.gz
chmod +x payload-dumper-go
```
Refer to the manual page for `payload-dumper-go` for more details.


## About policy download
Policies used during the experiments can be downloaded and extracted semi-automatically.
You can either download them before building the docker image or download them inside a container running with said image.
Beware that some interaction is required to download Xiaomi policies: when prompted you will be asked to enter an url; open the link provided with the prompt in your browser and copy the link that the button `Download Full Rom` is pointing to into the prompt.


To download them before building the docker image proceed as follows.

Make sure to be in the same folder where you downloaded `payload-dumper-go`, otherwise cd there, then execute the download script.
You may also be required to enter your password since root privileges are needed to correctly mount the required partitions
```
cd src/selinuxtool/android-extract
./demo-extract
```

## Build the Mordente container with Docker
First, clone the required dependencies as above, then you can build the Docker image with the following.
```
docker build -t mordente .
```

Then create a container with the built image.
```
docker container create -it --name mordente mordente sh
```

Connect to the container with
```
docker container start mordente
docker exec -it mordente sh
```

If you have yet to download the required policies you can do that now inside the container with the following                  
```
cd src/selinuxtool/android-extract
./demo-extract
```         

## Replicate the testing suite using Docker
Assuming we are already inside the container you can replicate the experiments of the paper with the following.
```
mordente policy policies/p1 policies/p2
mordente policy policies/p2 policies/p3
mordente policy policies/p1 policies/p4
mordente policy policies/p2 policies/p5
mordente policy policies/p2 policies/p6
```


## Using Mordente
Mordente is used by specifying the paths of two policies one's whishes to compare.
By default, a predefined list of queries will be perfomed.
Use the option `--queries` together with a path to specify a different set of queries (one per line).
Mordente then can be run as follows.
```
mordente policy --queries {path_of_the_queries} {path_of_the_first_policy} {path_of_the_second_policy}
```
