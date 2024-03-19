//! A minimal nodes-based programming runtime, focusing on the following principles:
//! 
//! * **efficiency**: the runtime should implement highly efficient execution algorithms, using low-level tools to run fast
//! * **portability**: this runtime should allow for building node-based systems in a variety of environments
//! * **minimalism**: this runtime should be simple and small
//! * **correctness**: successful compilation should imply functionality
//! * **polymorphism**: ultimately, most sensible classes of use-cases of the node-based paradigm should be covered by simply providing appropriate configuration and node implementations
//! 
//! This crate exposes mainly
//! 
//! * the `Flow` struct, which is the main data structure for the runtime
//! * `Executor` implementations, which execute the flow by updating nodes and propagating data
//! * the `Node` trait, which must be implemented by nodes
//! 
//! A node is a unit of computation that has inputs and outputs.
//! If the node is connected to a predecessor node which pushed data to a connected output, the node is updated.
//! If the node pushes data to a connected output, successor nodes of the corresponding output will be updated.
//! Anything that implements the `Node` trait can be a node, and the runtime is generic over the type of data that is exchanged between nodes.
//! See the tests for examples.

use std::rc::Rc;
use std::collections::{
    HashMap as Map,
    HashSet as Set,
};

#[derive(Debug)]
pub enum RcErr {
    Err,
    InputAlreadyConnected,
    InvalidPort,
    PortsMissmatch,
    NodeNotFound,
}

pub type RcRes<T> = Result<T, RcErr>;

/// Turns an Option into a RcRes, returning the generic Err(RcErr::Err) if the Option is None.
/// Should gradually replace these with more specific errors.
macro_rules! expect {
    ($x:expr) => {
        match $x {
            Some(x) => x,
            None => return Err(RcErr::Err),
        }
    };
}

pub mod flows {
    use super::*;
    use super::nodes::*;

    /// The flow keeps nodes and their connections, and is responsible for executing the flow.
    /// by invoking a node.
    #[allow(dead_code)]
    pub struct Flow<T> {
        title: String,
        nodes: Map<NodeId, NodeInternal<T>>,
        port_succ: Map<NodePortAlias, Set<NodePortAlias>>,
        port_pred: Map<NodePortAlias, Option<NodePortAlias>>,
        // redundant data for faster access
        port_succ_masked: Map<NodePortAlias, Set<NodePortAlias>>,
        node_succ: Map<NodeId, Set<NodeId>>,
        node_pred: Map<NodeId, Set<NodeId>>,
    }

    impl<T> Default for Flow<T> {
        fn default() -> Self {
            Self {
                title: String::new(),
                nodes: Map::new(),
                port_succ: Map::new(),
                port_pred: Map::new(),
                port_succ_masked: Map::new(),
                node_succ: Map::new(),
                node_pred: Map::new(),
            }
        }
    }

