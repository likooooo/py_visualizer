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

find_package(type_traist_notebook REQUIRED)
find_package(PythonLibs 3 REQUIRED)
include_directories(${Boost_INCLUDE_DIRS} ${PYTHON_INCLUDE_DIRS})

add_executable(py_gui gui.cpp)
add_library(py_visualizer SHARED py_plugin.cpp)

# 设置链接库
target_link_libraries(py_visualizer PUBLIC ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} )
# target_link_libraries(py_gui PUBLIC ${Boost_LIBRARIES} ${PYTHON_LIBRARIES} )
target_link_libraries(py_gui PUBLIC py_visualizer)


add_custom_command(TARGET py_visualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    ${CMAKE_SOURCE_DIR}/visualizer.py
    $<TARGET_FILE_DIR:py_visualizer>
)

install(EXPORT CudaTargets
    FILE py_visualizerTargets.cmake
    NAMESPACE py_visualizer::
    DESTINATION cmake
)

install(TARGETS py_gui py_visualizer EXPORT CudaTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)
install(FILES 
    ${CMAKE_CURRENT_SOURCE_DIR}/py_helper.hpp 
    ${CMAKE_CURRENT_SOURCE_DIR}/py_plugin.h
    DESTINATION include)

set(PY_VISUALIZER_FILES ${CMAKE_INSTALL_PREFIX}/bin/visualizer.py)
set(PY_PY_PLUGINS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/core_plugins)
install(FILES 
    ${PY_VISUALIZER_FILES}
    DESTINATION bin)
install(DIRECTORY 
    ${PY_PY_PLUGINS_DIR}
    DESTINATION bin)

configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/py_visualizer_files.cmake.in
    ${CMAKE_CURRENT_SOURCE_DIR}/cmake/py_visualizer_files.cmake
)

install(FILES
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/py_visualizerConfig.cmake"
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/py_visualizer_files.cmake"
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/py_visualizer-config-version.cmake"
    DESTINATION cmake
)
include(${PROJECT_SOURCE_DIR}/cmake/auto_ctest.cmake)