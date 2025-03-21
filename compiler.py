import re
import os
import sys
from enum import Enum, auto
from typing import List, Optional, Union, Dict, Any, Set

# Token types
class TokenType(Enum):
    INCLUDE = auto()
    FUNCTION = auto()
    IDENTIFIER = auto()
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    COMMA = auto()
    STRING = auto()
    NUMBER = auto()
    SEMICOLON = auto()  # Add token type for semicolons
    EOF = auto()

# Modify Token class to include source file information
class Token:
    def __init__(self, type: TokenType, value: str, line: int, source_file: str = ""):
        self.type = type
        self.value = value
        self.line = line
        self.source_file = source_file

class Lexer:
    def __init__(self, source: str, source_file: str = ""):
        self.source = source
        self.position = 0
        self.line = 1
        self.tokens = []
        self.source_file = source_file

    def tokenize(self) -> List[Token]:
        while self.position < len(self.source):
            char = self.source[self.position]
            
            # Skip whitespace
            if char.isspace():
                if char == '\n':
                    self.line += 1
                self.position += 1
                continue
            
            # Skip comments
            if char == '/' and self.position + 1 < len(self.source) and self.source[self.position + 1] == '/':
                self.position = self.source.find('\n', self.position)
                if self.position == -1:
                    self.position = len(self.source)
                continue
            
            # Include directives
            if char == '#':
                if self.source[self.position:].startswith('#M_include'):
                    self.tokens.append(Token(TokenType.INCLUDE, '#M_include', self.line, self.source_file))
                    self.position += 10  # Length of '#M_include'
                elif self.source[self.position:].startswith('#include'):
                    self.tokens.append(Token(TokenType.INCLUDE, '#include', self.line, self.source_file))
                    self.position += 8  # Length of '#include'
                else:
                    self.position += 1
                continue
            
            # Function declarations
            if self.source[self.position:].startswith('void'):
                self.tokens.append(Token(TokenType.FUNCTION, 'void', self.line, self.source_file))
                self.position += 4  # Length of 'void'
                continue
            
            # Identifiers
            if char.isalpha() or char == '_':
                start = self.position
                while self.position < len(self.source) and (self.source[self.position].isalnum() or self.source[self.position] == '_'):
                    self.position += 1
                identifier = self.source[start:self.position]
                self.tokens.append(Token(TokenType.IDENTIFIER, identifier, self.line, self.source_file))
                continue
            
            # Numbers
            if char.isdigit():
                start = self.position
                while self.position < len(self.source) and self.source[self.position].isdigit():
                    self.position += 1
                number = self.source[start:self.position]
                self.tokens.append(Token(TokenType.NUMBER, number, self.line, self.source_file))
                continue
            
            # Strings
            if char == '"':
                start = self.position
                self.position += 1  # Skip opening quote
                while self.position < len(self.source) and self.source[self.position] != '"':
                    if self.source[self.position] == '\\' and self.position + 1 < len(self.source):
                        self.position += 2  # Skip escape sequence
                    else:
                        self.position += 1
                
                if self.position >= len(self.source):
                    raise SyntaxError(f"Unterminated string at line {self.line}")
                
                self.position += 1  # Skip closing quote
                string_value = self.source[start:self.position]
                self.tokens.append(Token(TokenType.STRING, string_value, self.line, self.source_file))
                continue
            
            # Simple tokens
            if char == '(':
                self.tokens.append(Token(TokenType.LEFT_PAREN, '(', self.line, self.source_file))
                self.position += 1
                continue
            
            if char == ')':
                self.tokens.append(Token(TokenType.RIGHT_PAREN, ')', self.line, self.source_file))
                self.position += 1
                continue
            
            if char == '{':
                self.tokens.append(Token(TokenType.LEFT_BRACE, '{', self.line, self.source_file))
                self.position += 1
                continue
            
            if char == '}':
                self.tokens.append(Token(TokenType.RIGHT_BRACE, '}', self.line, self.source_file))
                self.position += 1
                continue
            
            if char == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, self.source_file))
                self.position += 1
                continue
            
            # Add semicolon handling
            if char == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', self.line, self.source_file))
                self.position += 1
                continue
            
            if char == '$':
                # Check if $ is followed by digits
                start = self.position
                self.position += 1  # Skip the $
                
                # Collect the number after $
                while self.position < len(self.source) and self.source[self.position].isdigit():
                    self.position += 1
                
                if self.position > start + 1:  # Ensure there are digits after $
                    address_value = self.source[start:self.position]  # Include the $ in the token
                    self.tokens.append(Token(TokenType.IDENTIFIER, address_value, self.line, self.source_file))
                else:
                    # Just a $ symbol by itself
                    self.tokens.append(Token(TokenType.IDENTIFIER, '$', self.line, self.source_file))
                continue
            
            # Unknown character
            raise SyntaxError(f"Unexpected character '{char}' at line {self.line} in {self.source_file}")
        
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.source_file))
        return self.tokens