    impl<T> Flow<T> {
        /// Adds a new node to the flow, and returns its id. Currently, this never fails.
        pub fn add_node(&mut self, mut node: Box<dyn Node<T>>) -> RcRes<NodeId> {
            let id = NodeId(self.nodes.len());
            node.init(id);
            let node_internal = NodeInternal { 
                id: id.clone(), 
                inputs: node.init_inputs().into_iter().map(|i| (i, InputState::Active)).collect(),
                outputs: node.init_outputs(),
                node,
            };
            self.node_succ.insert(id, Set::new());
            self.node_pred.insert(id, Set::new());
            node_internal.iter_out().for_each(|o| {
                self.port_succ.insert(o, Set::new());
                self.port_succ_masked.insert(o, Set::new());
            });
            node_internal.iter_inp().for_each(|i| {
                self.port_pred.insert(i, None);
            });
            self.nodes.insert(id.clone(), node_internal);
            Ok(id)
        }
        fn _clear_inp_conns(&mut self, node_id: NodeId) -> RcRes<()> {
            let node_internal = expect!(self.nodes.get(&node_id));
            // run over all inputs and disconnect them if they are connected
            node_internal.iter_inp().try_for_each(|inp| -> RcRes<()> {
                if let Some(out) = expect!(self.port_pred.get(&inp)) {
                    self.disconnect(*out, inp)?
                }
                Ok(())
            })?;
            Ok(())
        }
        fn _clear_out_conns(&mut self, node_id: NodeId) -> RcRes<()> {
            let node_internal = expect!(self.nodes.get(&node_id));
            // run over all outputs and remove all their connections
            node_internal.iter_out().try_for_each(|out| -> RcRes<()> {
                let succs = expect!(self.port_succ.get(&out))
                    .clone();   // avoid borrowing self.port_succ
                succs.iter().try_for_each(|inp| -> RcRes<()> {
                    self.disconnect(out, *inp)?;
                    Ok(())
                })?;
                Ok(())
            })?;
            Ok(())
        }
        /// Removes a node from the flow. If the node has connections, they are removed as well.
        pub fn remove_node(&mut self, node_id: NodeId) -> RcRes<()> {
            self._clear_inp_conns(node_id)?;
            self._clear_out_conns(node_id)?;
            self.nodes.remove(&node_id);
            Ok(())
        }
        /// Connects two ports. This function fails if
        /// * the `from` port is not a valid node output
        /// * the `to` port is not a valid node input
        /// * the `to` port is already connected
        pub fn connect(&mut self, from: NodePortAlias, to: NodePortAlias) -> RcRes<()> {
            let (fr_nid, fr_dir, fr_prt) = from;
            let (to_nid, to_dir, to_prt) = to;
            let fr_node = expect!(self.nodes.get(&fr_nid));
            let to_node = expect!(self.nodes.get(&to_nid));
            // sanity checks
            if !self.port_succ.contains_key(&from) || !self.port_pred.contains_key(&to) || fr_dir == to_dir {
                return Err(RcErr::InvalidPort);
            }
            if fr_prt >= fr_node.outputs.len() || to_prt >= to_node.inputs.len() {
                return Err(RcErr::InvalidPort);
            }
            if expect!(self.port_pred.get(&to)).is_some() {
                return Err(RcErr::InputAlreadyConnected);
            }
            // connect
            expect!(self.port_succ.get_mut(&from)).insert(to);
            if self.nodes[&to_nid].inputs[to_prt].1 == InputState::Active {
                expect!(self.port_succ_masked.get_mut(&from)).insert(to);
            }
            self.port_pred.insert(to, Some(from));
            expect!(self.node_succ.get_mut(&fr_nid)).insert(to_nid);
            expect!(self.node_pred.get_mut(&to_nid)).insert(fr_nid);
            Ok(())
        }
        /// Disconnects two ports. This function fails if
        /// * the `from` port is not a valid node output
        /// * the `to` port is not a valid node input
        /// * the ports are not connected
        pub fn disconnect(&mut self, from: NodePortAlias, to: NodePortAlias) -> RcRes<()> {
            if !self.port_succ.contains_key(&from) || !self.port_pred.contains_key(&to) {
                return Err(RcErr::InvalidPort);
            }
            expect!(self.port_succ.get_mut(&from))
                .remove(&to);
            expect!(self.port_succ_masked.get_mut(&from))
                .remove(&to);
            self.port_pred.insert(to, None);
            let (fr_nid, _, _) = from;
            let (to_nid, _, _) = to;
            expect!(self.node_succ.get_mut(&fr_nid)).remove(&to_nid);
            expect!(self.node_pred.get_mut(&to_nid)).remove(&fr_nid);
            Ok(())
        }
        pub fn output_val_of(&self, node_id: NodeId, port: usize) -> RcRes<Option<Rc<T>>> {
            Ok(self.nodes
                .get(&node_id).ok_or(RcErr::NodeNotFound)?
                .outputs.get(port).ok_or(RcErr::InvalidPort)?
                .get_val())
        }
        pub fn set_output_val_of(&mut self, node_id: NodeId, port: usize, val: Rc<T>) -> RcRes<()> {
            let node = self.nodes.get_mut(&node_id).ok_or(RcErr::NodeNotFound)?;
            node.outputs[port].set_val(val);
            Ok(())
        }
        /// Returns a the value of the connected output port, if the input is connected.
        /// Returns None if the input is not connected.
        /// Returns an error if the input port is invalid.
        pub fn input_val_of(&self, node_id: NodeId, port: usize) -> RcRes<Option<Rc<T>>> {
            let inp_alias = (node_id, Direction::In, port);
            let out = self.port_pred.get(&inp_alias).ok_or(RcErr::InvalidPort)?;
            if let Some(out) = out {
                let (out_nid, _, out_prt) = out;
                Ok(self.output_val_of(*out_nid, *out_prt)?)
            } else {
                Ok(None)
            }
        }
        /// Returns the the input values of a node, in the order of the inputs.
        pub fn input_values_of(&self, node_id: NodeId) -> RcRes<Vec<Option<Rc<T>>>> {
            let node = self.nodes.get(&node_id).ok_or(RcErr::NodeNotFound)?;
            Ok(node.inputs.iter().enumerate().map(
                |(i, _)| self.input_val_of(node_id, i).unwrap()
            ).collect())
        }
        /// Updates a node, given its id and the environment.
        pub fn update_node(&mut self, node_id: NodeId, env: &mut NodeInvocationEnv<T>) -> RcRes<()> {
            let node = expect!(self.nodes.get_mut(&node_id));
            node.node.on_update(env)
        }
        /// Returns the ids of the direct predecessor nodes of a given node.
        pub fn succ_nodes(&self, node_id: NodeId) -> RcRes<Set<NodeId>> {
            Ok(self.node_succ.get(&node_id)
                .ok_or(RcErr::NodeNotFound)?
                .clone()
            )
        }
        /// Returns the ids of the direct predecessor nodes of a given node.
        pub fn pred_nodes(&self, node_id: NodeId) -> RcRes<Set<NodeId>> {
            Ok(self.node_pred.get(&node_id)
                .ok_or(RcErr::NodeNotFound)?
                .clone()
            )
        }
        /// Returns the ids of the direct successor nodes of a given output port.
        /// Returns an error if the port doesn't exist or isn't an output port.
        pub fn succ_nodes_of_port(&self, port: NodePortAlias, consider_masking: bool) -> RcRes<Vec<NodeId>> {
            let (_, dir, _) = &port;
            if dir == &Direction::In {
                return Err(RcErr::InvalidPort);
            }
            Ok( {if consider_masking { &self.port_succ_masked } else { &self.port_succ } }
                .get(&port).ok_or(RcErr::InvalidPort)?
                .iter().map(|(n, _, _)| n.clone())
                .collect()
            )
        }
        /// Returns the ids of the direct successor nodes of a given set of output ports.
        /// Returns an error if any of the ports doesn't exist or isn't an output port.
        pub fn succ_nodes_of_ports(&self, ports: Set<NodePortAlias>, consider_masking: bool) -> RcRes<Vec<NodeId>> {
            let mut res = Vec::new();
            for p in ports {
                res.extend(self.succ_nodes_of_port(p, consider_masking)?);
            }
            Ok(res)
        }
        /// Masks the inputs of a node. Deactivated inputs won't trigger node updates
        /// on data arrivals during execution.
        /// Files if the node doesn't exist or the mask doesn't match the number of inputs.
        pub fn mask_inputs(&mut self, node_id: NodeId, mask: Vec<InputState>) -> RcRes<()> {
            let node = self.nodes.get_mut(&node_id).ok_or(RcErr::NodeNotFound)?;
            if mask.len() != node.inputs.len() {
                return Err(RcErr::PortsMissmatch);
            }
            for (i, m) in mask.iter().enumerate() {
                node.inputs[i].1 = *m;
                // update masked connections
                let inp_alias = (node_id, Direction::In, i);
                if let Some(out) = expect!(self.port_pred.get(&inp_alias)) {
                    let (out_nid, _, out_prt) = out;
                    if m == &InputState::Inactive {
                        self.port_succ_masked.get_mut(&(*out_nid, Direction::Out, *out_prt))
                            .ok_or(RcErr::InvalidPort)?
                            .remove(&inp_alias);
                    } else {
                        let (out_nid, _, out_prt) = out;
                        self.port_succ_masked.get_mut(&(*out_nid, Direction::Out, *out_prt))
                            .ok_or(RcErr::InvalidPort)?
                            .insert(inp_alias);
                    }
                }
            }
            Ok(())
        }
    }

