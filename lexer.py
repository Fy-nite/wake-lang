import re
from enum import Enum, auto
from typing import List

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
    SEMICOLON = auto()
    EOF = auto()

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