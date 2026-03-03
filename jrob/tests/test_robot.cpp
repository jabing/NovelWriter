#include "jrob/robot.hpp"
#include <iostream>

int main() {
    std::cout << "Running jrob tests..." << std::endl;
    
    jrob::Robot robot("TestBot");
    
    if (robot.getName() != "TestBot") {
        std::cerr << "FAILED: Robot name mismatch" << std::endl;
        return 1;
    }
    
    std::cout << "Test 1 passed: Robot created with correct name" << std::endl;
    
    robot.sayHello();
    
    std::cout << "All tests passed!" << std::endl;
    return 0;
}