    #[derive(Clone, Copy, PartialEq, Eq, Hash)]
    pub enum Direction {
        In,
        Out,
    }

    pub type NodePortAlias = (NodeId, Direction, usize);

    // type InputActive = bool;
    #[derive(Clone, Copy, PartialEq, Eq)]
    pub enum InputState {
        Active,
        Inactive,
    }

    struct NodeInternal<T> {
        id: NodeId,
        node: Box<dyn Node<T>>,
        inputs: Vec<(NodeInput, InputState)>,
        outputs: Vec<NodeOutput<T>>,
    }

    impl<T> NodeInternal<T> {
        fn iter_inp(&self) -> impl Iterator<Item = NodePortAlias> {
            let id = self.id.clone();
            (0..self.inputs.len()).map(move |i| (id.clone(), Direction::In, i))
        }
        fn iter_out(&self) -> impl Iterator<Item = NodePortAlias> {
            let id = self.id.clone();
            (0..self.outputs.len()).map(move |i| (id.clone(), Direction::Out, i))
        }
    }

    pub trait Executor<T> {
        fn invoke(&mut self, flow: &mut Flow<T>, n: NodeId) -> RcRes<()>;
    }

    pub mod executors {
        use super::*;

        pub struct TopoWithLoops {}

        impl TopoWithLoops {
            pub fn new() -> Self {
                Self {}
            }
        }

