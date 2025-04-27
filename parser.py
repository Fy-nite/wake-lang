from enum import Enum, auto
from typing import List, Optional, Union, Dict, Any
from lexer import Token, TokenType

class NodeType(Enum):
    PROGRAM = auto()
    INCLUDE = auto()
    FUNCTION = auto()
    MOV = auto()
    DB = auto()
    CALL = auto()
    HLT = auto()
    RET = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    INC = auto()
    JMP = auto()
    CMP = auto()
    JE = auto()
    JNE = auto()
    JL = auto()
    JG = auto()
    PUSH = auto()
    POP = auto()
    OUT = auto()
    COUT = auto()
    EXIT = auto()
    AND = auto()
    OR = auto()
    XOR = auto()
    NOT = auto()
    SHL = auto()
    SHR = auto()

class Node:
    def __init__(self, type: NodeType, value: Optional[Union[str, Dict[str, Any]]] = None):
        self.type = type
        self.value = value
        self.children: List[Node] = []

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Node:
        program = Node(NodeType.PROGRAM)
        
        while not self.is_at_end():
            node = None # Initialize node for this iteration
            if self.check(TokenType.INCLUDE):
                 # Advance past the INCLUDE token before calling parse_include
                self.advance() 
                node = self.parse_include()
            elif self.match(TokenType.FUNCTION):
                node = self.parse_function()
            else:
                # Skip unrecognized tokens or handle errors
                token = self.peek()
                # Avoid infinite loop on unexpected token at EOF
                if token.type != TokenType.EOF:
                     print(f"Warning: Skipping unexpected token '{token.value}' ({token.type}) at line {token.line} in {token.source_file}")
                     self.advance()
                else:
                     break # Stop if only EOF is left

            # Add the parsed node to the program if it's not None
            if node:
                program.children.append(node)
        
        return program
        
    # Add missing helper methods
    def is_at_end(self) -> bool:
        """Check if we've reached the end of the token list."""
        return self.peek().type == TokenType.EOF
        
    def match(self, *types) -> bool:
        """Match the current token against one or more types."""
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False
        
    def check(self, type: TokenType) -> bool:
        """Check if the current token is of the specified type."""
        if self.is_at_end():
            return False
        return self.peek().type == type
        
    def advance(self) -> Token:
        """Advance to the next token and return the previous one."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()
        
    def peek(self) -> Token:
        """Return the current token without advancing."""
        return self.tokens[self.current]
        
    def previous(self) -> Token:
        """Return the previous token."""
        return self.tokens[self.current - 1]
        
    def consume(self, type: TokenType, message: str) -> Token:
        """Consume the current token if it matches the expected type, otherwise raise an error."""
        if self.check(type):
            return self.advance()
        
        current_token = self.peek()
        source_text = self._get_line_context(current_token.line, current_token.source_file)
        error_msg = f"{message} at line {current_token.line} in {current_token.source_file}\n{source_text}"
        raise SyntaxError(error_msg)
    
    def _get_line_context(self, line_num: int, source_file: str) -> str:
        """Get the content of the line for better error reporting."""
        try:
            if source_file:
                with open(source_file, 'r') as file:
                    lines = file.readlines()
                    if 1 <= line_num <= len(lines):
                        line = lines[line_num - 1].rstrip()
                        pointer = ' ' * (len(line) - len(line.lstrip())) + '^'
                        return f"Line {line_num}: {line}\n{pointer}"
            return ""
        except:
            return ""

    def parse_include(self) -> Node:
        # Get the include token (#M_include or #include)
        include_token = self.previous()
        # Expect a string token immediately after
        path_token = self.consume(TokenType.STRING, f"Expected string path after '{include_token.value}'")
        
        # Only create Include nodes for #M_include, as #include content is already merged
        if include_token.value == '#M_include':
             # Store both the directive and the path, maybe useful later
            return Node(NodeType.INCLUDE, value={'directive': include_token.value, 'path': path_token.value})
        else:
            # For regular #include, the tokens are already in the stream,
            # so we don't need a specific node. We just consumed the tokens.
            # Return None or a special marker if needed, but skipping seems fine.
            # However, the current parse loop expects a node. Let's return a dummy node
            # or adjust the main parse loop. For now, let's skip adding it to the AST.
            # We need to adjust the main parse loop in parse()
            return None # Indicate no node should be added for #include

    def parse_function(self) -> Node:
        # Parse function name
        if not self.match(TokenType.IDENTIFIER):
            raise SyntaxError(f"Expected function name at line {self.peek().line}")
        
        function_name = self.previous().value
        
        # Parse function parameters (currently only empty parameters supported)
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after function name")
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters")
        
        # Parse function body
        self.consume(TokenType.LEFT_BRACE, "Expected '{' before function body")
        
        function_node = Node(NodeType.FUNCTION, value=function_name)
        
        # Parse function statements
        while not self.check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            # Skip any semicolons between statements
            while self.match(TokenType.SEMICOLON):
                pass
                
            if self.match(TokenType.IDENTIFIER):
                identifier = self.previous().value
                
                if identifier == "mov":
                    function_node.children.append(self.parse_mov_statement())
                elif identifier == "db":
                    function_node.children.append(self.parse_db_statement())
                elif identifier == "call":
                    function_node.children.append(self.parse_call_statement())
                elif identifier == "hlt":
                    function_node.children.append(self.parse_hlt_statement())
                elif identifier == "ret":
                    function_node.children.append(self.parse_ret_statement())
                # New instruction parsing
                elif identifier == "add":
                    function_node.children.append(self.parse_binary_instruction(NodeType.ADD))
                elif identifier == "sub":
                    function_node.children.append(self.parse_binary_instruction(NodeType.SUB))
                elif identifier == "mul":
                    function_node.children.append(self.parse_binary_instruction(NodeType.MUL))
                elif identifier == "div":
                    function_node.children.append(self.parse_binary_instruction(NodeType.DIV))
                elif identifier == "inc":
                    function_node.children.append(self.parse_unary_instruction(NodeType.INC))
                elif identifier == "jmp":
                    function_node.children.append(self.parse_jump_instruction(NodeType.JMP))
                elif identifier == "cmp":
                    function_node.children.append(self.parse_binary_instruction(NodeType.CMP))
                elif identifier == "je":
                    function_node.children.append(self.parse_conditional_jump_instruction(NodeType.JE))
                elif identifier == "jne":
                    function_node.children.append(self.parse_conditional_jump_instruction(NodeType.JNE))
                elif identifier == "jl":
                    function_node.children.append(self.parse_conditional_jump_instruction(NodeType.JL))
                elif identifier == "jg":
                    function_node.children.append(self.parse_conditional_jump_instruction(NodeType.JG))
                elif identifier == "push":
                    function_node.children.append(self.parse_unary_instruction(NodeType.PUSH))
                elif identifier == "pop":
                    function_node.children.append(self.parse_unary_instruction(NodeType.POP))
                elif identifier == "out":
                    function_node.children.append(self.parse_out_instruction(NodeType.OUT))
                elif identifier == "cout":
                    function_node.children.append(self.parse_out_instruction(NodeType.COUT))
                elif identifier == "exit":
                    function_node.children.append(self.parse_unary_instruction(NodeType.EXIT))
                elif identifier == "and":
                    function_node.children.append(self.parse_binary_instruction(NodeType.AND))
                elif identifier == "or":
                    function_node.children.append(self.parse_binary_instruction(NodeType.OR))
                elif identifier == "xor":
                    function_node.children.append(self.parse_binary_instruction(NodeType.XOR))
                elif identifier == "not":
                    function_node.children.append(self.parse_unary_instruction(NodeType.NOT))
                elif identifier == "shl":
                    function_node.children.append(self.parse_binary_instruction(NodeType.SHL))
                elif identifier == "shr":
                    function_node.children.append(self.parse_binary_instruction(NodeType.SHR))
                else:
                    token = self.previous()
                    line_info = f"at line {token.line} in {token.source_file}"
                    raise SyntaxError(f"Unexpected identifier '{identifier}' {line_info}")
            else:
                self.advance()  # Skip unrecognized tokens
            
            # Skip any semicolons after statements
            while self.match(TokenType.SEMICOLON):
                pass
        
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' after function body")
        
        return function_node

    def parse_mov_statement(self) -> Node:
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'mov'")
        
        if not self.match(TokenType.IDENTIFIER) and not self.match(TokenType.NUMBER):
            raise SyntaxError(f"Expected destination at line {self.peek().line}")
        
        dest = self.previous().value
        
        self.consume(TokenType.COMMA, "Expected ',' between arguments")
        
        if not self.match(TokenType.IDENTIFIER) and not self.match(TokenType.NUMBER):
            raise SyntaxError(f"Expected source at line {self.peek().line}")
        
        src = self.previous().value
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(NodeType.MOV, value={"dest": dest, "src": src})

    def parse_db_statement(self) -> Node:
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'db'")
        
        # Handle $ prefix in addresses
        if not self.match(TokenType.IDENTIFIER):
            raise SyntaxError(f"Expected address at line {self.peek().line}")
        
        address_token = self.previous().value
        
        # Make sure it starts with $
        if not address_token.startswith('$'):
            raise SyntaxError(f"Address in db statement must start with $ at line {self.peek().line}")
        
        # Extract the numeric part after $
        address = address_token[1:] if len(address_token) > 1 else ""
        
        self.consume(TokenType.COMMA, "Expected ',' between arguments")
        
        if not self.match(TokenType.STRING):
            raise SyntaxError(f"Expected string at line {self.peek().line}")
        
        string = self.previous().value
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(NodeType.DB, value={"address": address, "string": string})

    def parse_call_statement(self) -> Node:
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'call'")
        
        if not self.match(TokenType.STRING):
            raise SyntaxError(f"Expected function name at line {self.peek().line}")
        
        function_name = self.previous().value
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after function name")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(NodeType.CALL, value=function_name)

    def parse_hlt_statement(self) -> Node:
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'hlt'")
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after 'hlt'")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(NodeType.HLT)

    # Add support for ret instruction
    def parse_ret_statement(self) -> Node:
        self.consume(TokenType.LEFT_PAREN, "Expected '(' after 'ret'")
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after 'ret'")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(NodeType.RET)

    # Helper methods for instruction parsing
    def parse_binary_instruction(self, node_type: NodeType) -> Node:
        self.consume(TokenType.LEFT_PAREN, f"Expected '(' after instruction")
        
        if not self.match(TokenType.IDENTIFIER) and not self.match(TokenType.NUMBER):
            raise SyntaxError(f"Expected first argument at line {self.peek().line}")
        
        dest = self.previous().value
        
        self.consume(TokenType.COMMA, "Expected ',' between arguments")
        
        if not self.match(TokenType.IDENTIFIER) and not self.match(TokenType.NUMBER):
            raise SyntaxError(f"Expected second argument at line {self.peek().line}")
        
        src = self.previous().value
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(node_type, value={"dest": dest, "src": src})
    
    def parse_unary_instruction(self, node_type: NodeType) -> Node:
        self.consume(TokenType.LEFT_PAREN, f"Expected '(' after instruction")
        
        if not self.match(TokenType.IDENTIFIER) and not self.match(TokenType.NUMBER):
            raise SyntaxError(f"Expected argument at line {self.peek().line}")
        
        operand = self.previous().value
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after argument")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(node_type, value=operand)
    
    def parse_jump_instruction(self, node_type: NodeType) -> Node:
        self.consume(TokenType.LEFT_PAREN, f"Expected '(' after jump instruction")
        
        # Jump target should be a string (for labels) or identifier
        if not self.match(TokenType.STRING) and not self.match(TokenType.IDENTIFIER):
            raise SyntaxError(f"Expected label at line {self.peek().line}")
        
        target = self.previous().value
        if target.startswith('"') and target.endswith('"'):
            target = target[1:-1]  # Remove quotes if present
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after jump target")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(node_type, value=target)
    
    def parse_conditional_jump_instruction(self, node_type: NodeType) -> Node:
        self.consume(TokenType.LEFT_PAREN, f"Expected '(' after conditional jump")
        
        if not self.match(TokenType.STRING) and not self.match(TokenType.IDENTIFIER):
            raise SyntaxError(f"Expected true label at line {self.peek().line}")
        
        true_label = self.previous().value
        if true_label.startswith('"') and true_label.endswith('"'):
            true_label = true_label[1:-1]
            
        self.consume(TokenType.COMMA, "Expected ',' between jump targets")
        
        if not self.match(TokenType.STRING) and not self.match(TokenType.IDENTIFIER):
            raise SyntaxError(f"Expected false label at line {self.peek().line}")
        
        false_label = self.previous().value
        if false_label.startswith('"') and false_label.endswith('"'):
            false_label = false_label[1:-1]
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after jump targets")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(node_type, value={"true": true_label, "false": false_label})
    
    def parse_out_instruction(self, node_type: NodeType) -> Node:
        self.consume(TokenType.LEFT_PAREN, f"Expected '(' after output instruction")
        
        # Expect the first argument (port number or identifier) - should be NUMBER or IDENTIFIER
        if not self.match(TokenType.NUMBER) and not self.match(TokenType.IDENTIFIER):
            raise SyntaxError(f"Expected first argument (port number/identifier) at line {self.peek().line}")
        arg1 = self.previous().value
        
        self.consume(TokenType.COMMA, "Expected ',' between output arguments")
        
        # Expect the second argument (register/identifier/address) - should be an IDENTIFIER
        if not self.match(TokenType.IDENTIFIER):
            raise SyntaxError(f"Expected second argument (register/identifier/address) at line {self.peek().line}")
        arg2 = self.previous().value
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after output arguments")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        # Store arguments as arg1 and arg2
        return Node(node_type, value={"arg1": arg1, "arg2": arg2})