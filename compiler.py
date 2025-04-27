#!/usr/bin/env python3

import re
import os
import sys
import argparse # Add argparse import
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
        """Process includes recursively, combining tokens correctly."""
        main_file_path = os.path.abspath(file_path)
        main_eof_token = None # To store the main file's EOF token info

        # Inner function to process a single file and its includes
        def process_file(current_file_path: str, is_main_file: bool = False) -> List[Token]:
            nonlocal main_eof_token
            abs_path = os.path.abspath(current_file_path)

            # Avoid circular includes, but always process the main file once
            if abs_path in self.loaded_files and not is_main_file:
                return []
            self.loaded_files.add(abs_path)

            try:
                source = self.load_file(abs_path)
                lexer = Lexer(source, abs_path)
                tokens = lexer.tokenize() # Tokenize the current file (includes its EOF)

                # If this is the main file being processed, capture its EOF token
                if is_main_file and tokens and tokens[-1].type == TokenType.EOF:
                    main_eof_token = tokens[-1]

                result_tokens = []
                i = 0
                # Iterate through tokens, excluding the last one (EOF)
                while i < len(tokens):
                    token = tokens[i]

                    # Stop if we hit the EOF token for this specific file
                    if token.type == TokenType.EOF:
                        break

                    if token.type == TokenType.INCLUDE:
                        # Expect a string token after include directive
                        if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.STRING:
                            include_value = tokens[i + 1].value.strip('"')
                            try:
                                include_path = self.resolve_include_path(include_value, abs_path)

                                # For regular #include, recursively process and extend tokens
                                if token.value == '#include':
                                    # Process the included file (not as the main file)
                                    included_tokens = process_file(include_path, False)
                                    result_tokens.extend(included_tokens)
                                # For #M_include, keep the directive and path as tokens
                                else:
                                    result_tokens.append(token)
                                    result_tokens.append(tokens[i + 1])

                            except FileNotFoundError as e:
                                print(f"Warning: {e} included from {abs_path} line {token.line}")
                                # Keep the include directive even if file not found, maybe handled later
                                result_tokens.append(token)
                                result_tokens.append(tokens[i + 1])

                            i += 2 # Move past the include directive and string path
                        else:
                            raise SyntaxError(f"Expected string after include directive at {abs_path} line {token.line}")
                    else:
                        # Add any other token to the result list
                        result_tokens.append(token)
                        i += 1

                return result_tokens # Return the list of tokens for this file (without its EOF)

            except Exception as e:
                print(f"Error processing file {current_file_path}: {str(e)}")
                raise

        # Start processing from the main file
        self.loaded_files = set() # Reset loaded files for this compilation run
        final_tokens = process_file(main_file_path, is_main_file=True)

        # Append the single, final EOF token from the main file
        if main_eof_token:
            final_tokens.append(main_eof_token)
        else:
            # Fallback: create a default EOF if the main file was empty or failed processing
            final_tokens.append(Token(TokenType.EOF, "", 1, main_file_path))

        return final_tokens

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

# Update compile_wake_to_masm to use the AST-based approach with include handling
def compile_wake_to_masm(input_file, output_file, verbose=False): # Add verbose parameter
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
        
        # Debug output to check tokens (conditional)
        if verbose:
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
        
        # Debug AST (conditional)
        if verbose:
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


def main():
    # Default paths using os.path for proper path handling
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Remove default_input as it's no longer used for defaulting
    # default_input = os.path.join(base_dir, "main.wake")
    default_output_base = "main" # Base name for default output if input has no extension

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Compile Wake language files to Masm.")
    # Make input_file a required positional argument
    parser.add_argument('input_file',
                        help="The input .wake file")
    parser.add_argument('-o', '--output', dest='output_file', default=None,
                        help="The output .masm file (defaults to input filename with .masm extension)")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose output for debugging")

    args = parser.parse_args()

    input_file = os.path.normpath(args.input_file)
    output_file = args.output_file
    verbose = args.verbose # Get verbose flag

    # Make sure input file exists (keep this check for a clear error)
    if not os.path.exists(input_file):
        # Use parser's error handling
        parser.error(f"Input file '{input_file}' not found")

    # If output file not specified, default based on input filename
    if output_file is None:
        input_basename = os.path.basename(input_file)
        # Determine output directory (same as input file)
        output_dir_default = os.path.dirname(input_file)
        if input_basename.lower().endswith('.wake'):
            output_basename = input_basename[:-5] + '.masm'
        else:
            # If input doesn't end with .wake, use its name + .masm
            output_basename = input_basename + '.masm'
        # Place output in the same directory as input by default
        output_file = os.path.join(output_dir_default, output_basename)
    else:
        output_file = os.path.normpath(output_file)

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            if verbose: # Conditional print
                print(f"Created output directory: {output_dir}")
        except OSError as e:
            parser.error(f"Error creating output directory '{output_dir}': {str(e)}")

    # Compile the file, passing the verbose flag
    success = compile_wake_to_masm(input_file, output_file, verbose)

    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