        #[allow(non_snake_case)]
        impl TopoWithLoops {
            /// Returns the nodes that can be reached in the flow from any node
            /// in I, in topological order, ignoring back edges (i.e. loops).
            fn topo<T>(&self, I: &Set<NodeId>, flow: &Flow<T>) -> RcRes<Vec<NodeId>> {
                // DFS-based
                let mut done = Set::new();
                let mut curr = Set::new();
                let mut res = Vec::new();
                let mut I = I.clone();
                while !I.is_empty() {
                    // remove node from I and visit
                    let n = I.iter().next().unwrap().clone();
                    I.remove(&n);
                    self.visit(n, &mut done, &mut curr, &mut res, flow)?;
                }
                res.reverse();
                Ok(res)
            }
            fn visit<T>(
                &self,
                n: NodeId,
                done: &mut Set<NodeId>,
                curr: &mut Set<NodeId>,
                res: &mut Vec<NodeId>,
                flow: &Flow<T>,
            ) -> RcRes<()> {
                if done.contains(&n) {  return Ok(());  }
                if curr.contains(&n) {  return Ok(());  }   // back edge; ignore
                curr.insert(n.clone());
                for succ in flow.succ_nodes(n)? {
                    self.visit(succ, done, curr, res, flow)?;
                }
                curr.remove(&n);
                done.insert(n.clone());
                res.push(n);
                Ok(())
            }
            /// Returns successor nodes of n who received data from one of n's outputs
            /// during the last invocation of n, according to env.
            fn successor_nodes<T>(&self, flow: &Flow<T>, n: &NodeId, env: &NodeInvocationEnv<T>) -> RcRes<Set<NodeId>> {
                let mut res = Set::new();
                for (i, _) in env.get_updates() {
                    res.extend(
                        flow.succ_nodes_of_port((*n, Direction::Out, *i), true)?
                    );
                }
                Ok(res)
            }
        }

