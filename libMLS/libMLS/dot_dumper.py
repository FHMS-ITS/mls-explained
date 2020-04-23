import subprocess
import tempfile
from typing import Optional

from libMLS.session import Session
from libMLS.tree_math import parent
from libMLS.tree_node import TreeNode


def _node_to_dot(node: Optional[TreeNode], node_index: int) -> str:
    return f"\"Index: {node_index}\\npub: {node.get_public_key().hex() if node is not None else 'Blank'}\""


def _node_to_style(node: Optional[TreeNode]) -> str:
    fillcolor = []

    if node is not None and node.has_private_key():
        fillcolor.append("silver")
    # if node is not None and is_leaf(node_index):
    #     fillcolor.append("lightgreen")

    if len(fillcolor) == 0:
        fillcolor = ["transparent"]

    return f"[style=filled fillcolor=\"{':'.join(fillcolor)}\"]"


class DotDumper:
    """
    This class is NOT part of the MLS protocol RFC, it is ONLY intendet for development purposes, a complete
    security sinkhole and highly pythonic.
    As with the rest of this MLS code, DO NOT USE THIS IN A PRODUCTION ENVIRONMENT
    See the CRAP-L Licence in the project root folder for more infos.
    """

    def __init__(self, session: Session, group_name: Optional[str] = None):
        self._session = session
        self._img_dir = tempfile.mkdtemp(prefix=f"{f'{group_name}-' if group_name is not None else ''}mls-states")
        self._num_dumped = 0

    def dump_state_dot(self) -> str:
        dot_contents: str = "digraph mls{\n"

        tree = self._session.get_state().get_tree()
        nodes = tree.get_nodes()
        num_leafs = tree.get_num_leaves()

        for index, node in enumerate(nodes):
            dot_contents += f"{_node_to_dot(node, index)}{_node_to_style(node)}\n"

            parent_node = parent(index, num_leafs)

            if parent_node != index and parent_node < len(nodes):
                dot_contents += f"\t{_node_to_dot(node, index)} -> {_node_to_dot(nodes[parent_node], parent_node)};\n"

        dot_contents += "}"
        return dot_contents

    def print_dot_state(self):
        print(self.dump_state_dot())

    def dump_dot_to_file(self, overwrite_path: Optional[str] = None) -> str:
        dot_source = self.dump_state_dot()

        if overwrite_path is None:
            overwrite_path = '/tmp/lastfile.svg'

        # pylint:disable=unexpected-keyword-arg
        try:
            svg_data = subprocess.check_output(['dot', '-Tsvg'], input=str.encode(dot_source))
        except Exception as exception:
            print(dot_source)
            raise exception


        with open(overwrite_path, 'w') as tmp_file:
            tmp_file.write(svg_data.decode('utf-8'))

        return overwrite_path

    def dump_next_state(self) -> str:
        path = self._img_dir + f'/state{str(self._num_dumped).rjust(3, "0")}.svg'
        self._num_dumped += 1

        return self.dump_dot_to_file(path)
