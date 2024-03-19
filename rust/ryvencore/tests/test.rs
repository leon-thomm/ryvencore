#[macro_use]
use util::generate_graph_tests;

use ryvencore::{
    *,
    flows::{*, executors::*},
    nodes::*,
};
use std::rc::Rc;

mod simple_echo {
    use super::*;

    pub struct SimpleEcho {
        id: NodeId,
    }

    impl SimpleEcho {
        pub fn new() -> Self {
            SimpleEcho {id: NodeId(0)}
        }
    }

    impl Node<i32> for SimpleEcho {
        fn init(&mut self, id: NodeId) {
            self.id = id;
        }
        fn init_inputs(&self) -> Vec<NodeInput> {
            vec![
                NodeInput {
                    label: "inp".to_string(),
                    port_type: NodePortType::Data,
                }
            ]
        }
        fn init_outputs(&self) -> Vec<NodeOutput<i32>> {
            vec![
                NodeOutput {
                    label: "out".to_string(),
                    port_type: NodePortType::Data,
                    val: None,
                }
            ]
        }
        fn on_placed(&mut self) {}
        fn on_removed(&mut self) {}
        fn on_rebuilt(&mut self) {}
        fn on_update(&mut self, env: &mut NodeInvocationEnv<i32>) -> RcRes<()> {
            println!("SimpleEcho::on_update");
            if let Some(inp) = env.get_inp(0)? {
                env.set_out(0, inp);
            } else {
                env.set_out(0, Rc::new(42));
            }
            Ok(())
        }
    }
}

mod min_max {
    use super::*;

    pub const LOW: i32 = 5;
    pub const HIGH: i32 = 100;

    pub struct MinMax {
        id: NodeId,
    }

    impl MinMax {
        pub fn new() -> Self {
            MinMax {id: NodeId(0)}
        }
    }

    impl Node<i32> for MinMax {
        fn init(&mut self, id: NodeId) {
            self.id = id;
        }
        fn init_inputs(&self) -> Vec<NodeInput> {
            vec![
                NodeInput {
                    label: "1".to_string(),
                    port_type: NodePortType::Data,
                },
                NodeInput {
                    label: "2".to_string(),
                    port_type: NodePortType::Data,
                }
            ]
        }
        fn init_outputs(&self) -> Vec<NodeOutput<i32>> {
            vec![
                NodeOutput {
                    label: "min".to_string(),
                    port_type: NodePortType::Data,
                    val: None,
                },
                NodeOutput {
                    label: "max".to_string(),
                    port_type: NodePortType::Data,
                    val: None,
                }
            ]
        }
        fn on_placed(&mut self) {}
        fn on_removed(&mut self) {}
        fn on_rebuilt(&mut self) {}
        fn on_update(&mut self, env: &mut NodeInvocationEnv<i32>) -> RcRes<()> {
            println!("MinMax::on_update");
            let a = env.get_inp(0)?;
            let b = env.get_inp(1)?;
            if a.is_some() || b.is_some() {
                let mut values = vec![];
                if a.is_some() { values.push(a.clone().unwrap()); }
                if b.is_some() { values.push(b.clone().unwrap()); }
                let min = values.iter().min().unwrap().clone();
                let max = values.iter().max().unwrap().clone();
                env.set_out(0, min);
                env.set_out(1, max);
            } else {
                env.set_out(0, Rc::new(LOW));
                env.set_out(1, Rc::new(HIGH));
            }
            Ok(())
        }
    }
}

mod ctr {
    use super::*;

    pub const THRESHOLD: i32 = 50;

    // will increment the input by 1 until it reaches a threshold
    pub struct Ctr {
        id: NodeId,
    }

    impl Ctr {
        pub fn new() -> Self {
            Ctr {id: NodeId(0)}
        }
    }

    impl Node<i32> for Ctr {
        fn init(&mut self, id: NodeId) {
            self.id = id;
        }
        fn init_inputs(&self) -> Vec<NodeInput> {
            vec![
                NodeInput {
                    label: "inp".to_string(),
                    port_type: NodePortType::Data,
                }
            ]
        }
        fn init_outputs(&self) -> Vec<NodeOutput<i32>> {
            vec![
                NodeOutput {
                    label: "out".to_string(),
                    port_type: NodePortType::Data,
                    val: None,
                }
            ]
        }
        fn on_placed(&mut self) {}
        fn on_removed(&mut self) {}
        fn on_rebuilt(&mut self) {}
        fn on_update(&mut self, env: &mut NodeInvocationEnv<i32>) -> RcRes<()> {
            println!("Ctr::on_update");
            if let Some(inp) = env.get_inp(0)? {
                if *inp < THRESHOLD {
                    env.set_out(0, Rc::new(*inp + 1));
                }
            }
            Ok(())
        }
    }
}

#[cfg(test)]
#[allow(non_snake_case)]
mod tests {
    use super::*;

    use simple_echo::SimpleEcho;
    use min_max::{MinMax, LOW, HIGH};
    use ctr::{Ctr, THRESHOLD};