        impl<T> Executor<T> for TopoWithLoops {
            /// * Starts an execution by updating nodes, beginning with n.
            /// * If a node pushes output data during update, all successor nodes of 
            /// the corresponding output will eventually be updated during the execution.
            /// * If no predecessor of a node has pushed data, the node will not be updated.
            /// * Nodes shall not make any assumptions about the order of node updates, 
            /// other than what is implied by any topological order.
            /// * Back-edges (i.e. loops) are respected and also lead to new invocations
            /// with minimal node update redundancy.
            /// * It is up to the user to ensure that an invocation in a cyclic graph will 
            /// terminate.
            fn invoke(&mut self, flow: &mut Flow<T>, n: NodeId) -> RcRes<()> {
                let mut q = OrderedMaskedQueue::new();
                q.enqueue(n);
                while !q.is_empty() {
                    q.set_mask(self.topo(&q.queued, flow)?);
                    while let Some(n) = q.dequeue() {
                        // update node
                        let mut env = NodeInvocationEnv::new(flow.input_values_of(n)?);
                        flow.update_node(n, &mut env)?;
                        // udpate queue
                        self.successor_nodes(&flow, &n, &env)?
                            .iter().for_each(|x| q.enqueue(*x));
                        // store updated output values
                        for (i, val) in env.get_updates() {
                            flow.set_output_val_of(n, *i, val.clone())?;
                        }
                    }
                }
                Ok(())
            }
        }

        /// Implements a queue of nodes where a separate set masks and
        /// orders the nodes that are queued.
        struct OrderedMaskedQueue<T>
        where
            T: Clone + PartialEq + Eq + std::hash::Hash,
        {
            mask: Vec<T>,
            queued: Set<T>,
        }

        impl<T> OrderedMaskedQueue<T>
        where
            T: Clone + PartialEq + Eq + std::hash::Hash,
         {
            fn new() -> Self {
                Self {
                    mask: Vec::new(),
                    queued: Set::new(),
                }
            }
            fn enqueue(&mut self, n: T) {
                self.queued.insert(n);
            }
            /// Return the first element in `mask` that is also in
            /// `queued`, and remove it from `queued`.
            /// If no such element exists, return None.
            fn dequeue(&mut self) -> Option<T> {
                if let Some(x) = self.mask.iter().find(|x| self.queued.contains(x)) {
                    self.queued.remove(x);
                    return Some(x.clone());
                }
                None
            }
            fn is_empty(&self) -> bool {
                self.queued.is_empty()
            }
            fn set_mask(&mut self, allowed: Vec<T>) {
                self.mask = allowed;
            }
        }
    }
}

pub mod nodes {
    use super::*;

    #[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
    pub struct NodeId(pub usize);

    #[derive(Clone, Copy, PartialEq, Eq, Hash)]
    pub enum NodePortType {
        Data,
    }

    pub struct NodeOutput<T> {
        pub label: String,
        pub port_type: NodePortType,
        pub val: Option<Rc<T>>,
    }

    impl<T> NodeOutput<T> {
        pub fn set_val(&mut self, val: Rc<T>) {
            self.val = Some(val);
        }
        pub fn get_val(&self) -> Option<Rc<T>> {
            self.val.clone()
        }
    }

    pub struct NodeInput {
        pub label: String,
        pub port_type: NodePortType,
    }

    pub struct NodeInvocationEnv<T> {
        input_data: Vec<Option<Rc<T>>>,
        output_updates: Map<usize, Rc<T>>,
    }

    impl<'a, T> NodeInvocationEnv<T> {
        pub fn new(input_data: Vec<Option<Rc<T>>>) -> Self {
            Self {
                input_data,
                output_updates: Map::new(),
            }
        }
        pub fn get_inp(&self,port: usize) -> RcRes<Option<Rc<T>>> {
            Ok(
                self.input_data.get(port)
                    .ok_or(RcErr::InvalidPort)?
                    .clone()
            )
        }
        pub fn set_out(&mut self, port: usize, data: Rc<T>) {
            self.output_updates.insert(port, data);
        }
        pub fn get_updates(&self) -> &Map<usize, Rc<T>> {
            &self.output_updates
        }
    }

    pub trait Node<T> {
        fn init(&mut self, id: NodeId);
        fn init_inputs(&self) -> Vec<NodeInput>;
        fn init_outputs(&self) -> Vec<NodeOutput<T>>;

        fn on_placed(&mut self);
        fn on_removed(&mut self);
        fn on_rebuilt(&mut self);
        fn on_update(&mut self, env: &mut NodeInvocationEnv<T>) -> RcRes<()>;
    }
}