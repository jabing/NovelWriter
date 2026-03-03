#include <catch2/catch_test_macros.hpp>
#include "jrob/robot.hpp"

TEST_CASE("Robot creation with correct name", "[robot]") {
    jrob::Robot robot("TestBot");
    
    REQUIRE(robot.getName() == "TestBot");
}

TEST_CASE("Robot name can be changed implicitly via construction", "[robot]") {
    jrob::Robot robot1("Robot1");
    jrob::Robot robot2("Robot2");
    
    REQUIRE(robot1.getName() == "Robot1");
    REQUIRE(robot2.getName() == "Robot2");
}

TEST_CASE("Robot with empty name", "[robot]") {
    jrob::Robot robot("");
    
    REQUIRE(robot.getName().empty());
}

TEST_CASE("Robot with long name", "[robot]") {
    std::string longName = "ThisIsAVeryLongRobotNameThatTestsEdgeCases";
    jrob::Robot robot(longName);
    
    REQUIRE(robot.getName() == longName);
}
