cmake_minimum_required(VERSION 3.21)
project(RenameUI LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOUIC_SEARCH_PATHS ui)
find_package(Qt6 6.5 COMPONENTS Widgets REQUIRED)

add_executable(RenameUI
    src/main.cpp
    src/widget.h
    src/widget.cpp
    ui/Widget.ui
)

target_link_libraries(RenameUI PRIVATE Qt6::Widgets)


add_custom_command(TARGET RenameUI POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory
            $<TARGET_FILE_DIR:RenameUI>/scripts
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
            ${CMAKE_SOURCE_DIR}/scripts/rename_by_excel.py
            $<TARGET_FILE_DIR:RenameUI>/scripts/rename_by_excel.py
)