# Add a FileLoader class to handle includes
class FileLoader:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.loaded_files: Set[str] = set()
        self.search_paths = []
        self.add_search_path(root_dir)
    
    def add_search_path(self, path: str):
        if path and os.path.isdir(path) and path not in self.search_paths:
            self.search_paths.append(path)
    
    def resolve_include_path(self, include_path: str, current_file: str) -> str:
        # Try relative to current file first
        if current_file:
            current_dir = os.path.dirname(os.path.abspath(current_file))
            full_path = os.path.normpath(os.path.join(current_dir, include_path))
            if os.path.isfile(full_path):
                return full_path
        
        # Try each search path
        for path in self.search_paths:
            full_path = os.path.normpath(os.path.join(path, include_path))
            if os.path.isfile(full_path):
                return full_path
        
        # Check if the file exists with .wake extension added
        if not include_path.lower().endswith('.wake'):
            with_extension = include_path + '.wake'
            result = self.resolve_include_path(with_extension, current_file)
            if result:
                return result
        
        raise FileNotFoundError(f"Could not find include file '{include_path}'")
    
    def load_file(self, file_path: str) -> str:
        with open(file_path, 'r') as file:
            return file.read()
    
    def process_includes(self, file_path: str) -> List[Token]:
        """Process includes recursively, but preserve main file's tokens"""
        main_file_path = os.path.abspath(file_path)  # Keep track of the initial file
        
        def process_file(file_path: str, is_main: bool = False) -> List[Token]:
            abs_path = os.path.abspath(file_path)
            
            # Skip if already processed (avoid circular includes)
            if abs_path in self.loaded_files and not is_main:
                return []
            
            self.loaded_files.add(abs_path)
            
            try:
                source = self.load_file(abs_path)
                lexer = Lexer(source, abs_path)
                tokens = lexer.tokenize()
                
                result_tokens = []
                i = 0
                
                while i < len(tokens):
                    token = tokens[i]
                    
                    if token.type == TokenType.INCLUDE:
                        # Must be followed by a string token
                        if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.STRING:
                            include_value = tokens[i + 1].value.strip('"')
                            try:
                                include_path = self.resolve_include_path(include_value, abs_path)
                                
                                # For regular #include, process and add included tokens
                                if token.value == '#include':
                                    included_tokens = process_file(include_path)
                                    result_tokens.extend(included_tokens)
                                # For #M_include, keep as is
                                else:
                                    result_tokens.append(token)
                                    result_tokens.append(tokens[i + 1])
                            except FileNotFoundError as e:
                                print(f"Warning: {e} included from {abs_path} line {token.line}")
                                result_tokens.append(token)
                                result_tokens.append(tokens[i + 1])
                            i += 2  # Skip the include directive and string
                        else:
                            raise SyntaxError(f"Expected string after include directive at {abs_path} line {token.line}")
                    else:
                        # Always include the token
                        result_tokens.append(token)
                        i += 1
                
                return result_tokens
                
            except Exception as e:
                print(f"Error processing file {file_path}: {str(e)}")
                raise
        
        # Start processing from the main file (marked as main)
        self.loaded_files = set()  # Reset loaded files tracking
        return process_file(main_file_path, is_main=True)

