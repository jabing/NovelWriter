#pragma once
#include <box2d/box2d.h>
#include <memory>

namespace jrob {

class World2D {
public:
    explicit World2D(b2Vec2 gravity = b2Vec2(0.0f, -9.8f));
    ~World2D();
    
    // Disable copy, enable move
    World2D(const World2D&) = delete;
    World2D& operator=(const World2D&) = delete;
    World2D(World2D&&) noexcept;
    World2D& operator=(World2D&&) noexcept;
    
    void step(float timeStep, int velocityIterations = 6, int positionIterations = 2);
    
    b2Body* createGround(float width = 50.0f);
    b2Body* createBox(float x, float y, float width, float height, bool dynamic = true);
    
    b2World* getWorld() const { return world_.get(); }
    
private:
    std::unique_ptr<b2World> world_;
};

} // namespace jrob
