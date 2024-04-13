"""
The flow executors are responsible for executing the flow. They have access to
the flow as well as the nodes' internals and are able to perform optimizations.
"""
from . import Flow, Node
from .data.Data import Data
from .NodePort import NodeOutput, NodeInput
from .RC import FlowAlg


"""
graph_adjacency = {
    node_output: [node_input],    
    node_input:  node_output | None
}
"""


class FlowExecutor:
    """
    Base class for special flow execution algorithms.
    """

    def __init__(self, flow: Flow):
        self.flow = flow
        self.flow_changed = True
        self.graph = self.flow.graph_adj
        self.graph_rev = self.flow.graph_adj_rev

    # Node.update() =>
    def update_node(self, node: Node, inp: int):
        pass

    # Node.input() =>
    def input(self, node: Node, index: int):
        pass

    # Node.set_output_val() =>
    def set_output_val(self, node: Node, index: int, val: Data):
        pass

    # Node.exec_output() =>
    def exec_output(self, node: Node, index: int):
        pass

    def conn_added(self, out: NodeOutput, inp: NodeInput, silent=False):
        pass

    def conn_removed(self, out: NodeOutput, inp: NodeInput, silent=False):
        pass


class DataFlowNaive(FlowExecutor):
    """
    The naive implementation of data-flow execution. Naive meaning setting a node output
    leads to an immediate update in all successors consecutively. No runtime optimization
    if performed, and some types of graphs can run really slow here, especially if they
    include "diamonds".

    Assumptions for the graph:
    - no non-terminating feedback loops
    """

    # Node.update() =>
    def update_node(self, node: Node, inp: int):
        try:
            node.update_event(inp)
        except Exception as e:
            node.update_err(e)

    # Node.input() =>
    def input(self, node: Node, index: int):
        inp = node._inputs[index]
        conn_out = self.graph_rev[inp]

        if conn_out:
            return conn_out.val
        else:
            return inp.default

    # Node.set_output_val() =>
    def set_output_val(self, node: Node, index: int, data):
        out = node._outputs[index]
        if not out.type_ == 'data':
            return
        out.val = data

        for inp in self.graph[out]:
            inp.node.update(inp=inp.node._inputs.index(inp))

    # Node.exec_output() =>
    def exec_output(self, node: Node, index: int):
        out = node._outputs[index]
        if not out.type_ == 'exec':
            return

        for inp in self.graph[out]:
            inp.node.update(inp=inp.node._inputs.index(inp))

    def conn_added(self, out: NodeOutput, inp: NodeInput, silent=False):
        if not silent:
            # update input
            inp.node.update(inp=inp.node._inputs.index(inp))

    def conn_removed(self, out, inp, silent=False):
        if not silent:
            # update input
            inp.node.update(inp=inp.node._inputs.index(inp))


