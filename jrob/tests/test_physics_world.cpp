#include <catch2/catch_test_macros.hpp>
#include "jrob/physics/world2d.hpp"

TEST_CASE("World2D can be created with default gravity", "[physics][world2d]") {
    jrob::World2D world;
    
    REQUIRE(world.getWorld() != nullptr);
}

TEST_CASE("World2D can be created with custom gravity", "[physics][world2d]") {
    b2Vec2 gravity(0.0f, -10.0f);
    jrob::World2D world(gravity);
    
    REQUIRE(world.getWorld() != nullptr);
}

TEST_CASE("World2D can step simulation", "[physics][world2d]") {
    jrob::World2D world;
    
    // Step the simulation - should not crash
    REQUIRE_NOTHROW(world.step(1.0f / 60.0f));
    
    // Step multiple times
    for (int i = 0; i < 10; ++i) {
        REQUIRE_NOTHROW(world.step(1.0f / 60.0f));
    }
}

TEST_CASE("World2D can create ground", "[physics][world2d]") {
    jrob::World2D world;
    
    b2Body* ground = world.createGround(50.0f);
    
    REQUIRE(ground != nullptr);
    REQUIRE(ground->GetType() == b2_staticBody);
}

TEST_CASE("World2D can create dynamic box", "[physics][world2d]") {
    jrob::World2D world;
    
    b2Body* box = world.createBox(0.0f, 10.0f, 1.0f, 1.0f, true);
    
    REQUIRE(box != nullptr);
    REQUIRE(box->GetType() == b2_dynamicBody);
}

TEST_CASE("World2D can create static box", "[physics][world2d]") {
    jrob::World2D world;
    
    b2Body* box = world.createBox(0.0f, 10.0f, 1.0f, 1.0f, false);
    
    REQUIRE(box != nullptr);
    REQUIRE(box->GetType() == b2_staticBody);
}

TEST_CASE("World2D box falls under gravity", "[physics][world2d]") {
    jrob::World2D world(b2Vec2(0.0f, -9.8f));
    
    // Create ground
    world.createGround(50.0f);
    
    // Create box above ground
    b2Body* box = world.createBox(0.0f, 10.0f, 1.0f, 1.0f, true);
    float initialY = box->GetPosition().y;
    
    // Step simulation
    for (int i = 0; i < 60; ++i) {
        world.step(1.0f / 60.0f);
    }
    
    // Box should have fallen
    float finalY = box->GetPosition().y;
    REQUIRE(finalY < initialY);
}

TEST_CASE("World2D supports move semantics", "[physics][world2d]") {
    jrob::World2D world1;
    
    // Move construct
    jrob::World2D world2(std::move(world1));
    REQUIRE(world2.getWorld() != nullptr);
    
    // Move assign
    jrob::World2D world3;
    world3 = std::move(world2);
    REQUIRE(world3.getWorld() != nullptr);
}
