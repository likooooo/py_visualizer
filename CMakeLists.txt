cmake_minimum_required(VERSION 3.12)
project(py_visualizer)

find_package(Boost COMPONENTS python numpy REQUIRED)
if(Boost_FOUND)
    message(STATUS "Found Boost version ${Boost_VERSION}")
    include_directories(${Boost_INCLUDE_DIRS})
    # Check if Python component of Boost is found
    if(TARGET Boost::python)
        message(STATUS "Boost.Python found")
    else()
        message(FATAL_ERROR "Boost.Python not found")
    endif()
else()
    message(FATAL_ERROR "Boost not found")
endif()

find_package(PythonLibs 3 REQUIRED)
include_directories(${Boost_INCLUDE_DIRS} ${PYTHON_INCLUDE_DIRS})

add_executable(py_gui gui.cpp)
add_library(py_visualizer gui.cpp)

# 设置链接库
target_link_libraries(py_gui PUBLIC ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} )
target_link_libraries(py_visualizer PUBLIC ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} )

add_custom_command(TARGET py_visualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    ${CMAKE_SOURCE_DIR}/visualizer.py
    $<TARGET_FILE_DIR:py_visualizer>
)

install(TARGETS py_gui py_visualizer EXPORT CudaTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)
install(DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
    DESTINATION include
    FILES_MATCHING 
        PATTERN "*.hpp"
        PATTERN "*.h"
        PATTERN "*.py"
        PATTERN "build" EXCLUDE
)
install(FILES
    "${CMAKE_CURRENT_SOURCE_DIR}/py_visualizerConfig.cmake"
    "${CMAKE_CURRENT_SOURCE_DIR}/py_visualizer-config-version.cmake"
    DESTINATION cmake
)