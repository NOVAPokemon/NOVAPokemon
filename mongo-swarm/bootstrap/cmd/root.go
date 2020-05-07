/*
Copyright © 2019 NAME HERE <EMAIL ADDRESS>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
package cmd

import (
	"fmt"
	"github.com/achan-ns/mongo-swarm/bootstrap/internal/app"
	"github.com/spf13/cobra"
)

var config app.Config

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "bootstrap",
	Short: "Bootstraps mongo locally",
	Long:  `Bootstraps mongo locally`,
	// Uncomment the following line if your bare application
	// has an action associated with it:
	// Run: func(cmd *cobra.Command, args []string) {
	// },
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
	}
	app.Bootstrap_Mongo(config)
}

func init() {
	var debug bool
	rootCmd.PersistentFlags().StringArrayVar(&config.DataSets, "dataSet", []string{}, "MongoDB data cluster")
	rootCmd.PersistentFlags().StringVar(&config.ConfigSet, "configSet", "", "MongoDB config cluster")
	rootCmd.PersistentFlags().StringVar(&config.Mongos, "mongos", "", "Mongos list")
	rootCmd.PersistentFlags().IntVar(&config.Retry, "retry", 100, "retry count")
	rootCmd.PersistentFlags().IntVar(&config.Wait, "wait", 5, "wait time between retries in seconds")
	rootCmd.PersistentFlags().IntVar(&config.Port, "port", 9090, "HTTP server port")
	rootCmd.PersistentFlags().BoolVar(&debug, "debug", false, "Debug Mode")
}
