#include "jrob/robot.hpp"
#include <iostream>

namespace jrob {

Robot::Robot(const std::string& name) : name_(name) {}

std::string Robot::getName() const {
    return name_;
}

void Robot::sayHello() const {
    std::cout << "Hello! I am " << name_ << ", a jrob robot." << std::endl;
}

} // namespace jrob
