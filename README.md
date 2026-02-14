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
- The three special propositions `CRITICAL`, `UNTRUSTED` and `TRUSTED`, which are associated with files by an heuristic based on the label name, its substrings and some common naming conventions for SEAndroid configurations.

## Installation
A docker image containing Mordente is provided for both linux/amd64 and linux/arm64 systems.
The tool relies on SETools, a collection of libraries to analyse SELinux policies, and thus it is not available on other ecosystems.


The file named `mordente.tar.gz` contained in the folder `images` contains the docker image of Mordente which can be loaded with the following.
```
docker load < images/mordente.tar.gz
```

### Setting up the Mordente container
First create a container with the provided Mordente image.
```
docker container create -it -v ./policies:/usr/local/Mordente/policies --name mordente edoxthebest/mordente
```

Then you can run the container and connect to it as follows.
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



## Kick-the-tire Test

The folders `simplePolicy1` and `simplePolicy2` located inside `policies` contain minimal SEAndroid policies; these, together with the formulas contained in `queries/CMLformulas`, can be used to perform a smoke test.

To test `Mordente`, run the following command:
```
mordente queries/CMLformulas policies/simplePolicy1 policies/simplePolicy2
```

The expected output is as follows (some lines are omitted for brevity):
```
# mordente queries/CMLformulas policies/simplePolicy1 policies/simplePolicy2 

2026-02-13 14:29:53,701 [INFO ]  Starting comparison of the specified policies.
...
2026-02-13 14:29:53,748 [INFO ]  Built InfoFlowGraph [N 5] [E 9] in 0.0018181800842285156.
2026-02-13 14:29:53,794 [INFO ]  Query perfomed `label_2 (CRITICAL) and not label_1 (CRITICAL)`
2026-02-13 14:29:53,794 [INFO ]         TRUE
2026-02-13 14:29:53,795 [INFO ]  Query perfomed `ito_2(label_2(CRITICAL)) and not ito_1(label_2(CRITICAL))`
2026-02-13 14:29:53,795 [INFO ]         FALSE, the following labels are counterexamples {('untrustedB', 'untrustedB'), ('untrustedA', 'safeD')}
2026-02-13 14:29:53,795 [INFO ]  Perfomed 2 queries in 0.046329498291015625.
```


## How to Replicate the Experiments of the Paper

### Downloading the policies required to perform the experiments
The real-world SEAndroid policies that we used for performance evaluation can be retrived as detailed below.

First, each respective firmware image must be downloaded from the manufacturers websites:

| Number | Android Image                                 | URLs      |
| ------ | ----------------------------------------------| --------------------- |
|   1    | Pixel 9 Pro Fold (Comet) - Android version 14 | https://dl.google.com/dl/android/aosp/comet-ota-ad1a.240530.030-98066022.zip |
|   2    | Pixel 9 Pro Fold (Comet) - Android version 15 | https://dl.google.com/dl/android/aosp/comet-ota-ap3a.241005.015-5350adac.zip |
|   3    | Pixel 9 Pro Fold (Comet) - Android version 16 | https://dl.google.com/dl/android/aosp/comet-ota-bp2a.250605.031.a3-b6c67e0a.zip |
|   4    | Xiaomi 11T                                    | https://c.mi.com/global/miuidownload/detail/device/1900400 |
|   5    | Xiaomi 14T                                    | https://c.mi.com/global/miuidownload/detail/device/1903070 |
|   6    | Xiaomi 15T                                    | https://c.mi.com/global/miuidownload/detail/device/1903375 |

Once the firmware is downloaded, copy the zip file to the shared `policies` folder, then connect to the container and extract the SEAndroid policy as follows.


### Extracting Policies from an Android Images with SEAExtract
SEAExtract is an auxiliary script that helps you extract the SEAndroid policy of a given Android Image.
To use it, run the following command inside the Mordente container:
```
./SEAExtract [--xiaomi] {image} {policy}
```
Where
- `image` is the Android image file
- `policy` is the filepath where SEAExtract will write the extracted policy
- `--xiaomi` should be used when extracting xiaomi policies

The following should extract all the policies required to replicate the experiments (assuming all have been downloaded and placed in the `policies` folder).
```
cd policies
../SEAExtract comet-ota-ad1a.240530.030-98066022.zip p1
../SEAExtract comet-ota-ap3a.241005.015-5350adac.zip p2
../SEAExtract comet-ota-bp2a.250605.031.a3-b6c67e0a.zip p3
../SEAExtract --xiaomi miui_AGATEGlobal_OS1.0.17.0.UKWMIXM_2deb69168e_14.0.zip p4
../SEAExtract --xiaomi degas_global-ota_full-OS2.0.208.0.VNEMIXM-user-15.0-4434ede5b4.zip p5
../SEAExtract --xiaomi goya_global-ota_full-OS3.0.8.0.WOEMIXM-user-16.0-345b449a05.zip p6
cd ..
```


### Running the Experiments
To perform the experiments on a default set of queries as detailed in the correlated paper use Mordente as follows.
```
mordente queries/experiments policies/p1 policies/p2
mordente queries/experiments policies/p2 policies/p3
mordente queries/experiments policies/p1 policies/p4
mordente queries/experiments policies/p2 policies/p5
mordente queries/experiments policies/p2 policies/p6
```

The expected time needed to run all the experiments is roughly 120 minutes.
<!-- The output should be as follows (se e' troppo lungo mettiamolo in un file). -->


## Manual installation

Alternatively, the docker image can be built locally with the provided dockerfile with the following.

```
docker build --platform linux/{amd64 | arm64} -t mordente .
```
