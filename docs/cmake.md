## Building Hermes
First build a distributable package, it will be placed at `[repo-path]/dist`

```sh
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=dist
cmake --build build
cmake --install build
```

## Importing Hermes
```cmake
find_package(hermes 1.0.0
    REQUIRED
    PATHS [repo-path]/dist/cmake
)
```

## Using Hermes

```cmake
cmake_minimum_required(VERSION 3.20)

project(myProject)

find_package(hermes 1.0.0
    REQUIRED
    PATHS [repo-path]/dist/cmake
)

add_hermes_grammar(
    # relative to current CMakeLists
    GRAMMAR grammar/myGrammer.hm
    
    # base directory containing all your grammar files that
    # get imported to the base grammar. These get added to the
    # list of dependencies so CMake will rebuild your grammar automatically
    GRAMMAR_DIR grammar

    # Output target name
    TARGET myParser

    # Optional, Flag to enable detailed parser logs
    DEBUG

    # Optional, Flag to enable strict mode for the parser generator
    # disallowing parse conflicts
    STRICT

    # Optional, filename for an output description file of the generated
    # automata
    DESC_FILE automata.txt
)


add_executable(myExe src/main.cpp)
target_link_libraries(myExe PRIVATE myParser)

```