extern crate ryvencore;

macro_rules! check_non_null {
    ($x:expr, $ret:expr) => {
        if $x.is_null() {
            return $ret;
        }
    };
}

macro_rules! from_raw_mut {
    ($x:expr, $ret:expr) => {
        if $x.is_null() { return $ret; }
        else { unsafe { &mut *$x } }
    };
}

macro_rules! from_raw {
    ($x:expr, $ret:expr) => {
        if $x.is_null() { return $ret; }
        else { unsafe { &* $x } }
    };
}

/// C-compatible wrappers of ryevencore types.
mod export_wrappers {
    use std::ffi::{c_void, c_int, c_char};

    use ryvencore::*;
    
    use flows::Executor;

    #[repr(C)]
    pub struct NodeId(pub c_int);

    #[repr(C)]
    pub struct NodeInput {
        pub label: *const c_char,
    }

    #[repr(C)]
    pub struct NodeOutput {
        pub label: *const c_char,
    }

    #[repr(C)]
    pub struct NodePortAlias(pub NodeId, pub bool, pub c_int);

    #[repr(C)]
    pub struct NodeInvocationEnv {
        pub env: *mut c_void,   // points to a nodes::NodeInvocationEnv<c_void>
    }

    #[repr(C)]
    pub struct Flow {
        pub flow: *mut c_void,  // points to a flows::Flow<c_void>
    }

    #[repr(C)]
    pub struct TopoWithLoops {
        pub exec: *mut c_void,  // points to a flows::executors::TopoWithLoops
    }
}

/// ryvencore-compatible wrappers of C types.
mod import_wrappers {
    use std::ffi::{c_void, c_int, c_char};

    use ryvencore::*;
    
    use super::export_wrappers::{
        NodeInput,
        NodeOutput,
        NodeInvocationEnv,
        Flow,
        TopoWithLoops,
        NodeId,
    };

    #[repr(C)]
    pub struct Node {
        pub fn_init: extern "C" fn(&mut Node, NodeId),
        pub fn_init_inputs: extern "C" fn(&Node) -> (*const NodeInput, c_int),
        pub fn_init_outputs: extern "C" fn(&Node) -> (*const NodeOutput, c_int),
        pub fn_on_placed: extern "C" fn(&mut Node),
        pub fn_on_removed: extern "C" fn(&mut Node),
        pub fn_on_rebuilt: extern "C" fn(&mut Node),
        pub fn_on_update: extern "C" fn(&mut Node, &mut NodeInvocationEnv) -> c_int,
    }

    // TODO: This is currently not translated by cbindgen.
    //       Replace references by raw pointers?
    //       Also, tuples don't exist in C.

    /*
        something like

        struct Node {
            void (*fn_init)(*Node,NodeId);
            (*NodeInput,c_int) (*fn_init_inputs)(*Node);
            (*NodeOutput,c_int) (*fn_init_outputs)(*Node);
            void (*fn_on_placed)(*Node);
            void (*fn_on_removed)(*Node);
            void (*fn_on_rebuilt)(*Node);
            int (*fn_on_update)(*Node,NodeInvocationEnv);
        }
     */

    pub struct _NodeWrapper {
        pub node: Node,
    }
    
    impl nodes::Node<c_void> for _NodeWrapper {
        fn init(&mut self, id: nodes::NodeId) {
            let id = NodeId((id.0 as c_int).try_into().unwrap());
            (self.node.fn_init)(&mut self.node, id)
        }
        fn init_inputs(&self) -> Vec<nodes::NodeInput> {
            let (p, n) = (self.node.fn_init_inputs)(&self.node);
            let mut inputs: Vec<*const NodeInput> = Vec::new();
            for i in 0..(n as isize) {
                let x = unsafe { p.offset(i) };
                inputs.push(unsafe { x });
            }
            let mut res = Vec::new();
            for input in inputs {
                // convert from *const c_char to String
                let label = unsafe {
                    std::ffi::CStr::from_ptr((*input).label).to_str().unwrap()
                };
                res.push(nodes::NodeInput {
                    label: label.to_string(),
                    port_type: nodes::NodePortType::Data,
                });
            }
            res
        }
        fn init_outputs(&self) -> Vec<nodes::NodeOutput<c_void>> {
            let (p, n) = (self.node.fn_init_outputs)(&self.node);
            let mut outputs: Vec<*const NodeOutput> = Vec::new();
            for i in 0..(n as isize) {
                let x = unsafe { p.offset(i) };
                outputs.push(unsafe { x });
            }
            let mut res = Vec::new();
            for output in outputs {
                // convert from *const c_char to String
                let label = unsafe {
                    std::ffi::CStr::from_ptr((*output).label).to_str().unwrap()
                };
                res.push(nodes::NodeOutput {
                    label: label.to_string(),
                    port_type: nodes::NodePortType::Data,
                    val: None,
                });
            }
            res
        }
        fn on_placed(&mut self) {
            (self.node.fn_on_placed)(&mut self.node)
        }
        fn on_removed(&mut self) {
            (self.node.fn_on_removed)(&mut self.node)
        }
        fn on_rebuilt(&mut self) {
            (self.node.fn_on_rebuilt)(&mut self.node)
        }
        fn on_update(&mut self, env: &mut nodes::NodeInvocationEnv<c_void>) -> RcRes<()> {
            let p = env as *mut nodes::NodeInvocationEnv<c_void> as *mut c_void;
            let mut env = NodeInvocationEnv { env: p };
            match (self.node.fn_on_update)(&mut self.node, &mut env) {
                0 => Ok(()),
                _ => Err(RcErr::Err),
            }
        }
    }
}

