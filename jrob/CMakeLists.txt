cmake_minimum_required(VERSION 3.16)

project(jrob VERSION 0.1.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Collect all source files
file(GLOB_RECURSE JROB_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")

# Create static library
add_library(jrob STATIC ${JROB_SOURCES})

target_include_directories(jrob
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# Collect all test files
file(GLOB_RECURSE JROB_TESTS "${CMAKE_CURRENT_SOURCE_DIR}/tests/*.cpp")

# Create test executable if tests exist
if(JROB_TESTS)
    add_executable(jrob_tests ${JROB_TESTS})
    target_link_libraries(jrob_tests PRIVATE jrob)
endif()

# Create example executables
file(GLOB JROB_EXAMPLES "${CMAKE_CURRENT_SOURCE_DIR}/examples/*.cpp")
foreach(example_file ${JROB_EXAMPLES})
    get_filename_component(example_name ${example_file} NAME_WE)
    add_executable(${example_name} ${example_file})
    target_link_libraries(${example_name} PRIVATE jrob)
endforeach()
