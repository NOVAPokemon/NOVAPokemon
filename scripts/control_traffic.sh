#!/bin/bash

l_flag=false
b_flag=false
r_flag=false

latency=0
bandwidth=0

function print_usage() {
	echo "bash control_latency.sh [OPTIONS]"
	echo "[OPTIONS]"
	echo "	-l 20ms	 	add 20ms of latency"
	echo "	-b 100mbit	limits egress bandwidth to 100mbit"
	echo "	-r		remove latency and bandwidth"
}

while getopts 'l:b:r' flag; do
  case "${flag}" in
    l)  l_flag=true
	latency=${OPTARG}
	;;
    b)  b_flag=true
    	bandwidth=${OPTARG}
	;;
    r) r_flag=true
	 ;;
    *) print_usage
       exit 1 ;;
  esac
done

pods=$(kubectl get pods --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')

function control_traffic_for_pod() {
  if [[ $pod =~ kibana || $pod =~ elastic || $pod =~ chaos-chaos ]]; then
		echo "skipped - $pod"
		continue
	fi

	if [ "$r_flag" = true ]; then
		echo "removing latency from pod $pod"
                kubectl exec "$pod" -- sh -c "tc qdisc del dev eth0 root"
		continue
	else
		kubectl exec "$pod" -- sh -c "tc qdisc add dev eth0 root handle 1:0 htb default 10"
	fi


	if [ "$b_flag" = true ]; then
                echo "limiting bandwidth to $bandwidth on pod $pod"
                kubectl exec "$pod" -- sh -c "tc class add dev eth0 parent 1:0 classid 1:10 htb rate $bandwidth prio 0"
	else
		kubectl exec "$pod" -- sh -c "tc class add dev eth0 parent 1:0 classid 1:10 htb rate 40gbit prio 0"
	fi

	if [ "$l_flag" = true ]; then
		echo "adding $latency to pod $pod"
		kubectl exec "$pod" -- sh -c "tc qdisc add dev eth0 parent 1:10 handle 110: netem delay $latency"
	fi

	kubectl exec "$pod" -- sh -c "tc filter add dev eth0 parent 1:0 prio 0 protocol ip handle 10 fw flowid 1:10"
}

for pod in $pods; do
	control_traffic_for_pod &
done
