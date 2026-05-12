name := "onlookers-gatling-suite"

version := "1.0.0"

scalaVersion := "2.13.12"

libraryDependencies ++= Seq(
  "io.gatling" % "gatling-test-framework" % "3.12.0" % Test,
  "io.gatling.highcharts" % "gatling-charts-highcharts" % "3.12.0" % Test
)

enablePlugins(GatlingPlugin)
