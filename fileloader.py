import os
from typing import List, Set
from lexer import Lexer, Token, TokenType

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