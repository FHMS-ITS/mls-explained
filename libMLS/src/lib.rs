#[macro_use]
extern crate cpython;

use cpython::{Python, PyResult};

fn hello(_py: Python) -> PyResult<String> {
    Ok("Hello World".to_string())
}

py_module_initializer!(libmlslib, initlibmlslib, PyInit_mlslib, |py, m | {
    try!(m.add(py, "__doc__", "This module is implemented in Rust"));
    try!(m.add(py, "hello", py_fn!(py, hello())));
    Ok(())
});
