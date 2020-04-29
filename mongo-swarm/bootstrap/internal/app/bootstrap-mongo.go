package app

import (
	logger "github.com/sirupsen/logrus"
)

func Bootstrap_Mongo(config Config) {

	for _, dataset := range config.DataSets {
		dataReplSetName, dataMembers, err := ParseReplicaSet(dataset)

		if err != nil {
			logger.Fatal(err)
		}

		logger.Infof("Bootstrap started for data cluster %v members %v", dataReplSetName, dataMembers)

		dataReplSet := &ReplicaSet{
			Name:    dataReplSetName,
			Members: dataMembers,
		}

		err = dataReplSet.InitWithRetry(config.Retry, config.Wait)
		if err != nil {
			logger.Fatal(err)
		}
		logger.Infof("%v replica set initialized successfully", dataReplSetName)

		hasPrimary, err := dataReplSet.WaitForPrimary(config.Retry, config.Wait)
		if err != nil {
			logger.Fatal(err)
		}
		dataReplSet.PrintStatus()
		if !hasPrimary {
			logger.Fatalf("No primary node found for replica set %v", dataReplSetName)
		}
	}

	cfgReplSetName, cfgMembers, err := ParseReplicaSet(config.ConfigSet)
	if err != nil {
		logger.Fatal(err)
	}

	logger.Infof("Bootstrap started for config cluster %v members %v", cfgReplSetName, cfgMembers)

	cfgReplSet := &ReplicaSet{
		Name:    cfgReplSetName,
		Members: cfgMembers,
	}

	err = cfgReplSet.InitWithRetry(config.Retry, config.Wait)
	if err != nil {
		logger.Fatal(err)
	}
	logger.Infof("%v replica set initialized successfully", cfgReplSetName)

	hasPrimary, err := cfgReplSet.WaitForPrimary(config.Retry, config.Wait)
	if err != nil {
		logger.Fatal(err)
	}
	cfgReplSet.PrintStatus()
	if !hasPrimary {
		logger.Fatalf("No primary node found for replica set %v", cfgReplSetName)
	}

	mongosList, err := ParseMongos(config.Mongos)
	if err != nil {
		logger.Fatal(err)
	}

	logger.Infof("Bootstrap started for mongos %v", mongosList)
	for _, mongos := range mongosList {

		err := pingWithRetry(mongos, config.Retry, config.Wait)
		if err != nil {
			logger.Fatalf("% mongos connection failed", mongos)
		} else {
			logger.Infof("%v is online", mongos)
		}

		m := &Mongos{
			Address:        mongos,
			ReplicaSetUrls: config.DataSets,
		}

		err = m.Init()
		if err != nil {
			logger.Fatal(err)
		}

		logger.Infof("%v shard added", mongos)
		logger.Info("Replica sets: ", m.ReplicaSetUrls)

	}

	logger.Info("Bootstrap finished successfully!")
}
