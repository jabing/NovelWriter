#pragma once

#include <string>

namespace jrob {

class Robot {
public:
    Robot(const std::string& name);
    
    std::string getName() const;
    void sayHello() const;

private:
    std::string name_;
};

} // namespace jrob