class DataFlowOptimized(DataFlowNaive):
    """
    *(see also documentation in Flow)*

    A special flow executor which implements some node functions to optimise flow execution.
    Whenever a new execution is invoked somewhere (some node or output is updated), it
    analyses the graph's connected component (of successors) where the execution was invoked
    and creates a few data structures to reverse engineer how many input
    updates every node possibly receives in this execution. A node's outputs are
    propagated once no input can still receive new data from a predecessor node.
    Therefore, while a node gets updated every time an input receives some data,
    every OUTPUT is only updated ONCE.
    This implies that every connection is activated at most once in an execution.
    This can result in asymptotic speedup in large data flows compared to normal data flow
    execution where any two executed branches which merge again in the future result in two
    complete executions of everything that comes after the merge, which quickly produces
    exponential performance issues.
    """

    def __init__(self, flow):
        super().__init__(flow)

        self.output_updated = {}
        self.waiting_count = {}
        self.node_waiting = {}
        self.num_conns_from_predecessors = None
        self.last_execution_root = None     # for reuse when a same execution is invoked many times consecutively
        self.execution_root = None          # can be Node or NodeOutput
        self.execution_root_node = None     # the updated Node or the updated NodeOutput's Node

    # NODE FUNCTIONS

    # Node.update() =>
    def update_node(self, node, inp=-1):
        if self.execution_root_node is None:  # execution starter!
            self.start_execution(root_node=node)
            self.invoke_node_update_event(node, inp)
            self.propagate_outputs(node)
            self.stop_execution()
        else:
            self.invoke_node_update_event(node, inp)

    # Node.input() =>
    #   DataFlowNative.input(node, index)

    # Node.set_output_val() =>
    def set_output_val(self, node, index, data):
        out = node._outputs[index]

        if self.execution_root_node is None:  # execution starter!
            self.start_execution(root_output=out)

            out.val = data
            self.output_updated[out] = True
            self.propagate_output(out)

            self.stop_execution()

        else:

            if not self.node_waiting[out.node]:
                # the output's node might not be part of the analyzed graph!
                # in this case we immediately push the value
                # there are other possible solutions to this, including running
                # a new execution analysis of this graph here

                super().set_output_val(node, index, data)

            else:
                out.val = data
                self.output_updated[out] = True

    # Node.exec_output() =>
    def exec_output(self, node, index):
        # rudimentary exec support also in data flows

        out = node._outputs[index]

        if self.execution_root_node is None:  # execution starter!
            self.start_execution(root_output=out)

            self.output_updated[out] = True
            self.propagate_output(out)

            self.stop_execution()

        else:
            self.output_updated[out] = True

    """
    
    Helper methods
    
    """

    def start_execution(self, root_node: Node = None, root_output: NodeOutput = None):

        # reset cached output values
        self.output_updated = {}
        for n in self.flow.nodes:
            for out in n._outputs:
                self.output_updated[out] = False

        if root_node is not None:
            self.execution_root = root_node
            self.execution_root_node = root_node
            self.waiting_count = self.generate_waiting_count(root_node=root_node)

        elif root_output is not None:
            self.execution_root = root_output
            self.execution_root_node = root_output.node
            self.waiting_count = self.generate_waiting_count(root_output=root_output)

    def stop_execution(self):
        self.execution_root_node = None
        self.last_execution_root = self.execution_root
        self.execution_root = None

    def generate_waiting_count(self, root_node=None, root_output=None):
        if not self.flow_changed and self.execution_root is self.last_execution_root:
            return self.num_conns_from_predecessors.copy()
        self.flow_changed = False

        nodes = self.flow.nodes
        node_successors = self.flow.node_successors

        # DP TABLE
        self.num_conns_from_predecessors = {
            n: 0
            for n in nodes
        }

        successors = set()
        visited = {
            n: False
            for n in nodes
        }

        # BC
        if root_node is not None:
            successors.add(root_node)

        elif root_output is not None:
            for inp in self.graph[root_output]:
                connected_node = inp.node
                self.num_conns_from_predecessors[connected_node] += 1
                successors.add(connected_node)

        # ITERATION
        while len(successors) > 0:
            n = successors.pop()
            if visited[n]:
                continue

            for s in node_successors[n]:
                self.num_conns_from_predecessors[s] += 1
                successors.add(s)
            visited[n] = True

        self.node_waiting = visited

        return self.num_conns_from_predecessors.copy()

    def invoke_node_update_event(self, node, inp):
        super().update_node(node, inp)

    def decrease_wait(self, node):
        """decreases the wait count of the node;
        if the count reaches zero, which means there is no other input waiting for data,
        the output values get propagated"""

        self.waiting_count[node] -= 1
        if self.waiting_count[node] == 0:
            self.propagate_outputs(node)

    def propagate_outputs(self, node: Node):
        """propagates all outputs of node"""

        for out in node._outputs:
            self.propagate_output(out)

    def propagate_output(self, out):
        """pushes an output's value to successors if it has been changed in the execution"""

        if self.output_updated[out]:
            # same procedure for data and exec connections
            for inp in self.graph[out]:
                inp.node.update(inp=inp.node._inputs.index(inp))

        # decrease wait count of successors
        for inp in self.graph[out]:
            self.decrease_wait(inp.node)


class ExecFlowNaive(FlowExecutor):
    """
    ...
    """

    def __init__(self, flow):
        super().__init__(flow)

        # all the nodes currently updating because of an output data request
        # used to prevent redundant predecessor updates during the update
        # of a single successor
        self.updated_nodes = None

    # Node.update() = >
    def update_node(self, node, inp):
        if inp != -1 and node._inputs[inp].type_ == 'data':
            return

        execution_starter = self.updated_nodes is None

        if execution_starter:
            self.updated_nodes = {node}
        else:
            self.updated_nodes.add(node)

        try:
            node.update_event(inp)
        except Exception as e:
            node.update_err(e)

        if execution_starter:
            self.updated_nodes = None

    # Node.input() =>
    def input(self, node, index):
        inp = node._inputs[index]
        out = self.graph_rev[inp]
        if out:
            n = out.node
            if n not in self.updated_nodes:
                n.update(-1)

            return out.val
        else:
            return None

    # Node.set_output_val() =>
    def set_output_val(self, node: Node, index: int, data: Data):
        out = node._outputs[index]
        out.val = data

    # Node.exec_output() =>
    def exec_output(self, node, index):
        for inp in self.graph[node._outputs[index]]:
            inp.node.update(inp.node._inputs.index(inp))


def executor_from_flow_alg(algorithm: FlowAlg):
    if algorithm == FlowAlg.DATA:
        return DataFlowNaive
    if algorithm == FlowAlg.DATA_OPT:
        return DataFlowOptimized
    if algorithm == FlowAlg.EXEC:
        return ExecFlowNaive
