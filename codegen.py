from parser import Node, NodeType

class CodeGenerator:
    def generate(self, ast: Node) -> str:
        output = []
        
        for node in ast.children:
            # Handle #M_include nodes specifically if needed, e.g., pass them through
            if node.type == NodeType.INCLUDE:
                 # Assuming #M_include means pass the directive and path literally
                 #(charlie) yes it does. just replace the M_ with nothing and you got a masm include, oh and keep the # and quotes
                 # The path might still have quotes, strip them if needed by assembler
                #  output.append(f"{node.value['directive']} {node.value['path']}")
                output.append(f"#include {node.value['path']}")
            elif node.type == NodeType.FUNCTION:
                output.extend(self.generate_function(node))
            # Add handling for other top-level nodes if any are introduced later
        
        return '\n'.join(output)

    def generate_function(self, function_node: Node) -> List[str]:
        output = []
        indent_level = 1  # Track the current indentation level

        def indent_line(line: str) -> str:
            """Apply indentation to a line based on the current level."""
            return '    ' * indent_level + line

        # Generate function header (no indentation for labels)
        output.append(f"LBL {function_node.value}")

        # Generate function body
        for statement in function_node.children:
            if statement.type == NodeType.MOV:
                output.append(indent_line(f"MOV {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.DB:
                output.append(indent_line(f"DB ${statement.value['address']} {statement.value['string']}"))
            elif statement.type == NodeType.CALL:
                output.append(indent_line(f"CALL #{statement.value}"))
            elif statement.type == NodeType.HLT:
                # HLT should not be indented
                output.append(f"HLT")
            elif statement.type == NodeType.RET:
                # RET should not be indented
                output.append(f"RET")
            elif statement.type == NodeType.ADD:
                output.append(indent_line(f"ADD {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.SUB:
                output.append(indent_line(f"SUB {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.MUL:
                output.append(indent_line(f"MUL {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.DIV:
                output.append(indent_line(f"DIV {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.INC:
                output.append(indent_line(f"INC {statement.value}"))
            elif statement.type == NodeType.JMP:
                output.append(indent_line(f"JMP #{statement.value}"))
            elif statement.type == NodeType.CMP:
                output.append(indent_line(f"CMP {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.JE:
                output.append(indent_line(f"JE #{statement.value['true']} #{statement.value['false']}"))
            elif statement.type == NodeType.JNE:
                output.append(indent_line(f"JNE #{statement.value['true']} #{statement.value['false']}"))
            elif statement.type == NodeType.JL:
                output.append(indent_line(f"JL #{statement.value['true']} #{statement.value['false']}"))
            elif statement.type == NodeType.JG:
                output.append(indent_line(f"JG #{statement.value['true']} #{statement.value['false']}"))
            elif statement.type == NodeType.PUSH:
                output.append(indent_line(f"PUSH {statement.value}"))
            elif statement.type == NodeType.POP:
                output.append(indent_line(f"POP {statement.value}"))
            elif statement.type == NodeType.OUT:
                output.append(indent_line(f"OUT {statement.value['port']} {statement.value['value']}"))
            elif statement.type == NodeType.COUT:
                output.append(indent_line(f"COUT {statement.value['port']} {statement.value['value']}"))
            elif statement.type == NodeType.EXIT:
                output.append(indent_line(f"EXIT {statement.value}"))
            elif statement.type == NodeType.AND:
                output.append(indent_line(f"AND {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.OR:
                output.append(indent_line(f"OR {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.XOR:
                output.append(indent_line(f"XOR {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.NOT:
                output.append(indent_line(f"NOT {statement.value}"))
            elif statement.type == NodeType.SHL:
                output.append(indent_line(f"SHL {statement.value['dest']} {statement.value['src']}"))
            elif statement.type == NodeType.SHR:
                output.append(indent_line(f"SHR {statement.value['dest']} {statement.value['src']}"))

        # Add a newline after each function
        output.append("")

        return output