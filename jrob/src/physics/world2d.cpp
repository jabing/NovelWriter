#include "jrob/physics/world2d.hpp"

namespace jrob {

World2D::World2D(b2Vec2 gravity) : world_(std::make_unique<b2World>(gravity)) {}

World2D::~World2D() = default;

World2D::World2D(World2D&&) noexcept = default;

World2D& World2D::operator=(World2D&&) noexcept = default;

void World2D::step(float timeStep, int velocityIterations, int positionIterations) {
    world_->Step(timeStep, velocityIterations, positionIterations);
}

b2Body* World2D::createGround(float width) {
    b2BodyDef bodyDef;
    bodyDef.type = b2_staticBody;
    bodyDef.position.Set(0.0f, 0.0f);
    
    b2Body* body = world_->CreateBody(&bodyDef);
    
    b2EdgeShape shape;
    shape.SetTwoSided(b2Vec2(-width / 2.0f, 0.0f), b2Vec2(width / 2.0f, 0.0f));
    
    body->CreateFixture(&shape, 0.0f);
    
    return body;
}

b2Body* World2D::createBox(float x, float y, float width, float height, bool dynamic) {
    b2BodyDef bodyDef;
    bodyDef.type = dynamic ? b2_dynamicBody : b2_staticBody;
    bodyDef.position.Set(x, y);
    
    b2Body* body = world_->CreateBody(&bodyDef);
    
    b2PolygonShape shape;
    shape.SetAsBox(width / 2.0f, height / 2.0f);
    
    b2FixtureDef fixtureDef;
    fixtureDef.shape = &shape;
    fixtureDef.density = dynamic ? 1.0f : 0.0f;
    fixtureDef.friction = 0.3f;
    
    body->CreateFixture(&fixtureDef);
    
    return body;
}

} // namespace jrob