/// The functional interface exposed to C.
mod api {
    use std::ffi::{c_void, c_int};
    use std::rc::Rc;
    use std::ptr::null;
    
    use ryvencore::*;
    use ryvencore::flows::Executor;

    use super::export_wrappers::{
        NodeInput,
        NodeOutput,
        NodeInvocationEnv,
        Flow,
        TopoWithLoops,
        NodeId,
        NodePortAlias,
    };
    use super::import_wrappers::{
        _NodeWrapper,
        Node,
    };

    macro_rules! extract_flow {
        ($x:expr) => {
            unsafe { Box::from_raw($x.flow as *mut flows::Flow<c_void>) }
        };
    }

    macro_rules! extract_env {
        ($x:expr) => {
            unsafe { Box::from_raw($x.env as *mut nodes::NodeInvocationEnv<c_void>) }
        };
    }

    macro_rules! extract_exec {
        ($x:expr) => {
            unsafe { Box::from_raw($x.exec as *mut flows::executors::TopoWithLoops) }
        };
    }

    #[no_mangle]
    pub extern "C" fn node_invocation_env_get_inp(env: *mut NodeInvocationEnv, port: c_int) -> *const c_void {
        let env = from_raw_mut!(env, null());
        match extract_env!(env).get_inp(port as usize) {
            Ok(Some(x)) => {
                let x = Box::new(x);
                Box::into_raw(x) as *const c_void
            }
            _ => std::ptr::null(),
        }
    }

    #[no_mangle]
    pub extern "C" fn node_invocation_env_set_out(env: *mut NodeInvocationEnv, port: c_int, val: *const c_void) -> c_int {
        check_non_null!(val, -1);
        let val = unsafe { Box::from_raw(val as *mut c_void) };
        let env = from_raw_mut!(env, -1);
        extract_env!(env).set_out(port as usize, Rc::new(*val));
        0
    }

    #[no_mangle]
    pub extern "C" fn flow_new() -> *mut Flow {
        let flow_instance: Box<flows::Flow<c_void>> = 
            Box::new(flows::Flow::default());
        let flow_ptr = Box::into_raw(flow_instance) as *mut c_void;
        Box::into_raw(Box::new(Flow { flow: flow_ptr }))
    }

    #[no_mangle]
    pub extern "C" fn flow_add_node(flow: *mut Flow, node: *mut Node) -> c_int {
        let flow = from_raw_mut!(flow, -1);
        check_non_null!(node, -1);
        let node = unsafe {
            // turn node into a _NodeWrapper
            Box::new(_NodeWrapper { 
                node: *Box::from_raw(node) 
            })
        };
        match extract_flow!(flow).add_node(node) {
            Ok(node_id) => node_id.0 as c_int,
            Err(_) => -1,
        }
    }

    #[no_mangle]
    pub extern "C" fn flow_remove_node(flow: *mut Flow, node_id: c_int) -> c_int {
        let flow = from_raw_mut!(flow, -1);
        match extract_flow!(flow).remove_node(nodes::NodeId(node_id as usize)) {
            Ok(_) => 0,
            Err(_) => -1,
        }
    }

    #[no_mangle]
    pub extern "C" fn flow_connect(flow: *mut Flow, from: NodePortAlias, to: NodePortAlias) -> c_int {
        let flow = from_raw_mut!(flow, -1);
        let from = (
            nodes::NodeId(from.0.0 as usize),
            match from.1 {
                false => flows::Direction::In,
                true => flows::Direction::Out,
            },
            from.2 as usize,
        );
        let to = (
            nodes::NodeId(to.0.0 as usize),
            match to.1 {
                false => flows::Direction::In,
                true => flows::Direction::Out,
            },
            to.2 as usize,
        );
        match extract_flow!(flow).connect(from, to) {
            Ok(_) => 0,
            Err(_) => -1,
        }
    }

    #[no_mangle]
    pub extern "C" fn flow_output_val_of(flow: *const Flow, node_id: c_int, port: c_int) -> *const c_void {
        let flow = from_raw!(flow, null());
        let res = extract_flow!(flow).output_val_of(nodes::NodeId(node_id as usize), port as usize);
        match res {
            Ok(Some(x)) => {
                let x = Box::new(x);
                Box::into_raw(x) as *const c_void
            }
            _ => std::ptr::null(),
        }
    }

    #[no_mangle]
    pub extern "C" fn topo_with_loops_new() -> *mut TopoWithLoops {
        let exec_instance: Box<flows::executors::TopoWithLoops> = 
            Box::new(flows::executors::TopoWithLoops::new());
        let exec_ptr = Box::into_raw(exec_instance) as *mut c_void;
        Box::into_raw(Box::new(TopoWithLoops { exec: exec_ptr }))
    }

    #[no_mangle]
    pub extern "C" fn topo_with_loops_invoke(exec: *mut TopoWithLoops, flow: *mut Flow, node_id: c_int) -> c_int {
        let exec = from_raw_mut!(exec, -1);
        let flow = from_raw_mut!(flow, -1);
        let mut _flow = extract_flow!(flow);
        match extract_exec!(exec).invoke(&mut _flow, nodes::NodeId(node_id as usize)) {
            Ok(_) => 0,
            Err(_) => -1,
        }
    }
}

use api::*;