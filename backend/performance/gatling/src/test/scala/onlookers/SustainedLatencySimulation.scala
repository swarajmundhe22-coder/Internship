package onlookers

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class SustainedLatencySimulation extends Simulation {

  private val baseUrl = System.getProperty("baseUrl", "http://127.0.0.1:8000/api/v1")
  private val tier = System.getProperty("tier", "low")

  private val usersPerSecond = tier match {
    case "low" => 20
    case "medium" => 60
    case "high" => 100
    case _ => 20
  }

  private val durationMinutes = Integer.getInteger("durationMinutes", 60)
  private val chaosRate = java.lang.Double.parseDouble(System.getProperty("chaosRate", "0.01"))

  private val httpProtocol = http
    .baseUrl(baseUrl)
    .acceptHeader("application/json")
    .contentTypeHeader("application/json")

  private val token = System.getProperty("token", "")

  private val feeder = csv("traffic/traffic_pattern_7d.csv").circular

  private val simulatePayload =
    """
      {
        "material": {
          "name": "Carbon Steel",
          "alloy_group": "Ferrous",
          "density_kg_m3": 7850,
          "electrochemical_potential_v": -0.65
        },
        "environment": {
          "temperature_c": 25,
          "relative_humidity_pct": 80,
          "chloride_ppm": 12000,
          "ph": 7.1,
          "dissolved_oxygen_mg_l": 6.4
        },
        "exposed_area_m2": 180,
        "exposure_time_hours": 8760,
        "asset_type": "Pipeline (Submerged)",
        "compliance_standard": "NACE SP0169",
        "criticality": "High",
        "region": "Monsoon Coastal",
        "uv_index": 6,
        "mic_activity": "Medium",
        "soil_resistivity_ohm_cm": 2200
      }
    """

  private val chaosInject = randomSwitch(
    chaosRate -> exec(session => session.set("chaos", true)),
    (1.0 - chaosRate) -> exec(session => session.set("chaos", false))
  )

  private val simulationScenario = scenario("sustained-latency")
    .feed(feeder)
    .exec(chaosInject)
    .doIfOrElse(session => session("scenario").as[String] == "health") {
      exec(http("health").get("/health"))
    } {
      doIfOrElse(session => session("scenario").as[String] == "ops_performance") {
        exec(
          http("ops_performance")
            .get("/ops/performance")
            .header("Authorization", s"Bearer $token")
        )
      } {
        doIfOrElse(session => session("scenario").as[String] == "auth_login") {
          exec(
            http("auth_login")
              .post("/auth/login")
              .body(StringBody("{\"email\":\"load@example.com\",\"password\":\"StrongPass123\"}"))
          )
        } {
          doIfOrElse(session => session("chaos").asOption[Boolean].contains(true)) {
            exec(
              http("simulate_chaos")
                .post("/simulation/simulate")
                .header("Authorization", s"Bearer $token")
                .body(StringBody("{\"material\":{},\"environment\":{}}"))
            )
          } {
            exec(
              http("simulate")
                .post("/simulation/simulate")
                .header("Authorization", s"Bearer $token")
                .body(StringBody(simulatePayload))
            )
          }
        }
      }
    }

  setUp(
    simulationScenario.inject(
      rampUsersPerSec(1).to(usersPerSecond).during(30.seconds),
      constantUsersPerSec(usersPerSecond).during(durationMinutes.minutes)
    )
  ).protocols(httpProtocol)
}
