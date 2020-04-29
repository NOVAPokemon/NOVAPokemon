package app

import (
	"errors"
	"fmt"
	"strings"
)

type Config struct {
	DataSets  []string // we support sharding, so each element in here is a dataset
	ConfigSet string
	Mongos    string
	Retry     int
	Wait      int
	Port      int
}

// ReplicaSet format <replicaSetName>/data1:27017,data2:27017,data3:27017
func ParseReplicaSet(definition string) (string, []string, error) {

	parts := strings.Split(definition, "/")

	replSetName := parts[0]

	members := strings.Split(parts[1], ",")

	if len(members) < 1 {
		return "", nil, errors.New("Invalid ReplicaSet definition, a minimum of 1 member required")
	}

	return replSetName, members, nil
}

func ParseMongos(definition string) ([]string, error) {
	list := strings.Split(definition, ",")

	for _, mongos := range list {
		parts := strings.Split(mongos, ":")
		if len(parts) != 2 {
			return nil, errors.New(fmt.Sprint("%v invalid format, expected <HOST>:<PORT>", mongos))
		}
	}

	return list, nil
}
