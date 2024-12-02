#include <boost/python.hpp>
#include <boost/python/numpy.hpp>
#include <filesystem>
#include <cassert>
#include <iostream>
#include <map>
#include <algorithm>
#include <cstring>
// #include "common.h"

#define catch_py_error(code) do{try{code;}catch (py::error_already_set) {PyErr_Print();exit(1);}}while(0)

namespace py = boost::python;
namespace np = boost::python::numpy;

inline py::list add_path_to_sys_path(const char* path) {
    py::object py_path;
    catch_py_error(py_path = py::import("sys"));
    catch_py_error(py_path = py_path.attr("path"));
    py::list sys_path = py::extract<py::list>(py_path);
    sys_path.append(path);
    return sys_path;
}
template<class T> inline 
std::ostream& py_list_to_string (std::ostream& strean, const py::list& py_list,const char* separator = "\n") {
    int list_count = len(py_list);
    auto print = [&](int offset, int size) {
        for (int i = 0; i < size; ++i) {
            py::object temp = py_list[offset + i];
            T& n = py::extract<T>(temp);
            strean << n << separator;
        }
    };
    if (list_count > 10) {
        print(0, 5);
        strean << "..." << separator;
        print(list_count - 6, 5);
    }
    else{
        print(0, list_count);
    }
    return strean;
}
struct pyobject_wrapper : public py::object {
    pyobject_wrapper() = default;
    explicit pyobject_wrapper(const py::object& obj) :py::object(obj){}
    inline pyobject_wrapper operator [](const char* key) const { return pyobject_wrapper(py::object::attr(key)); }
};

template<class TContainer> struct stl_container_converter {
    static PyObject* convert(const TContainer& vec) {
        py::list list;
        for (const auto& elem : vec) list.append(elem);
        return py::incref(list.ptr());
    }
    static void* convert_from_python(PyObject* obj) {
        void* p = std::malloc(sizeof(TContainer));
        TContainer& vec = *(new (p)TContainer());
        if (PyList_Check(obj) || PyTuple_Check(obj)) {
            py::handle<> handle(py::borrowed(obj));
            py::list list(handle);
            int n = len(list);
            vec.resize(n);// TODO : resize if T is vector
            for (int i = 0; i < n; i++) vec[i] = py::extract<typename TContainer::value_type>(list[i]);
        }
        return p;
    }
    static void register_converter() {
        py::to_python_converter<TContainer, stl_container_converter<TContainer>>();
        py::converter::registry::insert(
            &convert_from_python,
            py::type_id<TContainer>()
        );
    }
};
template<class T, class ...TRest> inline
void init_stl_converters() {
    stl_container_converter<T>::register_converter();
    if constexpr (sizeof...(TRest)) {
        init_stl_converters<TRest...>();
    }
}

struct py_loader final
{
    using module_map = std::map<std::string, pyobject_wrapper>;
    module_map modules;
    py_loader(const std::filesystem::path& path = "__main__"){
        reset_current(path);
    }
    void reset_current(const std::filesystem::path& path){
        modules.clear();
        append_import_to_current(path, modules);
    }
    void append_import_to_current(const std::filesystem::path& path, module_map& modules) const {
        namespace fs = std::filesystem;
        if (fs::is_directory(path)) {
            add_path_to_sys_path(path.c_str());
            for (const auto& entry : fs::directory_iterator(path)) {
                this->append_import_to_current(entry.path(), modules);
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
                if (obj.is_none()) throw std::range_error((std::ostringstream() << "import module failed in " << file).str());
                modules[file] = pyobject_wrapper(obj);
            );
        }
    }
    pyobject_wrapper operator[](const std::string& module_name) const {
        auto it = modules.find(module_name);
        if (modules.end() == it) throw std::range_error((std::ostringstream() << "can't find module " << module_name).str());
        return it->second;
    }
private:
    struct py_lifetime{
        bool is_py_running;
        py_lifetime(bool init = false) : is_py_running(init){
            if(!init) return;
            Py_Initialize();
            np::initialize();
        }
        ~py_lifetime(){
            if(!is_py_running) return;
            Py_Finalize();
        }
        void operator = (py_lifetime&& py) {
            std::swap(is_py_running, py.is_py_running);
        }
    };
    static py_lifetime& get_py_inter(){
        static py_lifetime py(false); 
        return py;
    };
public:
    static void init(){
        if(get_py_inter().is_py_running) return;
        get_py_inter() = py_lifetime(true);
        init_stl_converters<std::vector<int>>();
    }
    static void dispose(){
        get_py_inter() = py_lifetime(false);
    }
};

template<class T, class TAlloc> inline 
np::ndarray create_ndarray_from_vector(const std::vector<T, TAlloc>& data, std::vector<int> shape) {
    std::reverse(shape.begin(), shape.end());
    std::vector<int> strides(shape.size());
    strides.back() = sizeof(T);
    for (int i = shape.size() - 2; i >= 0; --i) {
        strides[i] = strides[i + 1] * shape[i + 1];
    }
    np::dtype dtype = np::dtype::get_builtin<T>();
    catch_py_error(np::ndarray ndarray = np::from_data(
        reinterpret_cast<const void*>(data.data()), dtype,
        py::tuple(py::list(shape)),
        py::tuple(py::list(strides)),
        py::object()
    );
    return ndarray;
        );
}

struct py_plot {
    static std::filesystem::path get_default_visualizer_dir()
    {
        std::filesystem::path current_path(__FILE__);
        auto s= current_path.parent_path();
        return "./";
    }
    py_loader loader;
    pyobject_wrapper visulizer;
    bool event_init = false;
    //std::function<void(double, double, double, double)>
    py_plot(std::filesystem::path path = get_default_visualizer_dir()) : loader(path) {
        visulizer = loader["visualizer"];
    }
    static bool& get_cancel_token() {
        static  bool cancel = false;
        return cancel;
    }
    static bool on_plot_close(py::object event) {
        printf("gui closing...\n");
        get_cancel_token() = true;
        return false;
    }
    static auto create_callback_simulation_fram_done(
        py::object callback_click = py::object(),
        py::object callback_motion = py::object()
    ) {
        auto callback_fram_display = [plot = py_plot(), callback_click, callback_motion](np::ndarray data) mutable {
            if (get_cancel_token()) return false;
            catch_py_error(plot.visulizer["update"](data));
            if (!plot.event_init) {
                catch_py_error(plot.visulizer["regist_on_close"](py_plot::on_plot_close));
                catch_py_error(auto func = plot.visulizer["regist_click_and_motion"](callback_click, callback_motion));
                plot.event_init = true;
            }
            return !get_cancel_token();
        };
        return callback_fram_display;
    }
};

inline void overload_click(int type, int flag, float dx, float dy) {
    const std::array<const char*, 4> btn_type{ "", "left", "mid", "right" };
    printf("%s  %s button at (%f, %f)\n", 0 == flag ? "press" : "release", btn_type.at(type), dx, dy);
}
