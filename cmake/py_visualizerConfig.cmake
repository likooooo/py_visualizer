# py_visualizerConfig.cmake - Configuration file for the py_visualizer package.

# Ensure that this script is included only once.
if(TARGET py_visualizer)
    return()
endif()

# Get the directory where this file is located.
get_filename_component(_current_dir "${CMAKE_CURRENT_LIST_FILE}" PATH)

# Include the exported targets file.
include("${_current_dir}/py_visualizerTargets.cmake")
include("${_current_dir}/py_visualizer_files.cmake")

# Set the package version variables.
set(py_visualizer_VERSION_MAJOR 1) # Replace with your major version
set(py_visualizer_VERSION_MINOR 0) # Replace with your minor version
set(py_visualizer_VERSION_PATCH 0) # Replace with your patch version
set(py_visualizer_VERSION "${py_visualizer_VERSION_MAJOR}.${py_visualizer_VERSION_MINOR}.${py_visualizer_VERSION_PATCH}")

# Check if the requested version is compatible.
if(NOT "${py_visualizer_FIND_VERSION}" STREQUAL "")
    if(NOT "${py_visualizer_FIND_VERSION}" VERSION_LESS "${py_visualizer_VERSION}")
        set(py_visualizer_VERSION_COMPATIBLE TRUE)
    endif()

    if("${py_visualizer_FIND_VERSION}" VERSION_EQUAL "${py_visualizer_VERSION}")
        set(py_visualizer_VERSION_EXACT TRUE)
    endif()
endif()

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
# Mark the package as found.
set(py_visualizer_FOUND TRUE)


function(copy_visualizer_files TARGET_NAME Dir)
    get_filename_component(TEST_WLE ${PY_VISUALIZER_FILES} NAME_WLE)

    add_custom_command(
        TARGET ${TARGET_NAME} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                ${PY_VISUALIZER_FILES}
                "${Dir}/${TEST_WLE}"
        COMMENT "Copying ${TEST_WLE} to ${Dir}/${TEST_WLE}"
    )
endfunction()