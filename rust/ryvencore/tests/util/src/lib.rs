use proc_macro::TokenStream;
use quote::quote;
use std::collections::{HashMap as Map, HashSet as Set};
use syn::parse::{Parse, ParseStream};

/*
    this macro turns something like this:

        NodeA.0.0 -> NodeB.1.0
        NodeB.1.0 -> NodeA.2.0

    into this:

        let mut flow: Flow<i32> = Flow::default();
        let node_id0 = flow.add_node(Box::new(NodeA::new())).unwrap();
        let node_id1 = flow.add_node(Box::new(NodeB::new())).unwrap();
        let node_id2 = flow.add_node(Box::new(NodeA::new())).unwrap();
        flow.connect((node_id, Direction::Out, 0), (node_id1, Direction::In, 0)).unwrap();
        flow.connect((node_id1, Direction::Out, 0), (node_id2, Direction::In, 0)).unwrap();

    whereas
    
        format: <node-type>.<instance>.<output> -> <node-type>.<instance>.<input>
*/

struct Graph {
    nodes: Map<String, Set<String>>,
    edges: Map<(String, String, usize), Set<(String, String, usize)>>,
}

impl Parse for Graph {
    fn parse(input: ParseStream) -> syn::Result<Self> {
        macro_rules! nxt {
            ($x:expr) => {
                $x.next().unwrap().trim()
            };
        }
        let mut nodes = Map::new();
        let mut edges = Map::new();
        
        let input_str = input.parse::<syn::LitStr>()?.value();
        let mut lines = input_str.lines().filter(|x| !x.trim().is_empty() && !x.trim().starts_with("#"));
        while let Some(input_str) = lines.next() {
            let mut parts = input_str.split("->");
            let mut from =      nxt!(parts).split(".");
            let mut to =        nxt!(parts).split(".");
            let from_ty =       nxt!(from);
            let to_ty =         nxt!(to);
            let from_inst =     nxt!(from);
            let to_inst =       nxt!(to);
            let from_out =      nxt!(from).parse::<usize>().unwrap();
            let to_in =         nxt!(to).parse::<usize>().unwrap();
            nodes.entry(from_ty.to_string()).or_insert(Set::new()).insert(from_inst.to_string());
            nodes.entry(to_ty.to_string()).or_insert(Set::new()).insert(to_inst.to_string());
            edges.entry((from_ty.to_string(), from_inst.to_string(), from_out)).or_insert(Set::new()).insert((to_ty.to_string(), to_inst.to_string(), to_in));
        }
        Ok(Graph { nodes, edges, })
    }
}

#[proc_macro]
pub fn generate_graph_tests(input: TokenStream) -> TokenStream {
    let graph = syn::parse_macro_input!(input as Graph);
    let mut code = String::new();
    code.push_str("let mut flow: Flow<i32> = Flow::default();\n");
    let mut node_ids = Map::new();
    for (ty, insts) in graph.nodes {
        for inst in insts {
            let node_name = format!("node_{}_{}", ty, inst);
            code.push_str(&format!("let {} = flow.add_node(Box::new({}::new())).unwrap();\n", node_name, ty));
            node_ids.insert((ty.clone(), inst.clone()), format!("{}", node_name));
        }
    }
    for ((from_ty, from_inst, from_out), tos) in graph.edges {
        for (to_ty, to_inst, to_in) in tos {
            code.push_str(&format!("flow.connect(({}, Direction::Out, {}), ({}, Direction::In, {})).unwrap();\n", node_ids[&(from_ty.clone(), from_inst.clone())], from_out, node_ids[&(to_ty.clone(), to_inst.clone())], to_in));
        }
    }
    code.parse().unwrap()
}