# AST node types
class NodeType(Enum):
    PROGRAM = auto()
    INCLUDE = auto()
    FUNCTION = auto()
    MOV = auto()
    DB = auto()
    CALL = auto()
    HLT = auto()
    RET = auto()
    # New instruction types
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
            if self.match(TokenType.INCLUDE):
                program.children.append(self.parse_include())
            elif self.match(TokenType.FUNCTION):
                program.children.append(self.parse_function())
            else:
                self.advance()  # Skip unrecognized tokens
        
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
        include_node = Node(NodeType.INCLUDE, value=self.previous().value)
        return include_node

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
        
        if not self.match(TokenType.NUMBER) and not self.match(TokenType.IDENTIFIER):
            raise SyntaxError(f"Expected port number at line {self.peek().line}")
        
        port = self.previous().value
        
        self.consume(TokenType.COMMA, "Expected ',' between output arguments")
        
        if not self.match(TokenType.IDENTIFIER) and not self.match(TokenType.NUMBER) and not self.match(TokenType.STRING):
            raise SyntaxError(f"Expected output value at line {self.peek().line}")
        
        value = self.previous().value
        if value.startswith('"') and value .endswith('"'):
            value = value[1:-1]
        
        self.consume(TokenType.RIGHT_PAREN, "Expected ')' after output arguments")
        
        # Skip optional semicolon after statement
        self.match(TokenType.SEMICOLON)
        
        return Node(node_type, value={"port": port, "value": value})

