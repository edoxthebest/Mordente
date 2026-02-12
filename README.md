# Mordente

This artifact contains Mordente, a tool for comparing different SEAndroid policies.
Mordente is a model checker for the novel Comparative Modal Logic CML and implements the algorithms introduced in the corresponding paper 
"Differential Verification of Information Flow in SEAndroid Policies", by Lorenzo Ceragioli, Letterio Galletta, and Edoardo Lunati.
Mordente takes as input a pair of SEAndroid policies and a file containing a list of CML formulas to verify.
The artifact also includes an auxiliary tool to extract SEAndroid policies from Android images, so they can be passed as input to Mordente. 
As a minimal example, we provide a pair of simple policies and instructions for running a kick-the-tire test. 
Finally, we provide instructions to recover the real-world policies used in our paper for performance evaluation, and a script for replicating our results.

## Comparative Modal Logic CML

Comparative Modal Logic is a logic for comparing different versions of the same system, each represented as a transition system with states labeled by the properties of interest (a Kripke structure). 
In this case, the transition systems are composed by:
- A set of states representing files and other system entities of Android devices;
- A transition relation representing the information flow between files caused by operations that are permitted by the SEAndroid policy.

The syntax of a CML formula `P` is defined by the following grammar:
```
P ::= true | s | P and P | not P | label_i (P) | ito_i P | ifrom_i P
```
where
- `s` is an atomic proposition represeting predefined security label defined below
- `i` is an integer representing the number of one of the two policies, i.e. either `1` or `2`
- `true`, `and`, `not` have the usual intuitive meaning
- `label_i P` is satisfied by a state if `P` is satisfied in the version `i` (corresponds to the up arrow symbol used in the paper)
- `ito_i P` is satisfied by a state if at least a reachable state satisfies `P` (corresponds to the white diamond symbol used in the paper)
- `ifrom_i P` is satisfied by a state if it can be reached by at least a state satisfying `P` (corresponds to the white diamond symbol used in the paper)


### Atomic Propositions

The valid CML atomic propositions that can be used with Mordente are:
- Any type name of the SEAndroid configurations in input
- The three special propositions `crit`, `untr` and `usr`, which stands for critical, untrusted and usr, and are associated with files by an heuristic based on the label name, its substrings and some common naming conventions for SEAndroid configurations.

## Installation
The file named `morente_image` contains the docker image of Mordente.


### Prerequisites

TODO

### Setting up the Mordente container
First create a container with the provided Mordente image.
```
docker container create -it --name mordente {mordente_image}
```

Connect to the container with
```
docker container start mordente
docker exec -it mordente /bin/bash
```

## Usage

Mordente takes as input a file containing the list of CML queries and two SEAndroid policies one's whishes to compare.
To use Mordente, run the following command:
```
mordente {queries} {policy1} {policy2}
```
Where
- `queries` is a file containing any number of CML formulas, one per line
- `policy1` is the file of the first SEAndroid file
- `policy2` is the file of the second SEAndroid file

### Extracting Policies from an Android Images with SEAExtract

SEAExtract is an auxiliary tool that helps you extract the SEAndroid policy of a given Android Image.
Tu use it, run the following command:
```
SEAExtract {image} {policy}
```
Where
- `image` is the Android image file
- `policy` is the filepath where SEAExtract will write the extracted policy

## Kick-the-tire Test

The files `simplePolicy1` and `simplePolicy2` contains simple SEAndroid policies for the test, and `CMLformulas` some properties to verify.
To test `Mordente`, run the following command:
```
mordente CMLformulas simplePolicy1 simplePolicy2
```

The expected output is as follows:
```
Expected output
```

## How to Replicate the Experiments of the Paper


### Downloading the policies required to perform the experiments
The real-world SEAndroid policies that we used for performance evaluation can be retrived as detailed below.

First, each respective firmware image must be downloaded from the manufacturers websites:

| Number | Android Image                                 | url to the image      |
| ------ | ----------------------------------------------| --------------------- |
|   1    | Pixel 9 Pro Fold (Comet) - Android version 14 | https://dl.google.com/dl/android/aosp/comet-ota-ad1a.240530.030-98066022.zip |
|   2    | Pixel 9 Pro Fold (Comet) - Android version 15 | https://dl.google.com/dl/android/aosp/comet-ota-ap3a.241005.015-5350adac.zip |
|   3    | Pixel 9 Pro Fold (Comet) - Android version 16 | https://dl.google.com/dl/android/aosp/comet-ota-bp2a.250605.031.a3-b6c67e0a.zip |
|   4    | Xiaomi 11T                                    | https://c.mi.com/global/miuidownload/detail/device/1900400: |
|   5    | Xiaomi 14T                                    | https://c.mi.com/global/miuidownload/detail/device/1903070: |
|   6    | Xiaomi 15T                                    | https://c.mi.com/global/miuidownload/detail/device/1903375: |

Once downloaded they should be copied inside the container, and their names changed as follows, where `#n` is the number of the image.
```
docker cp {downloaded_file_of_image_#n.zip} mordente:/usr/local/Mordente/{p#n}.zip  
```

>> sudo non funziona, facciamo versione extract ad-hoc

## Manually Replicating the Experiments

To compare a pair of real-world policies, use our auxiliary tool SEAExtract to extract the SEAndroid policies from the images above.
Assuming you want to compare the policies numbered `#n` and `#m`, you can run:
```
SEAExtract /usr/local/Mordente/{p#n}.zip /usr/local/Mordente/{p#n}_policy
SEAExtract /usr/local/Mordente/{p#m}.zip /usr/local/Mordente/{p#m}_policy
```

Then, you can use Mordente with the predefined set of queries described in the paper appendix, which are stored in the file rw_queries.
```
mordente rw_queries /usr/local/Mordente/{p#n}_policy /usr/local/Mordente/{p#m}_policy
```

## Running the Experiment Script

By running the script `experiments.py`, you can replicate the performance tests described in the paper.
The script is executed as follows:
```
./experiments.py
```

The expected time needed to run all the experiments is roughly xxx minutes. The output should be as follows (se e' troppo lungo mettiamolo in un file).

---------





# Cose vecchie o rimosse, qualcosa va rimesso (lasciato vuoto sopra, ad esempio i prerequisiti), ma non so cosa. Rimettete pure quello che non dovevo togliere

By default, a predefined list of queries will be perfomed.
Use the option `--queries` together with a path to specify a different set of queries (one per line).



## Prerequisites
Clone the main repository
```
git clone https://github.com/edoxthebest/Mordente.git
```

Clone the libraries on which Mordente relies
```
cd mordente
%git clone https://github.com/edoxthebest/mata.git
git clone --branch 1.20.0 --depth 1 https://github.com/VeriFIT/mata
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



## TODOs
Installazione: assumendo di avere l'immagine gia pronta non dovrebbe essere complicato
  basta creare un container e poi c'e da scaricare le politiche
Mancano poi le policy da scaricare
Si puo avere linux/amd64 and linux/arm64 -> da specificare credo
da recuperare le politiche di esempio per lo smoke test
migliorare come utilizzare il tool
  da aggiornare il codice del main
  da spiegare la sintassi delle queries
