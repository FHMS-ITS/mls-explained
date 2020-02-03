import subprocess
import tempfile
from typing import Optional

from libMLS.session import Session
from libMLS.tree_math import parent
from libMLS.tree_node import TreeNode


def _node_to_dot(node: TreeNode, node_index: int) -> str:
    return f"\"Index: {node_index}\\npub: {node.get_public_key().hex() if node is not None else 'None'}\""


class DotDumper:

    def __init__(self, session: Session, group_name: Optional[str] = None):
        self._session = session
        self._img_dir = tempfile.mkdtemp(prefix=f"{f'{group_name}-' if group_name is not None else ''}mls-states")
        self._num_dumped = 0

    def dump_state_dot(self) -> str:
        dot_contents: str = "digraph mls{\n"

        tree = self._session.get_state().get_tree()
        nodes = tree.get_nodes()

        for index, node in enumerate(nodes):
            dot_contents += f"{_node_to_dot(node,index)}[style=filled fillcolor=transparent];\n"

            parent_node = parent(index, len(nodes)-1)

            if parent_node != index:
                dot_contents += f"\t{_node_to_dot(node, index)} -> {_node_to_dot(nodes[parent_node], parent_node)};\n"

        dot_contents += "}"
        return dot_contents

    def print_dot_state(self):
        print(self.dump_state_dot())

    def dump_dot_to_file(self, overwrite_path: Optional[str] = None):
        dot_source = self.dump_state_dot()

        if overwrite_path is None:
            overwrite_path = '/tmp/lastfile.svg'

        # pylint:disable=unexpected-keyword-arg
        svg_data = subprocess.check_output(['dot', '-Tsvg'], input=str.encode(dot_source))
        with open(overwrite_path, 'w') as tmp_file:
            tmp_file.write(svg_data.decode('utf-8'))

    def dump_next_state(self):

        path = self._img_dir + f'/state{str(self._num_dumped).rjust(3, "0")}'
        self.dump_dot_to_file(path)
