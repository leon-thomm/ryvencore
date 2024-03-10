#include <cstdarg>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <ostream>
#include <new>


struct Node;

struct Flow {
  void *flow;
};

struct NodeId {
  int _0;
};

struct NodePortAlias {
  NodeId _0;
  bool _1;
  int _2;
};

struct NodeInvocationEnv {
  void *env;
};

struct TopoWithLoops {
  void *exec;
};


extern "C" {

int flow_add_node(Flow *flow, Node *node);

int flow_connect(Flow *flow, NodePortAlias from, NodePortAlias to);

Flow *flow_new();

const void *flow_output_val_of(const Flow *flow, int node_id, int port);

int flow_remove_node(Flow *flow, int node_id);

const void *node_invocation_env_get_inp(NodeInvocationEnv *env, int port);

int node_invocation_env_set_out(NodeInvocationEnv *env, int port, const void *val);

int topo_with_loops_invoke(TopoWithLoops *exec, Flow *flow, int node_id);

TopoWithLoops *topo_with_loops_new();

} // extern "C"
