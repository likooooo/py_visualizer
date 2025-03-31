#pragma once
#include <boost/python.hpp>
#include <boost/python/numpy.hpp>
#include <filesystem>
#include <cassert>
#include <iostream>
#include <map>
#include <algorithm>
#include <cstring>

#define catch_py_error(code) do{try{code;}catch (py::error_already_set) {PyErr_Print();exit(1);}}while(0)

namespace py = boost::python;
namespace np = boost::python::numpy;
namespace boost::python
{
    // 只是为了可读性...
    using list_tuple = py::list;
    using listi = py::list;
    using listf = py::list;
    using listc = py::list;

    using list2di = py::list;
    using list2df = py::list;
    using list2dc = py::list;
    using list2d = py::list;
    

    namespace numpy
    {
        using list_array2d = py::list;

        using array1di = np::ndarray;
        using array1df = np::ndarray;
        using array1dc = np::ndarray;
        using array1d = np::ndarray;


        using array2di = np::ndarray;
        using array2df = np::ndarray;
        using array2dc = np::ndarray;
        using array2d = np::ndarray;
        
        using array3di = np::ndarray;
        using array3df = np::ndarray;
        using array3dc = np::ndarray;
        using array3d = np::ndarray;      
    }
}
struct py_engine{
    bool is_py_running;
    py_engine(bool init = false);
    ~py_engine();
    void operator = (py_engine&& py);

    static void init();
    static void init_exception_for_pycall();
    static void dispose();
private:
    static py_engine& get_py_inter();
};


struct pyobject_wrapper : public py::object {
    pyobject_wrapper() = default;
    explicit pyobject_wrapper(const py::object& obj) :py::object(obj){}
    inline pyobject_wrapper operator [](const char* key) const { return pyobject_wrapper(py::object::attr(key)); }
    inline pyobject_wrapper operator [](const std::string& key) const { return pyobject_wrapper(py::object::attr(key.c_str())); }
};

inline py::list add_path_to_sys_path(const char* path) {
    py::object py_path;
    catch_py_error(py_path = py::import("sys"));
    catch_py_error(py_path = py_path.attr("path"));
    py::list sys_path = py::extract<py::list>(py_path);
    sys_path.append(path);
    return sys_path;
}
struct py_loader final
{
    using module_map = std::map<std::string, pyobject_wrapper>;
    module_map modules;
    py_loader() = default;
    py_loader(const std::filesystem::path& path){
        reset_current(path);
    }
    void reset_current(const std::filesystem::path& path){
        modules.clear();
        append_import_to_current(path);
    }
    void append_import_to_current(const std::filesystem::path& path) {
        namespace fs = std::filesystem;
        if (fs::is_directory(path)) {
            add_path_to_sys_path(path.c_str());
            for (const auto& entry : fs::directory_iterator(path)) {
                this->append_import_to_current(entry.path());
            }
        } 
        else {
            constexpr std::array<const char*, 2> suffix{".py", ".pyd"};
            const std::string suf = path.extension();
            if (suffix.end() == std::find_if(suffix.begin(), suffix.end(), [&suf](const char* a){ return 0 == std::strcmp(a, suf.c_str()); }))
                return;
            std::string file = path.stem().string();
            catch_py_error(
                py::object obj = py::import(file.c_str());
                if (obj.is_none()) throw std::range_error("import module failed in "  + file);
                modules[file] = pyobject_wrapper(obj);
                std::cout << "    load plugin " << path.stem() << " success" << std::endl;

            );
        }
    }
    pyobject_wrapper operator[](const std::string& module_name) const {
        auto it = modules.find(module_name);
        if (modules.end() == it) throw std::range_error("can't find module " + module_name);
        return it->second;
    }
};

struct py_plugin
{
    static std::vector<std::string> paths;
    static py_loader& ref();
    template<class T, class ...Args> static T call(const std::string& module, const std::string& func, Args&& ...args)
    {
        constexpr bool is_void_return = std::is_same<void, T>::value;
        if constexpr (!is_void_return)
        {
            catch_py_error(return py::extract<T>(ref()[module][func](std::forward<Args>(args)...)));
        }
        else{
            catch_py_error(ref()[module][func](std::forward<Args>(args)...));
        }
    } 
    static py::object exec(const std::vector<std::string>& console_cmd)
    {
        py::list args(console_cmd);
        py::object main_module, main_namespace;
        catch_py_error(main_module = py::import("__main__"));
        catch_py_error(main_namespace = main_module.attr("__dict__"));
        auto old_args = py::import("sys").attr("argv");
        py::import("sys").attr("argv") = py::list(console_cmd);
        catch_py_error(py::exec_file(console_cmd.front().c_str(), main_namespace));
        py::import("sys").attr("argv") = old_args;
        return main_namespace;
    } 
};