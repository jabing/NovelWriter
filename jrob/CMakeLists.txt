cmake_minimum_required(VERSION 3.16)

project(jrob VERSION 0.1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Include FetchContent for Catch2
include(FetchContent)
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.4.0
)
FetchContent_MakeAvailable(Catch2)

# Include FetchContent for Box2D
FetchContent_Declare(
  box2d
  GIT_REPOSITORY https://github.com/erincatto/box2d.git
  GIT_TAG        v2.4.1
)
FetchContent_MakeAvailable(box2d)

# Collect all source files
file(GLOB_RECURSE JROB_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")

# Create static library
add_library(jrob STATIC ${JROB_SOURCES})

target_include_directories(jrob
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_link_libraries(jrob PUBLIC box2d)

# Enable testing
enable_testing()

# Collect all test files
file(GLOB_RECURSE JROB_TESTS "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp")

# Create test executable if tests exist
if(JROB_TESTS)
    add_executable(jrob_tests ${JROB_TESTS})
    target_link_libraries(jrob_tests PRIVATE jrob Catch2::Catch2WithMain)
    
    # Add test to CTest
    add_test(NAME jrob_tests COMMAND jrob_tests)
endif()

# Create example executables
file(GLOB JROB_EXAMPLES "${CMAKE_CURRENT_SOURCE_DIR}/examples/*.cpp")
foreach(example_file ${JROB_EXAMPLES})
    get_filename_component(example_name ${example_file} NAME_WE)
    add_executable(${example_name} ${example_file})
    target_link_libraries(${example_name} PRIVATE jrob)
endforeach()