class CodeGenerator:
    def generate(self, ast: Node) -> str:
        output = []
        
        for node in ast.children:
            if node.type == NodeType.INCLUDE:
                output.append(node.value)
            elif node.type == NodeType.FUNCTION:
                output.extend(self.generate_function(node))
        
        return '\n'.join(output)

    def generate_function(self, function_node: Node) -> List[str]:
        output = []
        
        # Generate function header
        output.append(f"LBL {function_node.value}")
        
        # Generate function body
        for statement in function_node.children:
            if statement.type == NodeType.MOV:
                output.append(f"MOV {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.DB:
                output.append(f"DB ${statement.value['address']} {statement.value['string']}")
            elif statement.type == NodeType.CALL:
                output.append(f"CALL #{statement.value}")
            elif statement.type == NodeType.HLT:
                output.append("HLT")
            elif statement.type == NodeType.RET:
                output.append("RET")
            # Generate new instruction types
            elif statement.type == NodeType.ADD:
                output.append(f"ADD {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.SUB:
                output.append(f"SUB {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.MUL:
                output.append(f"MUL {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.DIV:
                output.append(f"DIV {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.INC:
                output.append(f"INC {statement.value}")
            elif statement.type == NodeType.JMP:
                output.append(f"JMP #{statement.value}")
            elif statement.type == NodeType.CMP:
                output.append(f"CMP {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.JE:
                output.append(f"JE #{statement.value['true']} #{statement.value['false']}")
            elif statement.type == NodeType.JNE:
                output.append(f"JNE #{statement.value['true']} #{statement.value['false']}")
            elif statement.type == NodeType.JL:
                output.append(f"JL #{statement.value['true']} #{statement.value['false']}")
            elif statement.type == NodeType.JG:
                output.append(f"JG #{statement.value['true']} #{statement.value['false']}")
            elif statement.type == NodeType.PUSH:
                output.append(f"PUSH {statement.value}")
            elif statement.type == NodeType.POP:
                output.append(f"POP {statement.value}")
            elif statement.type == NodeType.OUT:
                output.append(f"OUT {statement.value['port']} {statement.value['value']}")
            elif statement.type == NodeType.COUT:
                output.append(f"COUT {statement.value['port']} {statement.value['value']}")
            elif statement.type == NodeType.EXIT:
                output.append(f"EXIT {statement.value}")
            elif statement.type == NodeType.AND:
                output.append(f"AND {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.OR:
                output.append(f"OR {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.XOR:
                output.append(f"XOR {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.NOT:
                output.append(f"NOT {statement.value}")
            elif statement.type == NodeType.SHL:
                output.append(f"SHL {statement.value['dest']} {statement.value['src']}")
            elif statement.type == NodeType.SHR:
                output.append(f"SHR {statement.value['dest']} {statement.value['src']}")
                
        # Add a newline after each function
        output.append("")
        
        return output

# Update compile_wake_to_masm to use the AST-based approach with include handling
def compile_wake_to_masm(input_file, output_file):
    try:
        print(f"Compiling {input_file} to {output_file}")
        
        # Set up file loader with search paths
        base_dir = os.path.dirname(os.path.abspath(input_file))
        file_loader = FileLoader(base_dir)
        
        # Add standard search paths
        exec_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        file_loader.add_search_path(exec_dir)
        file_loader.add_search_path(os.path.join(exec_dir, 'include'))
        file_loader.add_search_path(os.getcwd())
        
        # Process all includes and collect tokens
        tokens = file_loader.process_includes(input_file)
        
        # Debug output to check tokens
        print(f"Total tokens processed: {len(tokens)}")
        function_tokens = [t for t in tokens if t.type == TokenType.FUNCTION]
        print(f"Function declarations found: {len(function_tokens)}")
        
        # Show all function tokens and their source files
        for ft in function_tokens:
            idx = tokens.index(ft)
            if idx + 1 < len(tokens) and tokens[idx+1].type == TokenType.IDENTIFIER:
                func_name = tokens[idx+1].value
                source_file = ft.source_file
                print(f"Found function: {func_name} from {source_file}")
        
        # Parse tokens into AST
        parser = Parser(tokens)
        ast = parser.parse()
        
        # Debug AST
        function_nodes = [node for node in ast.children if node.type == NodeType.FUNCTION]
        print(f"Function nodes in AST: {len(function_nodes)}")
        for fn in function_nodes:
            print(f"Function in AST: {fn.value}")
        
        # Generate MASM code
        generator = CodeGenerator()
        masm_code = generator.generate(ast)
        
        # Write output
        with open(output_file, 'w') as outfile:
            outfile.write(masm_code)
        
        print(f"Wake file '{input_file}' successfully compiled to Masm file '{output_file}'")
        return True
        
    except SyntaxError as e:
        print(f"Syntax error: {str(e)}")
        return False
    except FileNotFoundError as e:
        print(f"File error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error compiling Wake to Masm: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def print_usage():
    print("Usage: python compiler.py [input_file.wake] [-o output_file.masm]")
    print("  If input_file is not specified, defaults to main.wake")
    print("  If output_file is not specified, defaults to main.masm or input_file with .masm extension")

def main():
    # Default paths using os.path for proper path handling
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_input = os.path.join(base_dir, "main.wake")
    default_output = os.path.join(base_dir, "main.masm")
    
    input_file = default_input
    output_file = None
    
    # Parse command line arguments
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '-o' and i + 1 < len(sys.argv):
            output_file = os.path.normpath(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '-h' or sys.argv[i] == '--help':
            print_usage()
            return
        else:
            input_file = os.path.normpath(sys.argv[i])
            i += 1
    
    # Make sure input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return False
    
    # If output file not specified, default to input filename with .masm extension
    if output_file is None:
        if input_file.lower().endswith('.wake'):
            output_file = input_file[:-5] + '.masm'
        else:
            output_file = default_output
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error creating output directory: {str(e)}")
            return False
    
    # Compile the file
    return compile_wake_to_masm(input_file, output_file)

if __name__ == "__main__":
    main()