    fn check_output(flow: &Flow<i32>, node: NodeId, output: usize, expected: i32) {
        let o = flow.output_val_of(node, output).unwrap();
        assert!(o.is_some());
        assert_eq!(*o.unwrap(), expected);
    }

    /*
        the format for the macro is
            <node-type>.<instance>.<output> -> <node-type>.<instance>.<input>
        where one such line declares an edge
    */

    #[test]
    fn basic() {
        generate_graph_tests!("
            SimpleEcho.0.0 -> SimpleEcho.1.0
            SimpleEcho.1.0 -> SimpleEcho.2.0
        ");

        // push 42 to the first node, should propagate through all
        let mut exc = TopoWithLoops::new();
        exc.invoke(&mut flow, node_SimpleEcho_0).unwrap();

        // push 100 to the third node
        flow.set_output_val_of(node_SimpleEcho_1, 0, Rc::new(100)).unwrap();
        let mut exc = TopoWithLoops::new();
        exc.invoke(&mut flow, node_SimpleEcho_2).unwrap();

        check_output(&flow, node_SimpleEcho_0, 0, 42);
        check_output(&flow, node_SimpleEcho_2, 0, 100);
    }

    #[test]
    fn min_max() {
        generate_graph_tests!("
            # only connect minimum
            MinMax.0.0 -> MinMax.1.0
            MinMax.0.0 -> MinMax.1.1

            # only connect maximum
            MinMax.0.1 -> MinMax.2.0
            MinMax.0.1 -> MinMax.2.1
            
            # connect both simple
            MinMax.0.1 -> MinMax.3.0
            MinMax.0.0 -> MinMax.3.1
            
            # connect both reversed
            MinMax.0.0 -> MinMax.4.1
            MinMax.0.1 -> MinMax.4.0
            
            # diamond
            MinMax.3.0 -> MinMax.5.0
            MinMax.4.1 -> MinMax.5.1
        ");

        let mut exc = TopoWithLoops::new();
        exc.invoke(&mut flow, node_MinMax_0).unwrap();

        check_output(&flow, node_MinMax_0, 0, LOW);
        check_output(&flow, node_MinMax_0, 1, HIGH);

        check_output(&flow, node_MinMax_1, 0, LOW);
        check_output(&flow, node_MinMax_1, 1, LOW);
        
        check_output(&flow, node_MinMax_2, 0, HIGH);
        check_output(&flow, node_MinMax_2, 1, HIGH);
        
        check_output(&flow, node_MinMax_3, 0, LOW);
        check_output(&flow, node_MinMax_3, 1, HIGH);
        
        check_output(&flow, node_MinMax_4, 0, LOW);
        check_output(&flow, node_MinMax_4, 1, HIGH);

        check_output(&flow, node_MinMax_5, 0, LOW);
        check_output(&flow, node_MinMax_5, 1, HIGH);
    }

    #[test]
    fn terminating_loop() {
        generate_graph_tests!("
            SimpleEcho.0.0 -> MinMax.0.0
            Ctr.0.0 -> MinMax.0.1
            MinMax.0.0 -> SimpleEcho.1.0
            SimpleEcho.1.0 -> MinMax.1.0
            MinMax.0.1 -> MinMax.1.1
            MinMax.1.1 -> Ctr.0.0
        ");

        let mut exc = TopoWithLoops::new();
        exc.invoke(&mut flow, node_SimpleEcho_0).unwrap();

        check_output(&flow, node_SimpleEcho_0, 0, 42);
        check_output(&flow, node_MinMax_0, 0, 42);
        check_output(&flow, node_MinMax_0, 1, THRESHOLD);
        check_output(&flow, node_SimpleEcho_1, 0, 42);
        check_output(&flow, node_MinMax_1, 0, 42);
        check_output(&flow, node_MinMax_1, 1, THRESHOLD);
        check_output(&flow, node_Ctr_0, 0, THRESHOLD);
    }

    #[test]
    fn basic_masking() {
        use flows::InputState::*;

        generate_graph_tests!("
            SimpleEcho.0.0 -> Ctr.0.0
            SimpleEcho.0.0 -> MinMax.0.0
            Ctr.0.0 -> MinMax.0.1
        ");

        let mut exc = TopoWithLoops::new();

        flow.mask_inputs(node_MinMax_0, vec![Inactive, Inactive]).unwrap();
        exc.invoke(&mut flow, node_SimpleEcho_0).unwrap();
        assert!(flow.output_val_of(node_MinMax_0, 0).unwrap().is_none());
        assert!(flow.output_val_of(node_MinMax_0, 1).unwrap().is_none());

        flow.mask_inputs(node_MinMax_0, vec![Active, Inactive]).unwrap();
        exc.invoke(&mut flow, node_Ctr_0).unwrap();
        assert!(flow.output_val_of(node_MinMax_0, 0).unwrap().is_none());
        assert!(flow.output_val_of(node_MinMax_0, 1).unwrap().is_none());

        flow.mask_inputs(node_MinMax_0, vec![Active, Active]).unwrap();
        exc.invoke(&mut flow, node_Ctr_0).unwrap();
        check_output(&flow, node_MinMax_0, 0, 42);
        check_output(&flow, node_MinMax_0, 1, 43);
    }
}