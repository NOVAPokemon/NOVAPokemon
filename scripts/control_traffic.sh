#!/bin/bash

l_flag=false
b_flag=false
r_flag=false

latency=0
bandwidth=0

function print_usage() {
	echo "bash control_latency.sh [OPTIONS]"
	echo "[OPTIONS]"
	echo "\t-l 20ms\t add 20ms of latency"
	echo "\t-b 100mbit\t limits egress bandwidth to 100mbit"
	echo "\t-r\tremove latency and bandwidth"
}

while getopts 'l:b:r' flag; do
  case "${flag}" in
    l) l_flag=true
	latency=${OPTARG}
	;;
    b) b_flag=true
    	bandwidth=${OPTARG}
	;;
    r) r_flag=true ;;
    *) print_usage
       exit 1 ;;
  esac
done

pods=$(kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')

for pod in $pods; do
	if [[ $pod =~ kibana || $pod =~ elastic || $pod =~ chaos-chaos ]]; then
		echo "skipped - $pod"
		continue
	fi

	if [ "$l_flag" = true ] && [ "$b_flag" = false ]; then
		echo "adding $latency to pod $pod"
		kubectl exec $pod -- sh -c "tc qdisc add dev eth0 root netem delay $latency"
	elif [ "$l_flag" = true ] && [ "$b_flag" = true ]; then
		echo "adding $latency and limiting bandwidth to $bandwidth to pod $pod"
		kubectl exec $pod -- sh -c "tc qdisc add dev eth0 root tbf rate $bandwidth burst 32kbit latency $latency"
	elif [ "$r_flag" = true ]; then
		echo "removing latency from pod $pod"
		kubectl exec $pod -- sh -c "tc qdisc del dev eth0 root"
	fi
done
